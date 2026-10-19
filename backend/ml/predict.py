"""
MedGraph AI — Patient Risk Prediction Service
==============================================
Reusable inference interface consumed by the FastAPI backend.

Given a dict of patient features, returns:
- risk_probability: float [0, 1]
- is_high_risk: bool
- top_shap_contributions: list of top contributing features with direction
"""

import json
import logging
import os
import pickle
import sys
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
import shap
from xgboost import XGBClassifier

sys.path.insert(0, os.path.dirname(__file__))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-loaded module-level singletons
# Loaded once on first call, reused across all subsequent requests
# ---------------------------------------------------------------------------
_model: Optional[XGBClassifier] = None
_explainer: Optional[shap.TreeExplainer] = None
_feature_names: Optional[List[str]] = None


def _load_model() -> XGBClassifier:
    global _model
    if _model is None:
        if not os.path.exists(config.MODEL_PATH):
            raise FileNotFoundError(
                f"Model artifact not found at {config.MODEL_PATH}. Run train.py first."
            )
        model = XGBClassifier()
        model.load_model(config.MODEL_PATH)
        _model = model
        logger.info("Model loaded from %s", config.MODEL_PATH)
    return _model


def _load_explainer() -> shap.TreeExplainer:
    global _explainer
    if _explainer is None:
        if not os.path.exists(config.EXPLAINER_PATH):
            raise FileNotFoundError(
                f"SHAP explainer not found at {config.EXPLAINER_PATH}. Run explainability.py first."
            )
        with open(config.EXPLAINER_PATH, "rb") as f:
            _explainer = pickle.load(f)
        logger.info("SHAP explainer loaded from %s", config.EXPLAINER_PATH)
    return _explainer


def _load_feature_names() -> List[str]:
    """
    Load the canonical ordered feature names used during training.

    This list is the single source of truth for column alignment.
    Using it in reindex() ensures new patients with unseen race categories
    or missing columns are safely zero-filled — never silently misaligned.
    """
    global _feature_names
    if _feature_names is None:
        feature_names_path = os.path.join(config.MODEL_DIR, "feature_names.json")
        if not os.path.exists(feature_names_path):
            raise FileNotFoundError(
                f"Feature names not found at {feature_names_path}. Run train.py first."
            )
        with open(feature_names_path) as f:
            _feature_names = json.load(f)
        logger.info("Feature names loaded: %d features", len(_feature_names))
    return _feature_names


def load_pipeline():
    """Pre-warm model, explainer, and feature names."""
    _load_model()
    _load_explainer()
    _load_feature_names()
    return True


def _preprocess_patient(patient_features: Dict[str, Any]) -> pd.DataFrame:
    """
    Preprocess a single patient feature dict into a model-ready DataFrame.

    Steps:
    1. Convert to single-row DataFrame.
    2. One-Hot Encode 'race' (same logic as training via pd.get_dummies).
    3. Remove any leakage/identifier columns if present.
    4. Reindex to training feature columns — fills unseen OHE categories with 0.
    5. Cast ALL columns to numeric (float64), converting Python None → np.nan.
       This mirrors utils.py behaviour and is required because dict-sourced
       DataFrames with None values infer dtype=object, which XGBoost rejects.
    """
    feature_names = _load_feature_names()

    df = pd.DataFrame([patient_features])

    # One-Hot Encode categorical features
    df = pd.get_dummies(df, columns=config.CATEGORICAL_FEATURES, dtype=int)

    # Drop leakage / identifier columns if accidentally present in input
    for col in config.EXCLUDE_COLUMNS:
        if col in df.columns:
            df = df.drop(columns=[col])

    # Align to training feature columns; fill missing OHE columns with 0
    df = df.reindex(columns=feature_names, fill_value=0)

    # Cast ALL columns to numeric — converts Python None → np.nan (float64).
    # This is the critical step that mirrors utils.preprocess_features() and
    # prevents XGBoost from receiving object-dtype columns at inference time.
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Validate dtypes before passing to model — fail fast with a clear message
    bad_cols = [
        col for col in df.columns
        if df[col].dtype not in (float, int, bool, "float64", "int64", "bool", "int32", "float32")
        and str(df[col].dtype) not in ("float64", "int64", "bool", "int32", "float32", "category")
    ]
    if bad_cols:
        raise ValueError(
            f"Inference dtype validation failed. Columns still have non-numeric dtype: {bad_cols}. "
            "Ensure all feature values are numeric, None (for missing), or a supported dtype."
        )

    return df


def predict_patient_risk(
    patient_features: Dict[str, Any],
    top_n: int = 5,
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Predict high-risk classification and generate a SHAP explanation for a single patient.

    Args:
        patient_features: Dict of raw patient feature values. Must include 'race'
                          and all expected numerical features. Missing numerical
                          values should be passed as None or np.nan (handled natively).
        top_n: Number of top SHAP contributing features to return (default: 5).
        threshold: Decision threshold for binary classification (default: 0.5).

    Returns:
        dict: {
            "risk_probability": float,
            "is_high_risk": bool,
            "top_shap_contributions": [
                {
                  "feature": str,
                  "shap_value": float,
                  "direction": "increases_risk" | "decreases_risk",
                  "feature_value": float | None
                }, ...
            ]
        }

    Raises:
        FileNotFoundError: If model/explainer artifacts are missing.
    """
    model = _load_model()
    explainer = _load_explainer()

    X_patient = _preprocess_patient(patient_features)

    # Risk probability (positive class)
    risk_probability = float(model.predict_proba(X_patient)[0, 1])
    is_high_risk = risk_probability >= threshold

    # SHAP local explanation
    shap_values = explainer.shap_values(X_patient)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    patient_shap = shap_values[0]
    feature_names = list(X_patient.columns)

    all_contributions = sorted(
        [
            {
                "feature": name,
                "shap_value": float(val),
                "direction": "increases_risk" if val > 0 else "decreases_risk",
                "feature_value": (
                    None
                    if pd.isna(X_patient.iloc[0][name])
                    else float(X_patient.iloc[0][name])
                ),
            }
            for name, val in zip(feature_names, patient_shap)
        ],
        key=lambda x: abs(x["shap_value"]),
        reverse=True,
    )

    return {
        "risk_probability": risk_probability,
        "is_high_risk": bool(is_high_risk),
        "top_shap_contributions": all_contributions[:top_n],
    }


if __name__ == "__main__":
    # Smoke-test with a synthetic high-risk patient profile
    test_patient = {
        "age": 68.5,
        "race": "white",
        "is_female": 0,
        "is_deceased": 0,
        "total_encounters": 42,
        "ambulatory_encounters": 15,
        "emergency_encounters": 4,
        "inpatient_encounters": 2,
        "outpatient": 3,
        "urgentcare_encounters": 1,
        "wellness_encounters": 5,
        "total_conditions": 6,
        "chronic_conditions": 4,
        "has_diabetes": 1,
        "has_hypertension": 1,
        "has_ckd": 1,
        "has_heart_failure": 0,
        "has_copd": 0,
        "has_obesity": 1,
        "total_medications": 8,
        "active_medications": 5,
        "total_procedures": 12,
        "latest_bmi": 33.2,
        "latest_cholesterol": 215.0,
        "latest_diastolic_bp": 85.0,
        "latest_egfr": None,     # Missing — handled natively by XGBoost
        "latest_glucose": 134.0,
        "latest_hba1c": 7.8,
        "latest_hdl": None,
        "latest_heart_rate": 78.0,
        "latest_ldl": None,
        "latest_systolic_bp": 138.0,
        "latest_triglycerides": None,
    }

    result = predict_patient_risk(test_patient, top_n=5)

    print("\n" + "=" * 60)
    print("SMOKE TEST — Single Patient Prediction")
    print("=" * 60)
    print(f"  Risk Probability : {result['risk_probability']:.4f}")
    print(f"  Is High Risk     : {result['is_high_risk']}")
    print("\n  Top SHAP Contributors:")
    for contrib in result["top_shap_contributions"]:
        sign = "+" if contrib["shap_value"] > 0 else ""
        print(f"    {contrib['feature']:<35} {sign}{contrib['shap_value']:.4f}  "
              f"[{contrib['direction']}]  (value: {contrib['feature_value']})")
    print("=" * 60)
