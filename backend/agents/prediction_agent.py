"""
MedGraph AI — Prediction Agent
================================
LangGraph node that runs XGBoost risk inference + SHAP explanations
for a patient, using the patient_data populated by the graph_agent.

Builds the feature vector from patient_data fields so that predictions
can be made without re-querying the features.parquet file.
"""

import logging
import os
import sys
from typing import Dict, Any

_AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
_ML_DIR = os.path.abspath(os.path.join(_AGENTS_DIR, "..", "ml"))
for _p in [_AGENTS_DIR, _ML_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import predict as ml_predict
except ImportError:
    from backend.ml import predict as ml_predict

try:
    from state import MedGraphState
except ImportError:
    from backend.agents.state import MedGraphState

logger = logging.getLogger(__name__)

# Observation type → feature name mapping (mirrors features.py logic)
OBS_TYPE_MAP = {
    "Body Mass Index":                "latest_bmi",
    "Systolic Blood Pressure":        "latest_systolic_bp",
    "Diastolic Blood Pressure":       "latest_diastolic_bp",
    "Hemoglobin A1c/Hemoglobin.total in Blood": "latest_hba1c",
    "Glucose":                        "latest_glucose",
    "Estimated Glomerular Filtration Rate": "latest_egfr",
    "Total Cholesterol":              "latest_cholesterol",
    "High Density Lipoprotein Cholesterol":  "latest_hdl",
    "Low Density Lipoprotein Cholesterol":   "latest_ldl",
    "Triglycerides":                  "latest_triglycerides",
    "Heart rate":                     "latest_heart_rate",
}

# Condition name → binary feature flag mapping
CONDITION_FLAG_MAP = {
    "diabetes":         "has_diabetes",
    "hypertension":     "has_hypertension",
    "chronic kidney":   "has_ckd",
    "heart failure":    "has_heart_failure",
    "copd":             "has_copd",
    "chronic obstructive": "has_copd",
    "obesity":          "has_obesity",
}

ENCOUNTER_TYPE_MAP = {
    "ambulatory":   "ambulatory_encounters",
    "emergency":    "emergency_encounters",
    "inpatient":    "inpatient_encounters",
    "outpatient":   "outpatient",
    "urgentcare":   "urgentcare_encounters",
    "wellness":     "wellness_encounters",
}


def _build_feature_vector(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reconstruct the feature vector from Neo4j patient_data.
    Maps graph fields back to ML feature names used during training.
    """
    patient  = patient_data.get("patient", {})
    conditions  = patient_data.get("conditions", [])
    medications = patient_data.get("medications", [])
    encounters  = patient_data.get("encounters", [])
    observations = patient_data.get("observations", [])
    summary     = patient_data.get("summary", {})

    features = {}

    # Demographics
    features["age"]         = patient.get("age")
    features["race"]        = patient.get("race", "unknown")
    features["is_female"]   = 1 if str(patient.get("gender", "")).lower() == "f" else 0
    features["is_deceased"] = 1 if patient.get("death_date") else 0

    # Summary counts
    features["total_encounters"]  = summary.get("total_encounters", len(encounters))
    features["total_conditions"]  = summary.get("total_conditions", len(conditions))
    features["total_medications"] = summary.get("total_medications", len(medications))
    features["total_procedures"]  = summary.get("total_procedures", 0)

    # Active medications
    features["active_medications"] = len(medications)

    # Encounter type counts (from recent encounters — approximate)
    enc_type_counts = {v: 0 for v in ENCOUNTER_TYPE_MAP.values()}
    for enc in encounters:
        enc_type = str(enc.get("encounter_type", "")).lower()
        for keyword, feat_name in ENCOUNTER_TYPE_MAP.items():
            if keyword in enc_type:
                enc_type_counts[feat_name] = enc_type_counts.get(feat_name, 0) + 1
    features.update(enc_type_counts)

    # Chronic conditions count
    active_conditions = [c for c in conditions if not c.get("stop_date")]
    features["chronic_conditions"] = len(active_conditions)

    # Binary condition flags
    for flag in CONDITION_FLAG_MAP.values():
        features[flag] = 0
    for cond in conditions:
        cond_lower = str(cond.get("condition_name", "")).lower()
        for keyword, flag in CONDITION_FLAG_MAP.items():
            if keyword in cond_lower:
                features[flag] = 1

    # Lab observations
    for obs in observations:
        obs_type = obs.get("obs_type", "")
        feat_name = OBS_TYPE_MAP.get(obs_type)
        if feat_name:
            val = obs.get("value")
            features[feat_name] = float(val) if val is not None else None

    # Fill missing lab features with None (XGBoost handles natively)
    for feat_name in OBS_TYPE_MAP.values():
        if feat_name not in features:
            features[feat_name] = None

    return features


def prediction_node(state: MedGraphState) -> MedGraphState:
    """
    LangGraph node: run XGBoost risk prediction + SHAP explanation.

    Requires state["patient_data"] to be populated by graph_node first.
    Populates state["risk_result"] with risk probability, classification,
    and top SHAP contributors.
    """
    logger.info("[PredictionAgent] Running risk prediction for patient: %s", state["patient_id"])

    patient_data = state.get("patient_data")
    if not patient_data:
        error = "PredictionAgent: patient_data is missing — graph_node may have failed."
        logger.error(error)
        return {
            **state,
            "risk_result": None,
            "errors": state.get("errors", []) + [error],
        }

    try:
        feature_vector = _build_feature_vector(patient_data)
        result = ml_predict.predict_patient_risk(feature_vector, top_n=5)

        logger.info(
            "[PredictionAgent] Risk probability: %.4f | High-risk: %s",
            result["risk_probability"],
            result["is_high_risk"],
        )

        return {**state, "risk_result": result}

    except Exception as exc:
        error_msg = f"PredictionAgent error: {exc}"
        logger.error(error_msg)
        return {
            **state,
            "risk_result": None,
            "errors": state.get("errors", []) + [error_msg],
        }
