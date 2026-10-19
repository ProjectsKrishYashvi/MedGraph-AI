"""
MedGraph AI — Machine Learning Pipeline Configuration
=====================================================
Defines feature columns, target label, exclusion/leakage lists,
hyperparameters, file paths, and cross-validation settings.
"""

import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DATA_PATH = os.path.join(DATA_DIR, "processed", "features.parquet")
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "xgboost_high_risk.json")
EXPLAINER_PATH = os.path.join(MODEL_DIR, "shap_explainer.pkl")
METRICS_PATH = os.path.join(MODEL_DIR, "evaluation_metrics.json")

# Target & Exclusion Definitions
TARGET_COLUMN = "is_high_risk"

# Columns to strictly exclude from ML feature set X:
# - patient_id: Arbitrary primary key string (no predictive signal)
# - risk_criteria_met: Direct count of triggered rules (100% Target Leakage)
# - is_high_risk: The target variable itself
EXCLUDE_COLUMNS = [
    "patient_id",
    "risk_criteria_met",
    "is_high_risk"
]

# Categorical Features requiring One-Hot Encoding
CATEGORICAL_FEATURES = [
    "race"
]

# Numerical Features (Demographics, Encounters, Conditions, Meds, Procedures, Observations)
NUMERICAL_FEATURES = [
    "age",
    "is_female",
    "is_deceased",
    "total_encounters",
    "ambulatory_encounters",
    "emergency_encounters",
    "inpatient_encounters",
    "outpatient",
    "urgentcare_encounters",
    "wellness_encounters",
    "total_conditions",
    "chronic_conditions",
    "has_diabetes",
    "has_hypertension",
    "has_ckd",
    "has_heart_failure",
    "has_copd",
    "has_obesity",
    "total_medications",
    "active_medications",
    "total_procedures",
    "latest_bmi",
    "latest_cholesterol",
    "latest_diastolic_bp",
    "latest_egfr",
    "latest_glucose",
    "latest_hba1c",
    "latest_hdl",
    "latest_heart_rate",
    "latest_ldl",
    "latest_systolic_bp",
    "latest_triglycerides"
]

# Train / Test Split Settings
RANDOM_STATE = 42
TEST_SIZE = 0.20
N_FOLDS = 5

# Baseline XGBoost Hyperparameters
# scale_pos_weight: (835 negative / 328 positive) ≈ 2.545 for balanced gradient loss
XGB_PARAMS = {
    "n_estimators": 150,
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "scale_pos_weight": 2.545,
    "random_state": RANDOM_STATE,
    "eval_metric": "logloss",
}
