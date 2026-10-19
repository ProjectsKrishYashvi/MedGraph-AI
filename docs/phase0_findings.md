# Phase 0 — Research & Data Understanding Findings

## 1. Dataset Overview

The dataset consists of 8 Synthea CSV files representing a synthetic cohort of patients and their healthcare journeys.

*   **Patients**: 1,163 total (Mean age: 45.0, 547 Male, 616 Female, 14.0% deceased)
*   **Encounters**: 61,459 total (Mean: 52.8 per patient, mostly wellness and ambulatory)
*   **Conditions**: 38,094 total (Mean: 33.2 per patient)
*   **Medications**: 56,430 total (Mean: 50.5 per patient)
*   **Observations**: 531,144 total
*   **Procedures**: 83,823 total
*   **Providers**: 5,056 total
*   **Organizations**: 1,127 total

Data quality is generally excellent. Referential integrity is 100% — there are zero orphan records for foreign key relationships between these core tables.

## 2. Entity Relationship Validation

The frozen data model specified in `DATABASE.md` is fully supported by the underlying data:

*   `Encounter.PATIENT` -> `Patient.Id` (100% valid)
*   `Encounter.PROVIDER` -> `Provider.Id` (100% valid)
*   `Encounter.ORGANIZATION` -> `Organization.Id` (100% valid)
*   `Provider.ORGANIZATION` -> `Organization.Id` (100% valid)
*   `Condition/Medication/Observation/Procedure.ENCOUNTER` -> `Encounter.Id` (100% valid)
*   `Condition/Medication/Observation/Procedure.PATIENT` -> `Patient.Id` (100% valid)

**Conclusion:** The graph schema (`Patient -> Encounter -> {Events}`) is perfectly aligned with the source data structure.

## 3. Code Systems (Critical Findings)

*   **Conditions:** Synthea uses **SNOMED CT** codes (e.g., `10509002`), not ICD-10 as initially presumed in the architecture docs.
*   **Medications:** Synthea already uses **RxNorm** numeric codes (e.g., `1014676`).
*   **Reference Data:**
    *   The provided ICD-10 reference file contains standard ICD-10-CM codes.
    *   The provided RxNorm reference file (`RXNCONSO.RRF`) is a standard UMLS-style rich reference file.

**ETL Strategy Adjustment:**
The ETL pipeline will treat SNOMED CT as the primary condition code. If an external crosswalk is unavailable, we will construct a lookup from the Synthea descriptions. The RxNorm step will be an enrichment/normalization step rather than a strict mapping from a proprietary code.

## 4. Observation Filtering

The `observations.csv` contains 247 distinct observation types, many of which are surveys or administrative. To prevent graph bloat and focus the ML model, Phase 1 ETL will filter observations to this clinically relevant subset:

*   Body Height, Body Weight, Body Mass Index
*   Systolic / Diastolic Blood Pressure
*   Heart rate, Respiratory rate
*   Hemoglobin A1c
*   Glucose (and Mass/volume variants)
*   Estimated Glomerular Filtration Rate (eGFR)
*   Total Cholesterol, Triglycerides, LDL, HDL
*   Creatinine

## 5. Feature Engineering Plan (ML Input)

Based on the exploration, the PySpark ETL (Phase 1) will engineer a flat feature table with the following per-patient columns:

**Demographics:** `age`, `is_female` (0/1), `is_deceased` (0/1)
**Encounter Metrics:** `total_encounters`, `wellness_encounters`, `ambulatory_encounters`, `emergency_encounters`, `inpatient_encounters`, `urgentcare_encounters`
**Condition Metrics:** `total_conditions`, `chronic_conditions` (count of conditions with no STOP date), `has_diabetes`, `has_hypertension`, `has_ckd`, `has_heart_failure`, `has_copd`, `has_obesity`
**Medication Metrics:** `total_medications`, `active_medications` (no STOP date)
**Observation Metrics (Latest numeric value):** `latest_bmi`, `latest_systolic_bp`, `latest_diastolic_bp`, `latest_hba1c`, `latest_glucose`, `latest_egfr`, `latest_cholesterol`, `latest_hdl`, `latest_ldl`, `latest_triglycerides`, `latest_heart_rate`
**Procedure Metrics:** `total_procedures`

## 6. High-Risk Patient Label Definition

We defined a composite rules-based target label for the XGBoost model. A patient is classified as **High-Risk (1)** if they meet **>= 3** of the following criteria:

1.  Has diabetes
2.  Has hypertension
3.  Has CKD
4.  Has heart failure
5.  Has COPD
6.  Has >= 3 ongoing chronic conditions (no STOP date)
7.  Latest HbA1c > 7.0
8.  Latest Systolic BP > 140
9.  Age >= 65 with >= 2 chronic conditions

**Label Distribution:**
Using a threshold of `>= 3` criteria yields an excellent, realistic class balance for the synthetic cohort:
*   Total Patients: 1,163
*   High-Risk: 328 (28.2%)
*   Low-Risk: 835 (71.8%)

---

## 7. Architectural Implications & Recommendations

**Verdict:** No changes to the frozen architecture are required.

The architecture described in `ARCHITECTURE.md` is robust and perfectly suited to the data we explored. The only deviation discovered is at the data-level implementation detail regarding Code Systems (SNOMED CT vs ICD-10).

*   **Data Layer:** Synthea data fits the proposed graph structure flawlessly.
*   **ETL Layer:** PySpark is well-suited to process this 146MB dataset and generate the planned feature table. The ICD-10 mapping step will be adjusted to an enrichment step based on SNOMED CT.
*   **Graph Database:** Neo4j will easily handle the scale of this dataset (~1,163 patients, ~61k encounters, ~100k events after filtering observations).
*   **Machine Learning Layer:** The proposed feature set and the defined target label (`>= 3` criteria) provide a strong, clinically plausible foundation for the XGBoost model. Class balance (28.2% positive) is ideal.
*   **Orchestration / RAG:** No implications found during data exploration; the plan remains solid.

We are ready to proceed to **Phase 1 — ETL & Canonical Data Layer**.
