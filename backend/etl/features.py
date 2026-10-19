import yaml
import os
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType

def load_risk_rules(config_path: str) -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def engineer_features(
    patients_df: DataFrame,
    encounters_df: DataFrame,
    conditions_df: DataFrame,
    medications_df: DataFrame,
    observations_df: DataFrame,
    procedures_df: DataFrame,
    config_path: str
) -> DataFrame:
    """
    Generate a flat feature table (one row per patient) for ML processing.
    """
    
    # 1. Base Demographics
    features_df = patients_df.select(
        F.col("patient_id"),
        F.col("age"),
        F.when(F.col("gender") == "F", 1).otherwise(0).alias("is_female"),
        (F.col("death_date").isNotNull()).cast(IntegerType()).alias("is_deceased"),
        F.col("race")
    )

    # 2. Encounter Metrics
    enc_stats = encounters_df.groupBy("patient_id").agg(
        F.count("encounter_id").alias("total_encounters"),
        F.sum(F.when(F.col("encounter_type") == "wellness", 1).otherwise(0)).alias("wellness_encounters"),
        F.sum(F.when(F.col("encounter_type") == "ambulatory", 1).otherwise(0)).alias("ambulatory_encounters"),
        F.sum(F.when(F.col("encounter_type") == "emergency", 1).otherwise(0)).alias("emergency_encounters"),
        F.sum(F.when(F.col("encounter_type") == "inpatient", 1).otherwise(0)).alias("inpatient_encounters"),
        F.sum(F.when(F.col("encounter_type") == "urgentcare", 1).otherwise(0)).alias("urgentcare_encounters")
    )
    features_df = features_df.join(enc_stats, on="patient_id", how="left")

    # 3. Condition Metrics
    cond_stats = conditions_df.groupBy("patient_id").agg(
        F.count("condition_id").alias("total_conditions"),
        F.sum(F.when(F.col("stop_date").isNull(), 1).otherwise(0)).alias("chronic_conditions"),
        F.max(F.when(F.lower(F.col("condition_name")).like("%diabetes%"), 1).otherwise(0)).alias("has_diabetes"),
        F.max(F.when(F.lower(F.col("condition_name")).like("%hypertension%") | F.lower(F.col("condition_name")).like("%hypertensive%"), 1).otherwise(0)).alias("has_hypertension"),
        F.max(F.when(F.lower(F.col("condition_name")).like("%chronic kidney%"), 1).otherwise(0)).alias("has_ckd"),
        F.max(F.when(F.lower(F.col("condition_name")).like("%heart failure%"), 1).otherwise(0)).alias("has_heart_failure"),
        F.max(F.when(F.lower(F.col("condition_name")).like("%chronic obstructive%"), 1).otherwise(0)).alias("has_copd"),
        F.max(F.when(F.lower(F.col("condition_name")).like("%obesity%") | F.lower(F.col("condition_name")).like("%body mass index 30+%"), 1).otherwise(0)).alias("has_obesity")
    )
    features_df = features_df.join(cond_stats, on="patient_id", how="left")

    # 4. Medication Metrics
    med_stats = medications_df.groupBy("patient_id").agg(
        F.count("medication_id").alias("total_medications"),
        F.sum(F.when(F.col("stop_date").isNull(), 1).otherwise(0)).alias("active_medications")
    )
    features_df = features_df.join(med_stats, on="patient_id", how="left")

    # 5. Procedure Metrics
    proc_stats = procedures_df.groupBy("patient_id").agg(
        F.count("procedure_id").alias("total_procedures")
    )
    features_df = features_df.join(proc_stats, on="patient_id", how="left")

    # 6. Observation Metrics (Latest value per patient)
    # We want the latest numeric value for specific observations
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

    # Filter numeric only and map names
    num_obs = observations_df.filter(F.col("observation_value").cast("double").isNotNull())
    
    # Create mapping expression
    mapping_expr = F.lit(None)
    for raw_name, clean_name in obs_mapping.items():
        if mapping_expr is None:
            mapping_expr = F.when(F.col("observation_name") == raw_name, clean_name)
        else:
            mapping_expr = mapping_expr.when(F.col("observation_name") == raw_name, clean_name)
            
    num_obs = num_obs.withColumn("feature_name", mapping_expr).filter(F.col("feature_name").isNotNull())
    
    # Get latest per patient/feature
    from pyspark.sql.window import Window
    w = Window.partitionBy("patient_id", "feature_name").orderBy(F.col("observation_date").desc())
    latest_obs = num_obs.withColumn("rn", F.row_number().over(w)).filter(F.col("rn") == 1)
    
    # Pivot to columns
    obs_pivoted = latest_obs.groupBy("patient_id").pivot("feature_name").agg(F.first(F.col("observation_value").cast("double")))
    
    # Ensure all expected columns exist
    for expected_col in set(obs_mapping.values()):
        if expected_col not in obs_pivoted.columns:
            obs_pivoted = obs_pivoted.withColumn(expected_col, F.lit(None).cast("double"))
            
    features_df = features_df.join(obs_pivoted, on="patient_id", how="left")

    # 7. Apply Configurable Risk Rules
    rules_config = load_risk_rules(config_path)
    min_criteria = rules_config.get("high_risk_threshold", {}).get("min_criteria_met", 3)
    
    # Initialize criteria count
    features_df = features_df.withColumn("risk_criteria_met", F.lit(0))
    
    # Fill nulls with 0 for counts/flags before evaluating rules
    fill_cols = ["has_diabetes", "has_hypertension", "has_ckd", "has_heart_failure", 
                 "has_copd", "chronic_conditions", "age"]
    features_df = features_df.fillna(0, subset=fill_cols)
    
    for rule in rules_config.get("rules", []):
        rule_type = rule.get("type")
        cond_expr = None
        
        if rule_type == "condition_flag":
            cond_expr = (F.col(rule["feature_column"]) == rule["value"])
            
        elif rule_type == "condition_count" or rule_type == "observation_threshold":
            col_name = rule["feature_column"]
            op = rule["operator"]
            val = rule["value"]
            if op == ">=":
                cond_expr = (F.col(col_name) >= val)
            elif op == ">":
                cond_expr = (F.col(col_name) > val)
            elif op == "==":
                cond_expr = (F.col(col_name) == val)
                
        elif rule_type == "composite":
            conditions = rule.get("conditions", [])
            for c in conditions:
                col_name = c["feature_column"]
                op = c["operator"]
                val = c["value"]
                curr_expr = None
                if op == ">=":
                    curr_expr = (F.col(col_name) >= val)
                elif op == ">":
                    curr_expr = (F.col(col_name) > val)
                
                if cond_expr is None:
                    cond_expr = curr_expr
                else:
                    cond_expr = cond_expr & curr_expr
                    
        if cond_expr is not None:
            # If the condition evaluates to true, add 1 to criteria met. 
            # Note: We must handle NULLs in observation columns carefully (null > 7 is null, treated as false)
            features_df = features_df.withColumn(
                "risk_criteria_met", 
                F.col("risk_criteria_met") + F.when(cond_expr, 1).otherwise(0)
            )
            
    # Compute final label
    features_df = features_df.withColumn(
        "is_high_risk", 
        F.when(F.col("risk_criteria_met") >= min_criteria, 1).otherwise(0)
    )
    
    # Drop intermediate columns if desired (we'll keep risk_criteria_met for explainability)
    return features_df
