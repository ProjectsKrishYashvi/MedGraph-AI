"""
MedGraph AI — Model Evaluation & Metrics Reporting
===================================================
Evaluates the trained XGBoost model against the held-out test set.
Computes and persists: ROC-AUC, PR-AUC, F1, Precision, Recall, Confusion Matrix.
"""

import json
import logging
import os
import sys

import numpy as np
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    confusion_matrix,
    classification_report,
)
from xgboost import XGBClassifier

sys.path.insert(0, os.path.dirname(__file__))
import config
import utils

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_model() -> XGBClassifier:
    """Load the serialized XGBoost model from disk."""
    if not os.path.exists(config.MODEL_PATH):
        raise FileNotFoundError(
            f"Trained model not found at {config.MODEL_PATH}. Run train.py first."
        )
    model = XGBClassifier()
    model.load_model(config.MODEL_PATH)
    logger.info("Model loaded from %s", config.MODEL_PATH)
    return model


def evaluate_model(
    model: XGBClassifier,
    X_test: "pd.DataFrame",
    y_test: "pd.Series",
) -> dict:
    """
    Evaluate the model on the holdout test set.

    Args:
        model: Trained XGBClassifier.
        X_test: Test feature matrix.
        y_test: Test target series.

    Returns:
        dict: All computed metrics.
    """
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)

    roc_auc = float(roc_auc_score(y_test, y_pred_proba))
    pr_auc = float(average_precision_score(y_test, y_pred_proba))
    f1 = float(f1_score(y_test, y_pred))
    precision = float(precision_score(y_test, y_pred))
    recall = float(recall_score(y_test, y_pred))
    cm = confusion_matrix(y_test, y_pred).tolist()
    report = classification_report(y_test, y_pred, target_names=["Low-Risk", "High-Risk"])

    metrics = {
        "test_set_size": len(y_test),
        "positive_class_count": int(y_test.sum()),
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "f1_score": f1,
        "precision": precision,
        "recall": recall,
        "confusion_matrix": cm,
    }

    print("\n" + "=" * 72)
    print("HOLDOUT TEST SET EVALUATION REPORT")
    print("=" * 72)
    print(f"  Test Set Size     : {metrics['test_set_size']} samples")
    print(f"  High-Risk Count   : {metrics['positive_class_count']}")
    print(f"  ROC-AUC           : {roc_auc:.4f}")
    print(f"  PR-AUC            : {pr_auc:.4f}")
    print(f"  F1 Score          : {f1:.4f}")
    print(f"  Precision         : {precision:.4f}")
    print(f"  Recall            : {recall:.4f}")
    print(f"\n  Confusion Matrix (rows=Actual, cols=Predicted):")
    print(f"    TN={cm[0][0]:4d}  FP={cm[0][1]:4d}")
    print(f"    FN={cm[1][0]:4d}  TP={cm[1][1]:4d}")
    print(f"\n  Classification Report:\n{report}")
    print("=" * 72)

    return metrics


def save_metrics(metrics: dict) -> None:
    """Persist evaluation metrics to JSON."""
    os.makedirs(config.MODEL_DIR, exist_ok=True)
    with open(config.METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Evaluation metrics saved to %s", config.METRICS_PATH)


def run_evaluation_pipeline() -> dict:
    """Full evaluation pipeline entry point."""
    logger.info("=== MedGraph AI — Model Evaluation Pipeline ===")

    _, X_test, _, y_test, _ = utils.prepare_ml_datasets()
    model = load_model()
    metrics = evaluate_model(model, X_test, y_test)
    save_metrics(metrics)

    return metrics


if __name__ == "__main__":
    run_evaluation_pipeline()
