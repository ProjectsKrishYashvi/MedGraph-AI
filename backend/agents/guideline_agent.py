"""
MedGraph AI — Guideline Agent
==============================
LangGraph node that retrieves relevant clinical guideline evidence
from the Qdrant RAG collection based on the patient's condition profile.

Uses patient_data (from graph_node) and risk_result (from prediction_node)
to construct a targeted retrieval query.
"""

import logging
import os
import sys
from typing import List, Dict, Any

_AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
_RAG_DIR = os.path.abspath(os.path.join(_AGENTS_DIR, "..", "rag"))
for _p in [_AGENTS_DIR, _RAG_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from retriever import get_retriever
except ImportError:
    from backend.rag.retriever import get_retriever

try:
    from state import MedGraphState
except ImportError:
    from backend.agents.state import MedGraphState

logger = logging.getLogger(__name__)


def _build_patient_profile_for_rag(
    patient_data: Dict[str, Any],
    risk_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Construct the patient profile dict expected by GuidelineRetriever.retrieve_for_patient().
    Maps graph patient_data back to feature flag format.
    """
    conditions = patient_data.get("conditions", [])
    patient    = patient_data.get("patient", {})
    obs        = patient_data.get("observations", [])

    # Build condition flags
    condition_flag_map = {
        "diabetes":          "has_diabetes",
        "hypertension":      "has_hypertension",
        "chronic kidney":    "has_ckd",
        "heart failure":     "has_heart_failure",
        "copd":              "has_copd",
        "chronic obstructive": "has_copd",
        "obesity":           "has_obesity",
    }

    profile = {flag: 0 for flag in condition_flag_map.values()}
    for cond in conditions:
        cond_lower = str(cond.get("condition_name", "")).lower()
        for keyword, flag in condition_flag_map.items():
            if keyword in cond_lower:
                profile[flag] = 1

    # Patient demographics
    profile["age"] = patient.get("age")

    # Latest lab values from observations
    obs_type_map = {
        "Hemoglobin A1c/Hemoglobin.total in Blood": "latest_hba1c",
        "Systolic Blood Pressure":                   "latest_systolic_bp",
        "Estimated Glomerular Filtration Rate":      "latest_egfr",
    }
    for observation in obs:
        feat_name = obs_type_map.get(observation.get("obs_type", ""))
        if feat_name:
            val = observation.get("value")
            if val is not None:
                profile[feat_name] = float(val)

    return profile


def guideline_node(state: MedGraphState) -> MedGraphState:
    """
    LangGraph node: retrieve relevant clinical guidelines from Qdrant.

    Requires state["patient_data"] from graph_node.
    Uses risk_result context if available to enrich retrieval.
    Populates state["guidelines"] with top-K relevant chunks.
    """
    logger.info("[GuidelineAgent] Retrieving guidelines for patient: %s", state["patient_id"])

    patient_data = state.get("patient_data")
    if not patient_data:
        error = "GuidelineAgent: patient_data is missing — skipping guideline retrieval."
        logger.warning(error)
        return {
            **state,
            "guidelines": [],
            "errors": state.get("errors", []) + [error],
        }

    try:
        risk_result  = state.get("risk_result") or {}
        rag_profile  = _build_patient_profile_for_rag(patient_data, risk_result)
        retriever    = get_retriever()
        guidelines   = retriever.retrieve_for_patient(rag_profile, top_k=5)

        logger.info(
            "[GuidelineAgent] Retrieved %d guideline chunks (top score: %.4f)",
            len(guidelines),
            guidelines[0]["score"] if guidelines else 0.0,
        )

        return {**state, "guidelines": guidelines}

    except Exception as exc:
        error_msg = f"GuidelineAgent error: {exc}"
        logger.error(error_msg)
        return {
            **state,
            "guidelines": [],
            "errors": state.get("errors", []) + [error_msg],
        }
