"""
MedGraph AI — XGBoost Model Training & Cross-Validation
========================================================
Trains a binary XGBoost classifier to predict high-risk patients.

Pipeline:
1. Load & preprocess data via utils.prepare_ml_datasets()
2. 5-Fold Stratified Cross-Validation on the training set
3. Train final model on the complete training set
4. Serialize model artifact and feature names for downstream modules
"""

from backend.ml import predict
import json
import logging
import os
import sys

import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_validate
from xgboost import XGBClassifier

sys.path.insert(0, os.path.dirname(__file__))
import config
import utils

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def cross_validate_model(
    X_train: "pd.DataFrame",
    y_train: "pd.Series",
) -> dict:
    """
    Run 5-Fold Stratified Cross-Validation on the training set.

    Returns:
        dict: Mean and std of ROC-AUC and F1 across all folds.
    """
    logger.info("Starting %d-Fold Stratified Cross-Validation...", config.N_FOLDS)

    cv = StratifiedKFold(
        n_splits=config.N_FOLDS,
        shuffle=True,
        random_state=config.RANDOM_STATE,
    )

    # Use a fresh estimator for CV — do not reuse the final model object
    cv_model = XGBClassifier(**config.XGB_PARAMS)

    cv_results = cross_validate(
        cv_model,
        X_train,
        y_train,
        cv=cv,
        scoring=["roc_auc", "f1"],
        return_train_score=False,
        n_jobs=-1,
    )

    mean_auc = float(np.mean(cv_results["test_roc_auc"]))
    std_auc = float(np.std(cv_results["test_roc_auc"]))
    mean_f1 = float(np.mean(cv_results["test_f1"]))
    std_f1 = float(np.std(cv_results["test_f1"]))

    for fold_i, (auc, f1) in enumerate(
        zip(cv_results["test_roc_auc"], cv_results["test_f1"]), start=1
    ):
        logger.info("  Fold %d: ROC-AUC = %.4f | F1 = %.4f", fold_i, auc, f1)

    logger.info("Cross-Validation Summary: ROC-AUC = %.4f +/- %.4f | F1 = %.4f +/- %.4f",
                mean_auc, std_auc, mean_f1, std_f1)

    return {
        "cv_roc_auc_mean": mean_auc,
        "cv_roc_auc_std": std_auc,
        "cv_f1_mean": mean_f1,
        "cv_f1_std": std_f1,
        "fold_roc_auc": list(cv_results["test_roc_auc"]),
        "fold_f1": list(cv_results["test_f1"]),
    }


def train_final_model(
    X_train: "pd.DataFrame",
    y_train: "pd.Series",
) -> XGBClassifier:
    """
    Train the final XGBoost model on the complete training set.

    Returns:
        XGBClassifier: Trained model.
    """
    logger.info("Training final XGBoost model on full training set (%d samples)...", len(y_train))
    model = XGBClassifier(**config.XGB_PARAMS)
    model.fit(X_train, y_train)
    logger.info("Final model trained successfully.")
    return model


def save_artifacts(
    model: XGBClassifier,
    feature_names: list,
    cv_results: dict,
) -> None:
    """
    Persist model, feature names, and CV results to disk.
    """
    os.makedirs(config.MODEL_DIR, exist_ok=True)

    # Save XGBoost model (JSON format — portable, human-readable)
    model.save_model(config.MODEL_PATH)
    logger.info("Model saved to %s", config.MODEL_PATH)

    # Save feature names — required for column alignment in predict.py
    feature_names_path = os.path.join(config.MODEL_DIR, "feature_names.json")
    with open(feature_names_path, "w") as f:
        json.dump(feature_names, f, indent=2)
    logger.info("Feature names saved to %s", feature_names_path)

    # Save CV results
    cv_path = os.path.join(config.MODEL_DIR, "cv_results.json")
    with open(cv_path, "w") as f:
        json.dump(cv_results, f, indent=2)
    logger.info("CV results saved to %s", cv_path)


def run_training_pipeline() -> XGBClassifier:
    """
    Full training pipeline entry point.

    Returns:
        XGBClassifier: Trained final model.
    """
    logger.info("=== MedGraph AI — XGBoost Training Pipeline ===")

    X_train, X_test, y_train, y_test, feature_names = utils.prepare_ml_datasets()

    cv_results = cross_validate_model(X_train, y_train)
    model = train_final_model(X_train, y_train)
    save_artifacts(model, feature_names, cv_results)

    logger.info("Training pipeline complete.")
    return model


if __name__ == "__main__":
    run_training_pipeline()
