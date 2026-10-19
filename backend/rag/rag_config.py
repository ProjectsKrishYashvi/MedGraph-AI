"""
MedGraph AI — RAG Subsystem Configuration
==========================================
Single source of truth for all RAG pipeline settings.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Resolve relative to project root regardless of where script is called from
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

GUIDELINES_DIR = os.path.join(_PROJECT_ROOT, "data", "guidelines")
QDRANT_PATH    = os.path.join(_PROJECT_ROOT, "data", "qdrant")

# ---------------------------------------------------------------------------
# Qdrant collection
# ---------------------------------------------------------------------------
COLLECTION_NAME = "clinical_guidelines"

# ---------------------------------------------------------------------------
# Embedding model
# ---------------------------------------------------------------------------
# fastembed downloads ONNX model to ~/.cache/fastembed on first use (~130 MB)
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM   = 384

# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------
CHUNK_SIZE    = 500   # characters per chunk (not tokens)
CHUNK_OVERLAP = 60    # overlap between consecutive chunks

# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
TOP_K = 5   # number of guideline chunks to return per query

# ---------------------------------------------------------------------------
# Guideline metadata — maps filename → human-readable source label
# ---------------------------------------------------------------------------
GUIDELINE_SOURCES = {
    "who_pen.txt":      "WHO Package of Essential NCD Interventions (WHO PEN)",
    "kdigo_ckd.txt":    "KDIGO 2024 Clinical Practice Guidelines for CKD",
    "ada_diabetes.txt": "ADA Standards of Medical Care in Diabetes",
}

# Condition tags associated with each guideline — used for structured metadata
GUIDELINE_CONDITION_TAGS = {
    "who_pen.txt":      ["hypertension", "diabetes", "copd", "cardiovascular"],
    "kdigo_ckd.txt":    ["ckd", "hypertension", "diabetes", "cardiovascular"],
    "ada_diabetes.txt": ["diabetes", "hypertension", "ckd", "cardiovascular", "obesity"],
}
