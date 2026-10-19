import os
os.environ["HADOOP_HOME"] = "c:\\hadoop"
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType
import schema
import features

# Define paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
RAW_DIR = os.path.join(DATA_DIR, "synthea_sample_data_csv_nov2021")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "risk_rules.yaml")

# Observation Whitelist (Expanded from CANONICAL_SCHEMA.md)
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

def create_spark_session():
    return SparkSession.builder \
        .appName("MedGraph_ETL") \
        .master("local[*]") \
        .getOrCreate()

def run_pipeline():
    print("Initializing Spark Session...")
    spark = create_spark_session()
    
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    print("Reading raw data...")
    patients_raw = spark.read.csv(os.path.join(RAW_DIR, "patients.csv"), header=True, schema=schema.patient_schema)
    encounters_raw = spark.read.csv(os.path.join(RAW_DIR, "encounters.csv"), header=True, schema=schema.encounter_schema)
    conditions_raw = spark.read.csv(os.path.join(RAW_DIR, "conditions.csv"), header=True, schema=schema.condition_schema)
    medications_raw = spark.read.csv(os.path.join(RAW_DIR, "medications.csv"), header=True, schema=schema.medication_schema)
    observations_raw = spark.read.csv(os.path.join(RAW_DIR, "observations.csv"), header=True, schema=schema.observation_schema)
    procedures_raw = spark.read.csv(os.path.join(RAW_DIR, "procedures.csv"), header=True, schema=schema.procedure_schema)
    providers_raw = spark.read.csv(os.path.join(RAW_DIR, "providers.csv"), header=True, schema=schema.provider_schema)
    organizations_raw = spark.read.csv(os.path.join(RAW_DIR, "organizations.csv"), header=True, schema=schema.organization_schema)

    print("Mapping to Canonical Schema...")
    
    # 1. Patient
    # Age calculated as of Nov 1, 2021 (dataset generation date)
    ref_date = F.to_date(F.lit("2021-11-01"))
    patients_canonical = patients_raw.select(
        F.col("Id").alias("patient_id"),
        F.col("BIRTHDATE").alias("birth_date"),
        F.col("DEATHDATE").alias("death_date"),
        F.col("GENDER").alias("gender"),
        F.col("RACE").alias("race"),
        F.col("ETHNICITY").alias("ethnicity"),
        F.col("MARITAL").alias("marital_status"),
        F.col("CITY").alias("city"),
        F.col("STATE").alias("state")
    ).withColumn(
        "age", 
        F.round(F.months_between(ref_date, F.col("birth_date")) / 12, 1)
    )

    # 2. Provider
    providers_canonical = providers_raw.select(
        F.col("Id").alias("provider_id"),
        F.col("ORGANIZATION").alias("organization_id"),
        F.col("NAME").alias("provider_name"),
        F.col("GENDER").alias("gender"),
        F.col("SPECIALITY").alias("specialty")
    )
    
    # 3. Organization
    organizations_canonical = organizations_raw.select(
        F.col("Id").alias("organization_id"),
        F.col("NAME").alias("organization_name"),
        F.col("CITY").alias("city"),
        F.col("STATE").alias("state")
    )

    # 4. Encounter
    encounters_canonical = encounters_raw.select(
        F.col("Id").alias("encounter_id"),
        F.col("PATIENT").alias("patient_id"),
        F.col("PROVIDER").alias("provider_id"),
        F.col("ORGANIZATION").alias("organization_id"),
        F.col("ENCOUNTERCLASS").alias("encounter_type"),
        F.col("START").alias("start_datetime"),
        F.col("STOP").alias("end_datetime")
    )

    # 5. Condition
    conditions_canonical = conditions_raw.select(
        F.md5(F.concat_ws("_", F.col("PATIENT"), F.col("ENCOUNTER"), F.col("CODE"), F.col("START"))).alias("condition_id"),
        F.col("ENCOUNTER").alias("encounter_id"),
        F.col("PATIENT").alias("patient_id"),
        F.col("CODE").alias("snomed_code"),
        F.col("DESCRIPTION").alias("condition_name"),
        F.col("START").alias("onset_date"),
        F.col("STOP").alias("stop_date")
    )

    # 6. Medication
    medications_canonical = medications_raw.select(
        F.md5(F.concat_ws("_", F.col("PATIENT"), F.col("ENCOUNTER"), F.col("CODE"), F.col("START"))).alias("medication_id"),
        F.col("ENCOUNTER").alias("encounter_id"),
        F.col("PATIENT").alias("patient_id"),
        F.col("CODE").alias("rxnorm_code"),
        F.col("DESCRIPTION").alias("medication_name"),
        F.col("START").alias("start_date"),
        F.col("STOP").alias("stop_date")
    )

    # 7. Procedure
    procedures_canonical = procedures_raw.select(
        F.md5(F.concat_ws("_", F.col("PATIENT"), F.col("ENCOUNTER"), F.col("CODE"), F.col("START"))).alias("procedure_id"),
        F.col("ENCOUNTER").alias("encounter_id"),
        F.col("PATIENT").alias("patient_id"),
        F.col("DESCRIPTION").alias("procedure_name"),
        F.col("START").alias("procedure_date")
    )

    # 8. Observation (Filtered)
    observations_canonical = observations_raw.filter(
        F.col("DESCRIPTION").isin(OBS_WHITELIST)
    ).select(
        F.md5(F.concat_ws("_", F.col("PATIENT"), F.col("ENCOUNTER"), F.col("CODE"), F.col("DATE"))).alias("observation_id"),
        F.col("ENCOUNTER").alias("encounter_id"),
        F.col("PATIENT").alias("patient_id"),
        F.col("DESCRIPTION").alias("observation_name"),
        F.col("VALUE").alias("observation_value"),
        F.col("UNITS").alias("observation_unit"),
        F.col("DATE").alias("observation_date")
    )

    # Write Canonical Datasets
    print("Writing Canonical Datasets to Parquet...")
    def write_parquet(df, name):
        out_path = os.path.join(PROCESSED_DIR, f"{name}.parquet")
        df.write.mode("overwrite").parquet(out_path)
        print(f"  Saved {name} ({df.count()} rows)")

    write_parquet(patients_canonical, "patients")
    write_parquet(providers_canonical, "providers")
    write_parquet(organizations_canonical, "organizations")
    write_parquet(encounters_canonical, "encounters")
    write_parquet(conditions_canonical, "conditions")
    write_parquet(medications_canonical, "medications")
    write_parquet(procedures_canonical, "procedures")
    write_parquet(observations_canonical, "observations")

    # Generate Feature Table
    print("\nEngineering ML Features...")
    features_df = features.engineer_features(
        patients_canonical,
        encounters_canonical,
        conditions_canonical,
        medications_canonical,
        observations_canonical,
        procedures_canonical,
        CONFIG_PATH
    )
    
    write_parquet(features_df, "features")
    print("ETL Pipeline Complete!")
    
if __name__ == "__main__":
    run_pipeline()
