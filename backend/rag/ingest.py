"""
MedGraph AI — Clinical Guidelines Ingestion Pipeline
=====================================================
Reads curated guideline text files, chunks them with controlled overlap,
generates BAAI/bge-small-en-v1.5 embeddings via fastembed, and stores
vectors + metadata into a local persistent Qdrant collection.

Run once to build the index; idempotent — recreates collection if it exists.

Usage:
    python backend/rag/ingest.py
"""

import logging
import os
import sys
import uuid
from typing import List, Dict

from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)
from fastembed import TextEmbedding

_RAG_DIR = os.path.dirname(os.path.abspath(__file__))
if _RAG_DIR not in sys.path:
    sys.path.insert(0, _RAG_DIR)

try:
    import rag_config as config
except ImportError:
    try:
        from backend.rag import rag_config as config
    except ImportError:
        import importlib.util
        _cfg_path = os.path.join(_RAG_DIR, "rag_config.py")
        _spec = importlib.util.spec_from_file_location("rag_config", _cfg_path)
        config = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(config)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Text Loading
# ---------------------------------------------------------------------------

def load_guidelines() -> List[Dict]:
    """
    Load all guideline text files from GUIDELINES_DIR.

    Returns:
        List of dicts: [{"filename": str, "text": str, "source": str, "condition_tags": list}]
    """
    documents = []
    if not os.path.exists(config.GUIDELINES_DIR):
        raise FileNotFoundError(
            f"Guidelines directory not found: {config.GUIDELINES_DIR}\n"
            "Create data/guidelines/ and add the guideline .txt files."
        )

    for filename in sorted(os.listdir(config.GUIDELINES_DIR)):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(config.GUIDELINES_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read().strip()

        source = config.GUIDELINE_SOURCES.get(filename, filename)
        condition_tags = config.GUIDELINE_CONDITION_TAGS.get(filename, [])

        documents.append({
            "filename":       filename,
            "text":           text,
            "source":         source,
            "condition_tags": condition_tags,
        })
        logger.info("Loaded: %s (%d characters)", filename, len(text))

    if not documents:
        raise ValueError(f"No .txt guideline files found in {config.GUIDELINES_DIR}")

    return documents


# ---------------------------------------------------------------------------
# Text Chunking
# ---------------------------------------------------------------------------

def chunk_documents(documents: List[Dict]) -> List[Dict]:
    """
    Split guideline texts into overlapping chunks using
    RecursiveCharacterTextSplitter.

    Section headers (===) are used as natural split points before
    character-level splitting — this keeps clinically coherent sections intact
    where possible.

    Returns:
        List of chunk dicts with text + metadata.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=[
            "\n=====",   # Section delimiters in our guideline files
            "\n\n",      # Paragraph breaks
            "\n",        # Line breaks
            ". ",        # Sentence breaks
            " ",         # Word breaks
        ],
    )

    chunks = []
    for doc in documents:
        doc_chunks = splitter.split_text(doc["text"])
        for i, chunk_text in enumerate(doc_chunks):
            chunk_text = chunk_text.strip()
            if len(chunk_text) < 50:  # Skip trivially short chunks
                continue
            chunks.append({
                "chunk_id":      str(uuid.uuid4()),
                "text":          chunk_text,
                "source":        doc["source"],
                "filename":      doc["filename"],
                "chunk_index":   i,
                "condition_tags": doc["condition_tags"],
            })

    logger.info("Total chunks produced: %d", len(chunks))
    return chunks


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------

def embed_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    Generate BAAI/bge-small-en-v1.5 embeddings for all chunk texts.

    fastembed downloads the ONNX model on first call (~130 MB).
    Subsequent calls use the cached model.

    Returns:
        chunks with an added "embedding" key (List[float]).
    """
    logger.info("Loading fastembed model: %s", config.EMBEDDING_MODEL)
    model = TextEmbedding(model_name=config.EMBEDDING_MODEL)

    texts = [c["text"] for c in chunks]
    logger.info("Generating embeddings for %d chunks...", len(texts))

    embeddings = list(model.embed(texts))

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding.tolist()

    logger.info("Embeddings generated. Vector dimension: %d", len(embeddings[0]))
    return chunks


# ---------------------------------------------------------------------------
# Qdrant Ingestion
# ---------------------------------------------------------------------------

def ingest_to_qdrant(chunks: List[Dict]) -> QdrantClient:
    """
    Store embedded chunks in the local persistent Qdrant collection.

    Recreates the collection if it already exists (idempotent re-ingestion).

    Returns:
        QdrantClient instance for immediate use.
    """
    os.makedirs(config.QDRANT_PATH, exist_ok=True)
    client = QdrantClient(path=config.QDRANT_PATH)

    # Drop and recreate collection for clean re-ingestion
    existing = [c.name for c in client.get_collections().collections]
    if config.COLLECTION_NAME in existing:
        client.delete_collection(config.COLLECTION_NAME)
        logger.info("Existing collection '%s' deleted for re-ingestion.", config.COLLECTION_NAME)

    client.create_collection(
        collection_name=config.COLLECTION_NAME,
        vectors_config=VectorParams(
            size=config.EMBEDDING_DIM,
            distance=Distance.COSINE,
        ),
    )
    logger.info("Collection '%s' created (dim=%d, metric=cosine).",
                config.COLLECTION_NAME, config.EMBEDDING_DIM)

    # Upload in one batch (< 1,000 chunks — fits comfortably in memory)
    points = [
        PointStruct(
            id=i,
            vector=chunk["embedding"],
            payload={
                "text":           chunk["text"],
                "source":         chunk["source"],
                "filename":       chunk["filename"],
                "chunk_index":    chunk["chunk_index"],
                "condition_tags": chunk["condition_tags"],
            },
        )
        for i, chunk in enumerate(chunks)
    ]

    client.upsert(collection_name=config.COLLECTION_NAME, points=points)
    logger.info("Upserted %d points into Qdrant collection '%s'.",
                len(points), config.COLLECTION_NAME)

    return client


# ---------------------------------------------------------------------------
# Pipeline Entry Point
# ---------------------------------------------------------------------------

def run_ingestion_pipeline() -> None:
    """Full ingestion pipeline: load → chunk → embed → store."""
    logger.info("=== MedGraph AI — RAG Ingestion Pipeline ===")

    documents = load_guidelines()
    chunks    = chunk_documents(documents)
    chunks    = embed_chunks(chunks)
    client    = ingest_to_qdrant(chunks)

    # Verify ingestion
    info = client.get_collection(config.COLLECTION_NAME)
    total_vectors = info.points_count

    print("\n" + "=" * 60)
    print("RAG INGESTION COMPLETE")
    print("=" * 60)
    print(f"  Guidelines loaded  : {len(documents)}")
    print(f"  Total chunks       : {len(chunks)}")
    print(f"  Vectors in Qdrant  : {total_vectors}")
    print(f"  Collection         : {config.COLLECTION_NAME}")
    print(f"  Embedding model    : {config.EMBEDDING_MODEL}")
    print(f"  Vector dimension   : {config.EMBEDDING_DIM}")
    print(f"  Qdrant path        : {config.QDRANT_PATH}")
    print("=" * 60)

    logger.info("Ingestion pipeline complete.")


if __name__ == "__main__":
    run_ingestion_pipeline()
