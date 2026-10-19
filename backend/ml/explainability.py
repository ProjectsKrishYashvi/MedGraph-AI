"""
MedGraph AI — SHAP Explainability Engine
=========================================
Generates global and local SHAP explanations for the XGBoost risk model.

- Global: Mean |SHAP value| per feature (feature importance ranking).
- Local: Per-patient SHAP values for the prediction API.
- Saves: SHAP TreeExplainer, global summary plot, summary JSON.
"""

import json
import logging
import os
import pickle
import sys
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — safe for server environments
import matplotlib.pyplot as plt
import shap
from xgboost import XGBClassifier

sys.path.insert(0, os.path.dirname(__file__))
import config
import utils

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SHAP_SUMMARY_PATH = os.path.join(config.MODEL_DIR, "shap_global_summary.json")
SHAP_PLOT_PATH = os.path.join(config.MODEL_DIR, "shap_feature_importance.png")


def load_model() -> XGBClassifier:
    """Load trained model from disk."""
    if not os.path.exists(config.MODEL_PATH):
        raise FileNotFoundError(
            f"Trained model not found at {config.MODEL_PATH}. Run train.py first."
        )
    model = XGBClassifier()
    model.load_model(config.MODEL_PATH)
    logger.info("Model loaded for SHAP explainability.")
    return model


def build_explainer(model: XGBClassifier) -> shap.TreeExplainer:
    """
    Initialize SHAP TreeExplainer for the XGBoost model.

    TreeExplainer is exact (not sampling-based) for tree models,
    guaranteeing consistency between global and local SHAP values.
    """
    explainer = shap.TreeExplainer(model)
    logger.info("SHAP TreeExplainer initialized.")
    return explainer


def compute_shap_values(
    explainer: shap.TreeExplainer,
    X: pd.DataFrame,
) -> np.ndarray:
    """
    Compute SHAP values for a feature matrix X.

    Returns the positive-class SHAP values (shape: n_samples x n_features).
    """
    shap_values = explainer.shap_values(X)
    # For binary XGBoost, shap_values is a single 2D array (not a list)
    if isinstance(shap_values, list):
        return shap_values[1]  # Positive class
    return shap_values


def compute_global_importance(
    shap_values: np.ndarray,
    feature_names: List[str],
) -> List[Dict]:
    """
    Compute global feature importance as mean(|SHAP value|) per feature.

    Returns:
        List of dicts sorted by importance descending.
    """
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    importance = sorted(
        [
            {"feature": name, "importance": float(val)}
            for name, val in zip(feature_names, mean_abs_shap)
        ],
        key=lambda x: x["importance"],
        reverse=True,
    )
    return importance


def save_explainer(explainer: shap.TreeExplainer) -> None:
    """Persist the TreeExplainer object to disk (pickle)."""
    os.makedirs(config.MODEL_DIR, exist_ok=True)
    with open(config.EXPLAINER_PATH, "wb") as f:
        pickle.dump(explainer, f)
    logger.info("SHAP explainer saved to %s", config.EXPLAINER_PATH)


def save_global_summary(importance: List[Dict]) -> None:
    """Save global SHAP feature importances as JSON."""
    with open(SHAP_SUMMARY_PATH, "w") as f:
        json.dump({"global_feature_importance": importance}, f, indent=2)
    logger.info("SHAP global summary saved to %s", SHAP_SUMMARY_PATH)


def save_summary_plot(
    shap_values: np.ndarray,
    X: pd.DataFrame,
) -> None:
    """Generate and save the SHAP beeswarm summary plot (top 20 features)."""
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X, max_display=20, show=False)
    plt.tight_layout()
    plt.savefig(SHAP_PLOT_PATH, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("SHAP summary plot saved to %s", SHAP_PLOT_PATH)


def explain_patient(
    explainer: shap.TreeExplainer,
    X_patient: pd.DataFrame,
    top_n: int = 5,
) -> List[Dict]:
    """
    Compute local SHAP explanation for a single patient.

    Args:
        explainer: Pre-built SHAP TreeExplainer.
        X_patient: Single-row DataFrame with aligned feature columns.
        top_n: Number of top contributing features to return.

    Returns:
        List of dicts: [{"feature": str, "shap_value": float, "direction": str}, ...]
    """
    shap_vals = explainer.shap_values(X_patient)
    if isinstance(shap_vals, list):
        shap_vals = shap_vals[1]

    patient_shap = shap_vals[0]
    feature_names = list(X_patient.columns)

    contributions = sorted(
        [
            {
                "feature": name,
                "shap_value": float(val),
                "direction": "increases_risk" if val > 0 else "decreases_risk",
                "feature_value": float(X_patient.iloc[0][name])
                    if not pd.isna(X_patient.iloc[0][name]) else None,
            }
            for name, val in zip(feature_names, patient_shap)
        ],
        key=lambda x: abs(x["shap_value"]),
        reverse=True,
    )
    return contributions[:top_n]


def run_explainability_pipeline() -> shap.TreeExplainer:
    """Full explainability pipeline entry point."""
    logger.info("=== MedGraph AI — SHAP Explainability Pipeline ===")

    X_train, X_test, y_train, y_test, feature_names = utils.prepare_ml_datasets()
    model = load_model()
    explainer = build_explainer(model)

    # Compute SHAP values on the test set for global summary
    logger.info("Computing SHAP values on test set (%d samples)...", len(X_test))
    shap_values = compute_shap_values(explainer, X_test)

    importance = compute_global_importance(shap_values, feature_names)

    print("\nTop 10 Features by Global SHAP Importance:")
    for rank, item in enumerate(importance[:10], start=1):
        print(f"  {rank:>2}. {item['feature']:<35} {item['importance']:.4f}")

    save_explainer(explainer)
    save_global_summary(importance)
    save_summary_plot(shap_values, X_test)

    logger.info("Explainability pipeline complete.")
    return explainer


if __name__ == "__main__":
    run_explainability_pipeline()
