from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType,
    DateType,
    TimestampType,
)

# Patient Schema
patient_schema = StructType([
    StructField("Id", StringType(), False),
    StructField("BIRTHDATE", DateType(), True),
    StructField("DEATHDATE", DateType(), True),
    StructField("SSN", StringType(), True),
    StructField("DRIVERS", StringType(), True),
    StructField("PASSPORT", StringType(), True),
    StructField("PREFIX", StringType(), True),
    StructField("FIRST", StringType(), True),
    StructField("LAST", StringType(), True),
    StructField("SUFFIX", StringType(), True),
    StructField("MAIDEN", StringType(), True),
    StructField("MARITAL", StringType(), True),
    StructField("RACE", StringType(), True),
    StructField("ETHNICITY", StringType(), True),
    StructField("GENDER", StringType(), True),
    StructField("BIRTHPLACE", StringType(), True),
    StructField("ADDRESS", StringType(), True),
    StructField("CITY", StringType(), True),
    StructField("STATE", StringType(), True),
    StructField("COUNTY", StringType(), True),
    StructField("ZIP", StringType(), True),
    StructField("LAT", DoubleType(), True),
    StructField("LON", DoubleType(), True),
    StructField("HEALTHCARE_EXPENSES", DoubleType(), True),
    StructField("HEALTHCARE_COVERAGE", DoubleType(), True),
])

# Encounter Schema
encounter_schema = StructType([
    StructField("Id", StringType(), False),
    StructField("START", TimestampType(), True),
    StructField("STOP", TimestampType(), True),
    StructField("PATIENT", StringType(), True),
    StructField("ORGANIZATION", StringType(), True),
    StructField("PROVIDER", StringType(), True),
    StructField("PAYER", StringType(), True),
    StructField("ENCOUNTERCLASS", StringType(), True),
    StructField("CODE", StringType(), True),
    StructField("DESCRIPTION", StringType(), True),
    StructField("BASE_ENCOUNTER_COST", DoubleType(), True),
    StructField("TOTAL_CLAIM_COST", DoubleType(), True),
    StructField("PAYER_COVERAGE", DoubleType(), True),
    StructField("REASONCODE", StringType(), True),
    StructField("REASONDESCRIPTION", StringType(), True),
])

# Condition Schema
condition_schema = StructType([
    StructField("START", DateType(), True),
    StructField("STOP", DateType(), True),
    StructField("PATIENT", StringType(), True),
    StructField("ENCOUNTER", StringType(), True),
    StructField("CODE", StringType(), True),
    StructField("DESCRIPTION", StringType(), True),
])

# Medication Schema
medication_schema = StructType([
    StructField("START", TimestampType(), True),
    StructField("STOP", TimestampType(), True),
    StructField("PATIENT", StringType(), True),
    StructField("PAYER", StringType(), True),
    StructField("ENCOUNTER", StringType(), True),
    StructField("CODE", StringType(), True),
    StructField("DESCRIPTION", StringType(), True),
    StructField("BASE_COST", DoubleType(), True),
    StructField("PAYER_COVERAGE", DoubleType(), True),
    StructField("DISPENSES", IntegerType(), True),
    StructField("TOTALCOST", DoubleType(), True),
    StructField("REASONCODE", StringType(), True),
    StructField("REASONDESCRIPTION", StringType(), True),
])

# Observation Schema
observation_schema = StructType([
    StructField("DATE", TimestampType(), True),
    StructField("PATIENT", StringType(), True),
    StructField("ENCOUNTER", StringType(), True),
    StructField("CATEGORY", StringType(), True),
    StructField("CODE", StringType(), True),
    StructField("DESCRIPTION", StringType(), True),
    StructField("VALUE", StringType(), True), # Some observations are textual
    StructField("UNITS", StringType(), True),
    StructField("TYPE", StringType(), True),
])

# Procedure Schema
procedure_schema = StructType([
    StructField("START", TimestampType(), True),
    StructField("STOP", TimestampType(), True),
    StructField("PATIENT", StringType(), True),
    StructField("ENCOUNTER", StringType(), True),
    StructField("CODE", StringType(), True),
    StructField("DESCRIPTION", StringType(), True),
    StructField("BASE_COST", DoubleType(), True),
    StructField("REASONCODE", StringType(), True),
    StructField("REASONDESCRIPTION", StringType(), True),
])

# Provider Schema
provider_schema = StructType([
    StructField("Id", StringType(), False),
    StructField("ORGANIZATION", StringType(), True),
    StructField("NAME", StringType(), True),
    StructField("GENDER", StringType(), True),
    StructField("SPECIALITY", StringType(), True),
    StructField("ADDRESS", StringType(), True),
    StructField("CITY", StringType(), True),
    StructField("STATE", StringType(), True),
    StructField("ZIP", StringType(), True),
    StructField("LAT", DoubleType(), True),
    StructField("LON", DoubleType(), True),
    StructField("UTILIZATION", IntegerType(), True),
])

# Organization Schema
organization_schema = StructType([
    StructField("Id", StringType(), False),
    StructField("NAME", StringType(), True),
    StructField("ADDRESS", StringType(), True),
    StructField("CITY", StringType(), True),
    StructField("STATE", StringType(), True),
    StructField("ZIP", StringType(), True),
    StructField("LAT", DoubleType(), True),
    StructField("LON", DoubleType(), True),
    StructField("PHONE", StringType(), True),
    StructField("REVENUE", DoubleType(), True),
    StructField("UTILIZATION", IntegerType(), True),
])
