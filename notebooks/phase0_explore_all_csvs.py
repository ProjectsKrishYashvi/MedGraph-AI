"""
Phase 0 — Section 1 & 2: Synthea CSV Exploration & Entity Relationship Mapping
Analyzes all 8 CSVs for structure, data quality, keys, and referential integrity.
"""

import csv
import json
import os
from collections import Counter, defaultdict

DATA_DIR = os.path.join("data", "synthea_sample_data_csv_nov2021")

CSV_FILES = [
    "patients.csv",
    "encounters.csv",
    "conditions.csv",
    "medications.csv",
    "observations.csv",
    "procedures.csv",
    "providers.csv",
    "organizations.csv",
]


def read_csv(filename):
    """Read a CSV file and return (headers, rows)."""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)
    return headers, rows


def analyze_nulls(headers, rows):
    """Count null/empty values per column."""
    null_counts = {h: 0 for h in headers}
    for row in rows:
        for h in headers:
            val = row.get(h, "")
            if val is None or val.strip() == "":
                null_counts[h] += 1
    return null_counts


def analyze_uniques(headers, rows):
    """Count unique values per column."""
    unique_counts = {}
    for h in headers:
        vals = set(row.get(h, "") for row in rows)
        unique_counts[h] = len(vals)
    return unique_counts


def print_separator():
    print("=" * 80)


def main():
    all_data = {}

    # =========================================================================
    # SECTION 1: CSV EXPLORATION
    # =========================================================================
    print("SECTION 1: SYNTHEA CSV EXPLORATION")
    print_separator()

    for filename in CSV_FILES:
        print(f"\n{'=' * 80}")
        print(f"FILE: {filename}")
        print(f"{'=' * 80}")

        headers, rows = read_csv(filename)
        all_data[filename] = (headers, rows)

        print(f"  Row Count: {len(rows)}")
        print(f"  Columns ({len(headers)}): {headers}")

        # Null analysis
        null_counts = analyze_nulls(headers, rows)
        nulls_present = {k: v for k, v in null_counts.items() if v > 0}
        if nulls_present:
            print(f"  Null/Empty Columns:")
            for col, count in sorted(nulls_present.items(), key=lambda x: -x[1]):
                pct = (count / len(rows)) * 100
                print(f"    {col}: {count} ({pct:.1f}%)")
        else:
            print(f"  Null/Empty Columns: None")

        # Unique values
        unique_counts = analyze_uniques(headers, rows)
        print(f"  Unique Value Counts:")
        for col, count in unique_counts.items():
            print(f"    {col}: {count}")

        # Sample row
        if rows:
            print(f"  Sample Row (first):")
            for k, v in rows[0].items():
                display_val = v[:80] if v else "(empty)"
                print(f"    {k}: {display_val}")

    # =========================================================================
    # SECTION 2: ENTITY RELATIONSHIP MAPPING
    # =========================================================================
    print(f"\n\n{'=' * 80}")
    print("SECTION 2: ENTITY RELATIONSHIP MAPPING")
    print_separator()

    # Collect all IDs
    _, patients = all_data["patients.csv"]
    _, encounters = all_data["encounters.csv"]
    _, conditions = all_data["conditions.csv"]
    _, medications = all_data["medications.csv"]
    _, observations = all_data["observations.csv"]
    _, procedures = all_data["procedures.csv"]
    _, providers = all_data["providers.csv"]
    _, organizations = all_data["organizations.csv"]

    patient_ids = set(r["Id"] for r in patients)
    encounter_ids = set(r["Id"] for r in encounters)
    provider_ids = set(r["Id"] for r in providers)
    org_ids = set(r["Id"] for r in organizations)

    print(f"\nPrimary Key Counts:")
    print(f"  Patients: {len(patient_ids)}")
    print(f"  Encounters: {len(encounter_ids)}")
    print(f"  Providers: {len(provider_ids)}")
    print(f"  Organizations: {len(org_ids)}")

    # Check FK: Encounter.PATIENT -> Patient.Id
    enc_patient_ids = set(r["PATIENT"] for r in encounters)
    orphan_enc_patients = enc_patient_ids - patient_ids
    print(f"\nFK: Encounter.PATIENT -> Patient.Id")
    print(f"  Unique patients in encounters: {len(enc_patient_ids)}")
    print(f"  Orphan encounters (no matching patient): {len(orphan_enc_patients)}")

    # Check FK: Encounter.PROVIDER -> Provider.Id
    enc_provider_ids = set(r["PROVIDER"] for r in encounters)
    orphan_enc_providers = enc_provider_ids - provider_ids
    print(f"\nFK: Encounter.PROVIDER -> Provider.Id")
    print(f"  Unique providers in encounters: {len(enc_provider_ids)}")
    print(f"  Orphan encounters (no matching provider): {len(orphan_enc_providers)}")

    # Check FK: Encounter.ORGANIZATION -> Organization.Id
    enc_org_ids = set(r["ORGANIZATION"] for r in encounters)
    orphan_enc_orgs = enc_org_ids - org_ids
    print(f"\nFK: Encounter.ORGANIZATION -> Organization.Id")
    print(f"  Unique orgs in encounters: {len(enc_org_ids)}")
    print(f"  Orphan encounters (no matching org): {len(orphan_enc_orgs)}")

    # Check FK: Provider.ORGANIZATION -> Organization.Id
    prov_org_ids = set(r["ORGANIZATION"] for r in providers)
    orphan_prov_orgs = prov_org_ids - org_ids
    print(f"\nFK: Provider.ORGANIZATION -> Organization.Id")
    print(f"  Unique orgs in providers: {len(prov_org_ids)}")
    print(f"  Orphan providers (no matching org): {len(orphan_prov_orgs)}")

    # Check conditions -> encounter, patient
    cond_patient_ids = set(r["PATIENT"] for r in conditions)
    cond_encounter_ids = set(r["ENCOUNTER"] for r in encounters)
    orphan_cond_patients = cond_patient_ids - patient_ids
    cond_enc_ids = set(r["ENCOUNTER"] for r in conditions)
    orphan_cond_encounters = cond_enc_ids - encounter_ids
    print(f"\nFK: Condition.PATIENT -> Patient.Id")
    print(f"  Orphan conditions (no matching patient): {len(orphan_cond_patients)}")
    print(f"FK: Condition.ENCOUNTER -> Encounter.Id")
    print(f"  Orphan conditions (no matching encounter): {len(orphan_cond_encounters)}")

    # Check medications -> encounter, patient
    med_patient_ids = set(r["PATIENT"] for r in medications)
    med_enc_ids = set(r["ENCOUNTER"] for r in medications)
    orphan_med_patients = med_patient_ids - patient_ids
    orphan_med_encounters = med_enc_ids - encounter_ids
    print(f"\nFK: Medication.PATIENT -> Patient.Id")
    print(f"  Orphan medications (no matching patient): {len(orphan_med_patients)}")
    print(f"FK: Medication.ENCOUNTER -> Encounter.Id")
    print(f"  Orphan medications (no matching encounter): {len(orphan_med_encounters)}")

    # Check observations -> encounter, patient
    obs_patient_ids = set(r["PATIENT"] for r in observations)
    obs_enc_ids = set(r["ENCOUNTER"] for r in observations)
    orphan_obs_patients = obs_patient_ids - patient_ids
    orphan_obs_encounters = obs_enc_ids - encounter_ids
    print(f"\nFK: Observation.PATIENT -> Patient.Id")
    print(f"  Orphan observations (no matching patient): {len(orphan_obs_patients)}")
    print(f"FK: Observation.ENCOUNTER -> Encounter.Id")
    print(f"  Orphan observations (no matching encounter): {len(orphan_obs_encounters)}")

    # Check procedures -> encounter, patient
    proc_patient_ids = set(r["PATIENT"] for r in procedures)
    proc_enc_ids = set(r["ENCOUNTER"] for r in procedures)
    orphan_proc_patients = proc_patient_ids - patient_ids
    orphan_proc_encounters = proc_enc_ids - encounter_ids
    print(f"\nFK: Procedure.PATIENT -> Patient.Id")
    print(f"  Orphan procedures (no matching patient): {len(orphan_proc_patients)}")
    print(f"FK: Procedure.ENCOUNTER -> Encounter.Id")
    print(f"  Orphan procedures (no matching encounter): {len(orphan_proc_encounters)}")

    # Cardinality analysis
    print(f"\nCARDINALITY ANALYSIS:")

    # Encounters per patient
    enc_per_patient = Counter(r["PATIENT"] for r in encounters)
    enc_counts = list(enc_per_patient.values())
    print(f"\n  Encounters per Patient:")
    print(f"    Min: {min(enc_counts)}")
    print(f"    Max: {max(enc_counts)}")
    print(f"    Mean: {sum(enc_counts)/len(enc_counts):.1f}")
    print(f"    Patients with 0 encounters: {len(patient_ids - enc_patient_ids)}")

    # Conditions per patient
    cond_per_patient = Counter(r["PATIENT"] for r in conditions)
    cond_counts = list(cond_per_patient.values())
    patients_with_no_conds = len(patient_ids - cond_patient_ids)
    print(f"\n  Conditions per Patient:")
    print(f"    Patients with conditions: {len(cond_per_patient)}")
    print(f"    Patients with no conditions: {patients_with_no_conds}")
    if cond_counts:
        print(f"    Min: {min(cond_counts)}")
        print(f"    Max: {max(cond_counts)}")
        print(f"    Mean: {sum(cond_counts)/len(cond_counts):.1f}")

    # Medications per patient
    med_per_patient = Counter(r["PATIENT"] for r in medications)
    med_counts = list(med_per_patient.values())
    patients_with_no_meds = len(patient_ids - med_patient_ids)
    print(f"\n  Medications per Patient:")
    print(f"    Patients with medications: {len(med_per_patient)}")
    print(f"    Patients with no medications: {patients_with_no_meds}")
    if med_counts:
        print(f"    Min: {min(med_counts)}")
        print(f"    Max: {max(med_counts)}")
        print(f"    Mean: {sum(med_counts)/len(med_counts):.1f}")

    # Observations per patient
    obs_per_patient = Counter(r["PATIENT"] for r in observations)
    obs_counts = list(obs_per_patient.values())
    print(f"\n  Observations per Patient:")
    print(f"    Patients with observations: {len(obs_per_patient)}")
    if obs_counts:
        print(f"    Min: {min(obs_counts)}")
        print(f"    Max: {max(obs_counts)}")
        print(f"    Mean: {sum(obs_counts)/len(obs_counts):.1f}")

    # Procedures per patient
    proc_per_patient = Counter(r["PATIENT"] for r in procedures)
    proc_counts = list(proc_per_patient.values())
    print(f"\n  Procedures per Patient:")
    print(f"    Patients with procedures: {len(proc_per_patient)}")
    if proc_counts:
        print(f"    Min: {min(proc_counts)}")
        print(f"    Max: {max(proc_counts)}")
        print(f"    Mean: {sum(proc_counts)/len(proc_counts):.1f}")

    # Providers per organization
    prov_per_org = Counter(r["ORGANIZATION"] for r in providers)
    prov_org_counts = list(prov_per_org.values())
    print(f"\n  Providers per Organization:")
    print(f"    Min: {min(prov_org_counts)}")
    print(f"    Max: {max(prov_org_counts)}")
    print(f"    Mean: {sum(prov_org_counts)/len(prov_org_counts):.1f}")


if __name__ == "__main__":
    main()
