"""
MedGraph AI — Clinical Guideline Retriever
==========================================
Semantic search interface over the Qdrant clinical guidelines collection.

Consumed by the LangGraph Guideline Agent (Phase 5) to retrieve
evidence-based recommendations relevant to a patient's condition profile.

Supports two query modes:
1. Free-text query string — direct semantic search
2. Patient profile dict — auto-constructs a structured query from conditions

Usage:
    from backend.rag.retriever import GuidelineRetriever
    retriever = GuidelineRetriever()
    results = retriever.retrieve("management of hypertension in CKD patients")
    results = retriever.retrieve_for_patient(patient_profile)
"""

import logging
import os
import sys
from typing import List, Dict, Optional, Union

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny

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

logger = logging.getLogger(__name__)


_shared_model: Optional[TextEmbedding] = None
_shared_client: Optional[QdrantClient] = None


class GuidelineRetriever:
    """
    Semantic retrieval interface for the clinical guidelines Qdrant collection.

    Lazy-loads the embedding model and Qdrant client on first call.
    Designed to be instantiated once and reused across the application lifetime
    (module-level singleton pattern matches predict.py design).
    """

    def __init__(self):
        pass

    def _get_model(self) -> TextEmbedding:
        global _shared_model
        if _shared_model is None:
            logger.info("Loading fastembed model: %s", config.EMBEDDING_MODEL)
            _shared_model = TextEmbedding(model_name=config.EMBEDDING_MODEL)
        return _shared_model

    def _get_client(self) -> QdrantClient:
        global _shared_client
        if _shared_client is None:
            if not os.path.exists(config.QDRANT_PATH):
                raise FileNotFoundError(
                    f"Qdrant database not found at {config.QDRANT_PATH}. "
                    "Run backend/rag/ingest.py first."
                )
            _shared_client = QdrantClient(path=config.QDRANT_PATH)
            logger.info("Qdrant client connected: %s", config.QDRANT_PATH)
        return _shared_client

    def _embed_query(self, query: str) -> List[float]:
        """Embed a single query string."""
        model = self._get_model()
        embeddings = list(model.embed([query]))
        return embeddings[0].tolist()

    def retrieve(
        self,
        query: str,
        top_k: int = config.TOP_K,
        condition_filter: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Retrieve the top-K most semantically relevant guideline chunks.

        Args:
            query: Natural language query (e.g., "blood pressure targets in CKD patients with diabetes")
            top_k: Number of results to return (default: config.TOP_K)
            condition_filter: Optional list of condition tags to filter by
                              (e.g., ["ckd", "diabetes"]). If None, searches all guidelines.

        Returns:
            List of dicts ordered by relevance score (descending):
            [
                {
                    "text": str,
                    "source": str,
                    "filename": str,
                    "chunk_index": int,
                    "condition_tags": List[str],
                    "score": float   # cosine similarity [0, 1]
                }, ...
            ]
        """
        client = self._get_client()
        query_vector = self._embed_query(query)

        # Build optional payload filter
        qdrant_filter = None
        if condition_filter:
            qdrant_filter = Filter(
                must=[
                    FieldCondition(
                        key="condition_tags",
                        match=MatchAny(any=condition_filter),
                    )
                ]
            )

        results = client.query_points(
            collection_name=config.COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )

        return [
            {
                "text":           hit.payload["text"],
                "source":         hit.payload["source"],
                "filename":       hit.payload["filename"],
                "chunk_index":    hit.payload["chunk_index"],
                "condition_tags": hit.payload["condition_tags"],
                "score":          round(hit.score, 4),
            }
            for hit in results.points
        ]

    def retrieve_for_patient(
        self,
        patient_profile: Dict,
        top_k: int = config.TOP_K,
    ) -> List[Dict]:
        """
        Auto-construct a retrieval query from a patient's condition profile.

        This is the primary entry point used by the LangGraph Guideline Agent.
        Maps patient feature flags → clinical condition text → semantic query.

        Args:
            patient_profile: Dict containing patient feature flags.
                Required keys (boolean 0/1): has_diabetes, has_hypertension,
                has_ckd, has_heart_failure, has_copd, has_obesity.
                Also uses: age, latest_hba1c, latest_systolic_bp, latest_egfr.
            top_k: Number of guideline chunks to retrieve.

        Returns:
            Same format as retrieve().
        """
        # Build condition list from binary flags
        condition_map = {
            "has_diabetes":      "type 2 diabetes mellitus glycemic management HbA1c",
            "has_hypertension":  "hypertension blood pressure management treatment targets",
            "has_ckd":           "chronic kidney disease CKD eGFR albuminuria management",
            "has_heart_failure": "heart failure cardiovascular management SGLT2 inhibitor",
            "has_copd":          "COPD chronic obstructive pulmonary disease bronchodilator",
            "has_obesity":       "obesity weight management BMI cardiovascular risk",
        }

        active_conditions = []
        condition_tags = []

        for flag, query_term in condition_map.items():
            if patient_profile.get(flag, 0) == 1:
                active_conditions.append(query_term)
                # Map flag to condition tag for Qdrant filtering
                tag = flag.replace("has_", "")
                if tag == "heart_failure":
                    tag = "cardiovascular"
                condition_tags.append(tag)

        # Enrich query with lab values if available
        enrichments = []
        hba1c = patient_profile.get("latest_hba1c")
        if hba1c and hba1c > 7.0:
            enrichments.append(f"HbA1c {hba1c}% above target")

        sbp = patient_profile.get("latest_systolic_bp")
        if sbp and sbp > 130:
            enrichments.append(f"systolic BP {sbp} mmHg elevated")

        egfr = patient_profile.get("latest_egfr")
        if egfr and egfr < 60:
            enrichments.append(f"eGFR {egfr} mL/min/1.73m2 reduced kidney function")

        age = patient_profile.get("age")
        if age and age >= 65:
            enrichments.append("older adult aged 65 or above")

        # Compose final query
        query_parts = active_conditions + enrichments
        if not query_parts:
            query = "chronic disease management high-risk patient"
        else:
            query = " | ".join(query_parts)

        logger.info("Patient guideline query: %s", query[:120])
        return self.retrieve(
            query=query,
            top_k=top_k,
            condition_filter=condition_tags if condition_tags else None,
        )

    def format_for_llm(self, results: List[Dict]) -> str:
        """
        Format retrieved chunks into a clean string suitable for LLM context injection.

        Returns a structured block with source attribution for each chunk.
        """
        if not results:
            return "No relevant clinical guidelines found."

        lines = ["RELEVANT CLINICAL GUIDELINE EVIDENCE:", ""]
        for i, r in enumerate(results, start=1):
            lines.append(f"[{i}] Source: {r['source']} (relevance: {r['score']})")
            lines.append(r["text"])
            lines.append("")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-level singleton (for use in LangGraph agents)
# ---------------------------------------------------------------------------
_retriever: Optional[GuidelineRetriever] = None


def get_retriever() -> GuidelineRetriever:
    """Return the shared GuidelineRetriever singleton."""
    global _retriever
    if _retriever is None:
        _retriever = GuidelineRetriever()
    return _retriever


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    retriever = GuidelineRetriever()

    test_queries = [
        "blood pressure targets for patients with diabetes and CKD",
        "HbA1c targets and metformin dose adjustment in chronic kidney disease",
        "COPD bronchodilator treatment GOLD staging",
    ]

    print("\n" + "=" * 70)
    print("RAG RETRIEVER SMOKE TEST")
    print("=" * 70)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 70)
        results = retriever.retrieve(query, top_k=2)
        for i, r in enumerate(results, 1):
            print(f"  [{i}] Score: {r['score']} | Source: {r['source']}")
            print(f"       {r['text'][:200]}...")
        print()

    # Test patient profile query
    print("\n--- Patient Profile Query Test ---")
    test_patient = {
        "has_diabetes":     1,
        "has_hypertension": 1,
        "has_ckd":          1,
        "has_heart_failure": 0,
        "has_copd":         0,
        "has_obesity":      1,
        "latest_hba1c":     7.8,
        "latest_systolic_bp": 145.0,
        "latest_egfr":      42.0,
        "age":              68.5,
    }
    results = retriever.retrieve_for_patient(test_patient, top_k=3)
    print(f"Retrieved {len(results)} chunks for patient profile:")
    for i, r in enumerate(results, 1):
        print(f"  [{i}] Score: {r['score']} | {r['source']}")
        print(f"       Tags: {r['condition_tags']}")
        print(f"       {r['text'][:180]}...")

    print("\n" + "=" * 70)
    print("Smoke test complete.")
    print("=" * 70)
