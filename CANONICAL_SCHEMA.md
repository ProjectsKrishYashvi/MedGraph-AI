# CANONICAL_SCHEMA.md

# Purpose

This document defines the canonical healthcare data model produced by the ETL pipeline.

It serves as the contract between:

- PySpark ETL
- Neo4j
- Feature Engineering
- Machine Learning
- LangGraph

Every downstream component depends on this schema.

---

# Core Entities

## Patient

Columns

- patient_id
- birth_date
- death_date
- gender
- race
- ethnicity
- marital_status
- city
- state

---

## Encounter

- encounter_id
- patient_id
- provider_id
- organization_id
- encounter_type
- start_datetime
- end_datetime

---

## Condition

- condition_id
- encounter_id
- patient_id
- snomed_code
- condition_name
- onset_date
- stop_date

Primary clinical terminology:

SNOMED CT

No ICD conversion in Version 1.

---

## Medication

- medication_id
- encounter_id
- patient_id
- rxnorm_code
- medication_name
- start_date
- stop_date

---

## Observation

- observation_id
- encounter_id
- patient_id
- observation_name
- observation_value
- observation_unit
- observation_date

Only clinically relevant observations are retained.

Initial whitelist:

- BMI
- Height
- Weight
- Systolic Blood Pressure
- Diastolic Blood Pressure
- HbA1c
- Blood Glucose
- Heart Rate
- Estimated Glomerular Filtration Rate
- Creatinine
- Total Cholesterol
- Low Density Lipoprotein Cholesterol
- High Density Lipoprotein Cholesterol
- Triglycerides

---

## Procedure

- procedure_id
- encounter_id
- patient_id
- procedure_name
- procedure_date

---

## Provider

- provider_id
- organization_id
- provider_name
- gender
- specialty

---

## Organization

- organization_id
- organization_name
- city
- state

---

# Feature Table

One row per patient.

Candidate features include:

## Demographics

- age
- gender
- race
- is_deceased

## Encounters

- total_encounters
- wellness_encounters
- ambulatory_encounters
- emergency_encounters
- inpatient_encounters
- urgentcare_encounters

## Conditions

- total_conditions
- chronic_conditions
- has_diabetes
- has_hypertension
- has_ckd
- has_copd
- has_heart_failure
- has_obesity

## Medications

- total_medications
- active_medications

## Observations

- latest_bmi
- latest_systolic_bp
- latest_diastolic_bp
- latest_hba1c
- latest_glucose
- latest_egfr
- latest_cholesterol
- latest_hdl
- latest_ldl
- latest_triglycerides
- latest_heart_rate

## Procedures

- total_procedures

---

# Risk Label

Risk labels are generated from configurable rules.

Rules must be loaded from:

config/risk_rules.yaml

The ETL pipeline must not hardcode thresholds.

---

# Data Types

Document the final data type for every field during implementation.

---

# Missing Values

Document the handling strategy for every feature.

---

# Validation Rules

Document all validation checks performed before exporting the canonical dataset.