import os
import pandas as pd
import numpy as np
import yaml

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "risk_rules.yaml")

EXPECTED_FILES = [
    "patients.parquet",
    "providers.parquet",
    "organizations.parquet",
    "encounters.parquet",
    "conditions.parquet",
    "medications.parquet",
    "procedures.parquet",
    "observations.parquet",
    "features.parquet"
]

PK_MAPPING = {
    "patients.parquet": "patient_id",
    "providers.parquet": "provider_id",
    "organizations.parquet": "organization_id",
    "encounters.parquet": "encounter_id",
    "conditions.parquet": "condition_id",
    "medications.parquet": "medication_id",
    "procedures.parquet": "procedure_id",
    "observations.parquet": "observation_id",
    "features.parquet": "patient_id"
}

FK_CHECKS = [
    ("encounters.parquet", "patient_id", "patients.parquet", "patient_id"),
    ("encounters.parquet", "provider_id", "providers.parquet", "provider_id"),
    ("encounters.parquet", "organization_id", "organizations.parquet", "organization_id"),
    ("providers.parquet", "organization_id", "organizations.parquet", "organization_id"),
    ("conditions.parquet", "patient_id", "patients.parquet", "patient_id"),
    ("conditions.parquet", "encounter_id", "encounters.parquet", "encounter_id"),
    ("medications.parquet", "patient_id", "patients.parquet", "patient_id"),
    ("medications.parquet", "encounter_id", "encounters.parquet", "encounter_id"),
    ("procedures.parquet", "patient_id", "patients.parquet", "patient_id"),
    ("procedures.parquet", "encounter_id", "encounters.parquet", "encounter_id"),
    ("observations.parquet", "patient_id", "patients.parquet", "patient_id"),
    ("observations.parquet", "encounter_id", "encounters.parquet", "encounter_id"),
]

def validate():
    print("================================================================================")
    print("CANONICAL DATASET VALIDATION REPORT")
    print("================================================================================\n")
    
    # 1. File Existence & Row Count Check
    print("[1/5] Checking file existence & row counts...")
    dfs = {}
    for filename in EXPECTED_FILES:
        filepath = os.path.join(PROCESSED_DIR, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"CRITICAL ERROR: Missing processed file {filepath}")
        df = pd.read_parquet(filepath)
        dfs[filename] = df
        print(f"  [OK] {filename:<22}: {len(df):>7} rows | Columns: {len(df.columns)}")

    # 2. Primary Key Uniqueness & Non-Null Check
    print("\n[2/5] Validating Primary Key Uniqueness & Integrity...")
    for filename, pk_col in PK_MAPPING.items():
        df = dfs[filename]
        null_count = df[pk_col].isna().sum()
        unique_count = df[pk_col].nunique()
        total_count = len(df)
        
        if null_count > 0:
            raise ValueError(f"CRITICAL ERROR: {filename} contains {null_count} null primary keys in '{pk_col}'")
        if unique_count != total_count:
            raise ValueError(f"CRITICAL ERROR: {filename} has duplicate primary keys in '{pk_col}' ({unique_count} unique vs {total_count} rows)")
        print(f"  [OK] {filename:<22} ('{pk_col}'): {unique_count}/{total_count} unique, non-null PKs")

    # 3. Foreign Key Referential Integrity Check
    print("\n[3/5] Checking Foreign Key Referential Integrity...")
    for child_file, child_fk, parent_file, parent_pk in FK_CHECKS:
        child_df = dfs[child_file]
        parent_df = dfs[parent_file]
        
        # Filter non-null child FKs
        child_keys = set(child_df[child_fk].dropna().unique())
        parent_keys = set(parent_df[parent_pk].unique())
        
        orphans = child_keys - parent_keys
        if len(orphans) > 0:
            raise ValueError(f"CRITICAL ERROR: Found {len(orphans)} orphan keys in {child_file}.'{child_fk}' pointing to missing {parent_file}.'{parent_pk}'")
        print(f"  [OK] {child_file:<20}.'{child_fk}' -> {parent_file:<20}.'{parent_pk}': 0 orphans ({len(child_keys)} linked keys)")

    # 4. Feature Table Completeness & Target Label Verification
    print("\n[4/5] Verifying Feature Table Integrity & Target Label Distribution...")
    features_df = dfs["features.parquet"]
    patients_df = dfs["patients.parquet"]
    
    if len(features_df) != len(patients_df):
        raise ValueError(f"CRITICAL ERROR: Feature table row count ({len(features_df)}) does not match patient count ({len(patients_df)})")
        
    required_feature_cols = [
        "patient_id", "age", "is_female", "is_deceased", 
        "total_encounters", "total_conditions", "chronic_conditions", 
        "has_diabetes", "has_hypertension", "has_ckd", "has_heart_failure", "has_copd", "has_obesity",
        "total_medications", "active_medications", "total_procedures",
        "latest_bmi", "latest_systolic_bp", "latest_diastolic_bp", "latest_hba1c", "latest_glucose",
        "latest_egfr", "latest_cholesterol", "latest_hdl", "latest_ldl", "latest_triglycerides", "latest_heart_rate",
        "risk_criteria_met", "is_high_risk"
    ]
    
    missing_cols = set(required_feature_cols) - set(features_df.columns)
    if missing_cols:
        raise ValueError(f"CRITICAL ERROR: Feature table missing required columns: {missing_cols}")
        
    high_risk_count = features_df["is_high_risk"].sum()
    low_risk_count = (features_df["is_high_risk"] == 0).sum()
    pct_high_risk = (high_risk_count / len(features_df)) * 100
    
    print(f"  [OK] Patient count match: {len(features_df)} == {len(patients_df)}")
    print(f"  [OK] All {len(required_feature_cols)} required feature columns present.")
    print(f"  [OK] Target Label Balance:")
    print(f"      - High-Risk (1) : {high_risk_count:>4} ({pct_high_risk:.1f}%)")
    print(f"      - Low-Risk  (0) : {low_risk_count:>4} ({100 - pct_high_risk:.1f}%)")

    # 5. Summary
    print("\n[5/5] Final Verification Result:")
    print("  ==========================================================")
    print("  SUCCESS: All canonical dataset validation checks passed!")
    print("  ==========================================================")

if __name__ == "__main__":
    validate()
