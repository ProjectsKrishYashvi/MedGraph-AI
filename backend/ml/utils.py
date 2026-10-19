"""
MedGraph AI — Data Preprocessing & Pipeline Utilities
=====================================================
Provides reusable functions for loading, validating, encoding,
and splitting the canonical ML feature dataset (features.parquet).

Ensures deterministic preprocessing, leakage prevention, and
preserves native missing values (NaN) for XGBoost tree splitting.
"""

import os
import logging
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any
from sklearn.model_selection import train_test_split

import config

logger = logging.getLogger(__name__)

def load_raw_feature_table(data_path: str = config.PROCESSED_DATA_PATH) -> pd.DataFrame:
    """
    Load the canonical features Parquet dataset.

    Args:
        data_path: Path to features.parquet file.

    Returns:
        pd.DataFrame: Raw feature DataFrame.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the dataset is empty.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Feature dataset not found at: {data_path}")
        
    df = pd.read_parquet(data_path)
    if df.empty:
        raise ValueError(f"Feature dataset at {data_path} is empty.")
        
    logger.info("Loaded feature dataset: %d rows x %d columns", df.shape[0], df.shape[1])
    return df

def validate_feature_schema(df: pd.DataFrame) -> None:
    """
    Validate that the DataFrame contains required columns and target variable.

    Args:
        df: Input feature DataFrame.

    Raises:
        ValueError: If target or required feature columns are missing.
    """
    if config.TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{config.TARGET_COLUMN}' missing from feature dataset.")
        
    missing_num = set(config.NUMERICAL_FEATURES) - set(df.columns)
    if missing_num:
        raise ValueError(f"Missing numerical feature columns: {missing_num}")
        
    missing_cat = set(config.CATEGORICAL_FEATURES) - set(df.columns)
    if missing_cat:
        raise ValueError(f"Missing categorical feature columns: {missing_cat}")
        
    logger.info("Feature schema validation passed cleanly.")

def preprocess_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Preprocess feature DataFrame into feature matrix X and target vector y.

    Steps:
    1. Separate target y (is_high_risk).
    2. Drop leakage columns (risk_criteria_met) and identifier (patient_id).
    3. One-Hot Encode categorical columns ('race').
    4. Preserve missing numerical values (NaN) intact for XGBoost.

    Args:
        df: Validated raw feature DataFrame.

    Returns:
        Tuple[pd.DataFrame, pd.Series]: (X, y)
    """
    validate_feature_schema(df)
    
    # 1. Target vector y
    y = df[config.TARGET_COLUMN].astype(int)
    
    # 2. Drop excluded columns (Target + Leakage + Primary Key)
    cols_to_drop = [c for c in config.EXCLUDE_COLUMNS if c in df.columns]
    X_raw = df.drop(columns=cols_to_drop)
    
    # 3. Categorical One-Hot Encoding
    X_encoded = pd.get_dummies(X_raw, columns=config.CATEGORICAL_FEATURES, dtype=int)
    
    # Ensure all numerical columns are float64/int64 and NaNs are preserved
    for col in config.NUMERICAL_FEATURES:
        if col in X_encoded.columns:
            X_encoded[col] = pd.to_numeric(X_encoded[col], errors='coerce')
            
    logger.info("Preprocessed feature matrix X: %d rows x %d features", X_encoded.shape[0], X_encoded.shape[1])
    return X_encoded, y

def get_stratified_split(
    X: pd.DataFrame, 
    y: pd.Series, 
    test_size: float = config.TEST_SIZE, 
    random_state: int = config.RANDOM_STATE
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Perform a stratified train/test split maintaining target class balance.

    Args:
        X: Feature matrix.
        y: Target series.
        test_size: Holdout fraction (default 0.20).
        random_state: Random seed for reproducibility (default 42).

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]: 
            (X_train, X_test, y_train, y_test)
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=test_size, 
        stratify=y, 
        random_state=random_state
    )
    
    train_pos_pct = (y_train.sum() / len(y_train)) * 100
    test_pos_pct = (y_test.sum() / len(y_test)) * 100
    
    logger.info("Stratified Split Complete:")
    logger.info("  - Train Set: %d samples (High-Risk: %d | %.1f%%)", len(y_train), y_train.sum(), train_pos_pct)
    logger.info("  - Test Set : %d samples (High-Risk: %d | %.1f%%)", len(y_test), y_test.sum(), test_pos_pct)
    
    return X_train, X_test, y_train, y_test

def prepare_ml_datasets(
    data_path: str = config.PROCESSED_DATA_PATH
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, List[str]]:
    """
    High-level entry point for ML data preparation pipeline.

    Reads features.parquet, runs validation, leakage prevention,
    OHE encoding, and returns stratified train/test splits + feature names.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, List[str]]:
            (X_train, X_test, y_train, y_test, feature_names)
    """
    df = load_raw_feature_table(data_path)
    X, y = preprocess_features(df)
    X_train, X_test, y_train, y_test = get_stratified_split(X, y)
    feature_names = list(X.columns)
    
    return X_train, X_test, y_train, y_test, feature_names

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    X_tr, X_te, y_tr, y_te, feats = prepare_ml_datasets()
    print("\n--- Pipeline Utilities Execution Summary ---")
    print(f"Features Count : {len(feats)}")
    print(f"X_train Shape  : {X_tr.shape}")
    print(f"X_test Shape   : {X_te.shape}")
    print(f"y_train Counts : 0 -> {(y_tr==0).sum()} | 1 -> {(y_tr==1).sum()}")
    print(f"y_test Counts  : 0 -> {(y_te==0).sum()} | 1 -> {(y_te==1).sum()}")
