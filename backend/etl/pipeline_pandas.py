import pandas as pd
import numpy as np
import yaml
import os
import hashlib

# Define paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
RAW_DIR = os.path.join(DATA_DIR, "synthea_sample_data_csv_nov2021")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "risk_rules.yaml")

OBS_WHITELIST = [
    "Body Mass Index",
    "Body Height",
    "Body Weight",
    "Systolic Blood Pressure",
    "Diastolic Blood Pressure",
    "Hemoglobin A1c/Hemoglobin.total in Blood",
    "Glucose",
    "Glucose [Mass/volume] in Blood",
    "Heart rate",
    "Estimated Glomerular Filtration Rate",
    "Creatinine",
    "Total Cholesterol",
    "Low Density Lipoprotein Cholesterol",
    "High Density Lipoprotein Cholesterol",
    "Triglycerides"
]

def load_risk_rules(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def run_pipeline():
    print("Initializing Pandas ETL Pipeline...")
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    print("Reading raw data...")
    patients_raw = pd.read_csv(os.path.join(RAW_DIR, "patients.csv"))
    encounters_raw = pd.read_csv(os.path.join(RAW_DIR, "encounters.csv"))
    conditions_raw = pd.read_csv(os.path.join(RAW_DIR, "conditions.csv"))
    medications_raw = pd.read_csv(os.path.join(RAW_DIR, "medications.csv"))
    observations_raw = pd.read_csv(os.path.join(RAW_DIR, "observations.csv"))
    procedures_raw = pd.read_csv(os.path.join(RAW_DIR, "procedures.csv"))
    providers_raw = pd.read_csv(os.path.join(RAW_DIR, "providers.csv"))
    organizations_raw = pd.read_csv(os.path.join(RAW_DIR, "organizations.csv"))

    print("Mapping to Canonical Schema...")
    
    # 1. Patient
    patients_canonical = patients_raw[['Id', 'BIRTHDATE', 'DEATHDATE', 'GENDER', 'RACE', 'ETHNICITY', 'MARITAL', 'CITY', 'STATE']].copy()
    patients_canonical.columns = ['patient_id', 'birth_date', 'death_date', 'gender', 'race', 'ethnicity', 'marital_status', 'city', 'state']
    
    patients_canonical['birth_date'] = pd.to_datetime(patients_canonical['birth_date'])
    ref_date = pd.to_datetime("2021-11-01")
    patients_canonical['age'] = ((ref_date - patients_canonical['birth_date']).dt.days / 365.25).round(1)

    # 2. Provider
    providers_canonical = providers_raw[['Id', 'ORGANIZATION', 'NAME', 'GENDER', 'SPECIALITY']].copy()
    providers_canonical.columns = ['provider_id', 'organization_id', 'provider_name', 'gender', 'specialty']

    # 3. Organization
    organizations_canonical = organizations_raw[['Id', 'NAME', 'CITY', 'STATE']].copy()
    organizations_canonical.columns = ['organization_id', 'organization_name', 'city', 'state']

    # 4. Encounter
    encounters_canonical = encounters_raw[['Id', 'PATIENT', 'PROVIDER', 'ORGANIZATION', 'ENCOUNTERCLASS', 'START', 'STOP']].copy()
    encounters_canonical.columns = ['encounter_id', 'patient_id', 'provider_id', 'organization_id', 'encounter_type', 'start_datetime', 'end_datetime']

    # UUID Generator with index to guarantee uniqueness
    def make_uuid(df):
        return [hashlib.md5(f"{idx}_{val}".encode()).hexdigest() for idx, val in enumerate(df.values)]

    # 5. Condition
    conditions_canonical = conditions_raw[['ENCOUNTER', 'PATIENT', 'CODE', 'DESCRIPTION', 'START', 'STOP']].copy()
    conditions_canonical.columns = ['encounter_id', 'patient_id', 'snomed_code', 'condition_name', 'onset_date', 'stop_date']
    conditions_canonical['condition_id'] = make_uuid(conditions_canonical[['patient_id', 'encounter_id', 'snomed_code', 'onset_date']])

    # 6. Medication
    medications_canonical = medications_raw[['ENCOUNTER', 'PATIENT', 'CODE', 'DESCRIPTION', 'START', 'STOP']].copy()
    medications_canonical.columns = ['encounter_id', 'patient_id', 'rxnorm_code', 'medication_name', 'start_date', 'stop_date']
    medications_canonical['medication_id'] = make_uuid(medications_canonical[['patient_id', 'encounter_id', 'rxnorm_code', 'start_date']])

    # 7. Procedure
    procedures_canonical = procedures_raw[['ENCOUNTER', 'PATIENT', 'DESCRIPTION', 'START']].copy()
    procedures_canonical.columns = ['encounter_id', 'patient_id', 'procedure_name', 'procedure_date']
    procedures_canonical['procedure_id'] = make_uuid(procedures_canonical[['patient_id', 'encounter_id', 'procedure_name', 'procedure_date']])

    # 8. Observation
    obs_filtered = observations_raw[observations_raw['DESCRIPTION'].isin(OBS_WHITELIST)].copy()
    observations_canonical = obs_filtered[['ENCOUNTER', 'PATIENT', 'DESCRIPTION', 'VALUE', 'UNITS', 'DATE']].copy()
    observations_canonical.columns = ['encounter_id', 'patient_id', 'observation_name', 'observation_value', 'observation_unit', 'observation_date']
    observations_canonical['observation_id'] = make_uuid(observations_canonical[['patient_id', 'encounter_id', 'observation_name', 'observation_date']])

    # Write Canonical Datasets
    print("Writing Canonical Datasets to Parquet...")
    def write_parquet(df, name):
        out_path = os.path.join(PROCESSED_DIR, f"{name}.parquet")
        # Ensure dates are strings for pyarrow compatibility if not datetime
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str)
                # handle float nan strings
                df[col] = df[col].replace('nan', None)
        df.to_parquet(out_path, engine="pyarrow", index=False)
        print(f"  Saved {name} ({len(df)} rows)")

    write_parquet(patients_canonical, "patients")
    write_parquet(providers_canonical, "providers")
    write_parquet(organizations_canonical, "organizations")
    write_parquet(encounters_canonical, "encounters")
    write_parquet(conditions_canonical, "conditions")
    write_parquet(medications_canonical, "medications")
    write_parquet(procedures_canonical, "procedures")
    write_parquet(observations_canonical, "observations")

    # Feature Engineering
    print("\nEngineering ML Features...")
    
    # Base
    features_df = patients_canonical[['patient_id', 'age', 'gender', 'death_date', 'race']].copy()
    features_df['is_female'] = (features_df['gender'] == 'F').astype(int)
    features_df['is_deceased'] = features_df['death_date'].notna().astype(int)
    features_df.drop(['gender', 'death_date'], axis=1, inplace=True)

    # Encounters
    enc_counts = encounters_canonical.groupby('patient_id').size().reset_index(name='total_encounters')
    enc_types = encounters_canonical.pivot_table(index='patient_id', columns='encounter_type', aggfunc='size', fill_value=0).reset_index()
    for col in ['wellness', 'ambulatory', 'emergency', 'inpatient', 'urgentcare']:
        if col not in enc_types.columns:
            enc_types[col] = 0
        enc_types = enc_types.rename(columns={col: f"{col}_encounters"})
    features_df = features_df.merge(enc_counts, on='patient_id', how='left').merge(enc_types, on='patient_id', how='left')

    # Conditions
    cond_counts = conditions_canonical.groupby('patient_id').size().reset_index(name='total_conditions')
    chronic = conditions_canonical[conditions_canonical['stop_date'].isna()].groupby('patient_id').size().reset_index(name='chronic_conditions')
    
    cond_flags = conditions_canonical.groupby('patient_id').agg(
        has_diabetes=('condition_name', lambda x: x.str.lower().str.contains('diabetes').any()),
        has_hypertension=('condition_name', lambda x: x.str.lower().str.contains('hypertension|hypertensive').any()),
        has_ckd=('condition_name', lambda x: x.str.lower().str.contains('chronic kidney').any()),
        has_heart_failure=('condition_name', lambda x: x.str.lower().str.contains('heart failure').any()),
        has_copd=('condition_name', lambda x: x.str.lower().str.contains('chronic obstructive').any()),
        has_obesity=('condition_name', lambda x: x.str.lower().str.contains('obesity|body mass index 30\\+').any()),
    ).reset_index()
    
    # Cast flags to int
    for c in ['has_diabetes', 'has_hypertension', 'has_ckd', 'has_heart_failure', 'has_copd', 'has_obesity']:
        cond_flags[c] = cond_flags[c].astype(int)
        
    features_df = features_df.merge(cond_counts, on='patient_id', how='left').merge(chronic, on='patient_id', how='left').merge(cond_flags, on='patient_id', how='left')

    # Medications
    med_counts = medications_canonical.groupby('patient_id').size().reset_index(name='total_medications')
    active_meds = medications_canonical[medications_canonical['stop_date'].isna()].groupby('patient_id').size().reset_index(name='active_medications')
    features_df = features_df.merge(med_counts, on='patient_id', how='left').merge(active_meds, on='patient_id', how='left')

    # Procedures
    proc_counts = procedures_canonical.groupby('patient_id').size().reset_index(name='total_procedures')
    features_df = features_df.merge(proc_counts, on='patient_id', how='left')

    # Observations
    obs_mapping = {
        "Body Mass Index": "latest_bmi",
        "Systolic Blood Pressure": "latest_systolic_bp",
        "Diastolic Blood Pressure": "latest_diastolic_bp",
        "Hemoglobin A1c/Hemoglobin.total in Blood": "latest_hba1c",
        "Glucose": "latest_glucose",
        "Glucose [Mass/volume] in Blood": "latest_glucose", 
        "Estimated Glomerular Filtration Rate": "latest_egfr",
        "Total Cholesterol": "latest_cholesterol",
        "High Density Lipoprotein Cholesterol": "latest_hdl",
        "Low Density Lipoprotein Cholesterol": "latest_ldl",
        "Triglycerides": "latest_triglycerides",
        "Heart rate": "latest_heart_rate"
    }

    obs = observations_canonical.copy()
    obs['feature_name'] = obs['observation_name'].map(obs_mapping)
    obs = obs.dropna(subset=['feature_name'])
    obs['observation_value'] = pd.to_numeric(obs['observation_value'], errors='coerce')
    obs = obs.dropna(subset=['observation_value'])
    obs = obs.sort_values('observation_date').groupby(['patient_id', 'feature_name']).tail(1)
    
    obs_pivot = obs.pivot(index='patient_id', columns='feature_name', values='observation_value').reset_index()
    for expected_col in set(obs_mapping.values()):
        if expected_col not in obs_pivot.columns:
            obs_pivot[expected_col] = np.nan
            
    features_df = features_df.merge(obs_pivot, on='patient_id', how='left')
    
    # Fill NAs for counts and flags before evaluating rules
    fill_cols = ['total_encounters', 'wellness_encounters', 'ambulatory_encounters', 'emergency_encounters', 'inpatient_encounters', 'urgentcare_encounters',
                 'total_conditions', 'chronic_conditions', 'has_diabetes', 'has_hypertension', 'has_ckd', 'has_heart_failure', 'has_copd', 'has_obesity',
                 'total_medications', 'active_medications', 'total_procedures']
    features_df[fill_cols] = features_df[fill_cols].fillna(0)

    # Apply Risk Rules
    rules_config = load_risk_rules(CONFIG_PATH)
    min_criteria = rules_config.get("high_risk_threshold", {}).get("min_criteria_met", 3)
    
    features_df['risk_criteria_met'] = 0
    
    for rule in rules_config.get("rules", []):
        rule_type = rule.get("type")
        cond = None
        
        if rule_type == "condition_flag":
            cond = (features_df[rule["feature_column"]] == rule["value"])
            
        elif rule_type in ["condition_count", "observation_threshold"]:
            col = rule["feature_column"]
            op = rule["operator"]
            val = rule["value"]
            if op == ">=":
                cond = (features_df[col] >= val)
            elif op == ">":
                cond = (features_df[col] > val)
            elif op == "==":
                cond = (features_df[col] == val)
                
        elif rule_type == "composite":
            c_cond = None
            for c in rule.get("conditions", []):
                col = c["feature_column"]
                op = c["operator"]
                val = c["value"]
                curr = None
                if op == ">=":
                    curr = (features_df[col] >= val)
                elif op == ">":
                    curr = (features_df[col] > val)
                
                if c_cond is None:
                    c_cond = curr
                else:
                    c_cond = c_cond & curr
            cond = c_cond
            
        if cond is not None:
            features_df['risk_criteria_met'] += cond.astype(int).fillna(0)
            
    features_df['is_high_risk'] = (features_df['risk_criteria_met'] >= min_criteria).astype(int)
    
    write_parquet(features_df, "features")
    print("Pandas ETL Pipeline Complete!")

if __name__ == "__main__":
    run_pipeline()
