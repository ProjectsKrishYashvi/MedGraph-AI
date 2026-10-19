"""
Phase 0 - Sections 3-10: Deep analysis of conditions, observations, demographics,
medications, encounters, code systems, feature engineering, and risk label.
"""

import csv
import os
from collections import Counter, defaultdict
from datetime import datetime, date

DATA_DIR = os.path.join("data", "synthea_sample_data_csv_nov2021")


def read_csv(filename):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def compute_age(birthdate_str, ref_date=date(2021, 11, 1)):
    bd = parse_date(birthdate_str)
    if not bd:
        return None
    return (ref_date - bd).days / 365.25


def sep():
    print("=" * 80)


def main():
    patients = read_csv("patients.csv")
    encounters = read_csv("encounters.csv")
    conditions = read_csv("conditions.csv")
    medications = read_csv("medications.csv")
    observations = read_csv("observations.csv")
    procedures = read_csv("procedures.csv")

    # =========================================================================
    # SECTION 3: CODE SYSTEM ANALYSIS
    # =========================================================================
    print("SECTION 3: CODE SYSTEM ANALYSIS")
    sep()

    # Condition codes analysis
    cond_codes = [r["CODE"] for r in conditions]
    unique_cond_codes = set(cond_codes)
    print(f"\nCondition Code Analysis:")
    print(f"  Total condition records: {len(conditions)}")
    print(f"  Unique condition codes: {len(unique_cond_codes)}")
    print(f"  Sample codes: {list(unique_cond_codes)[:10]}")

    # Check if any codes look like ICD-10 (letter followed by digits)
    icd_like = [c for c in unique_cond_codes if c and c[0].isalpha()]
    snomed_like = [c for c in unique_cond_codes if c and c[0].isdigit()]
    print(f"  Codes starting with letter (ICD-10 like): {len(icd_like)}")
    print(f"  Codes starting with digit (SNOMED CT like): {len(snomed_like)}")
    print(f"  CONCLUSION: Synthea conditions use SNOMED CT codes, NOT ICD-10")

    # Medication codes analysis
    med_codes = [r["CODE"] for r in medications]
    unique_med_codes = set(med_codes)
    print(f"\nMedication Code Analysis:")
    print(f"  Unique medication codes: {len(unique_med_codes)}")
    print(f"  Sample codes: {list(unique_med_codes)[:5]}")
    print(f"  Sample descriptions: {[r['DESCRIPTION'] for r in medications[:3]]}")
    # RxNorm codes are numeric
    all_numeric = all(c.isdigit() for c in unique_med_codes if c)
    print(f"  All codes numeric (RxNorm style): {all_numeric}")
    print(f"  CONCLUSION: Synthea medications already use RxNorm codes")

    # Check ICD-10 reference file
    icd_file = os.path.join("data", "icd10cm-code-descriptions-2027", "icd10cm-codes-2027.txt")
    icd_count = 0
    icd_samples = []
    with open(icd_file, "r", encoding="utf-8") as f:
        for line in f:
            icd_count += 1
            if icd_count <= 5:
                icd_samples.append(line.strip())
    print(f"\nICD-10-CM Reference File:")
    print(f"  Total entries: {icd_count}")
    print(f"  Format: <code><tab/spaces><description>")
    print(f"  Samples: {icd_samples[:3]}")

    # Check RxNorm reference file
    rxn_file = os.path.join("data", "RxNorm_full_prescribe_07062026", "RXNCONSO.RRF")
    rxn_count = 0
    rxn_sources = Counter()
    rxn_tty = Counter()
    with open(rxn_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("|")
            rxn_count += 1
            if len(parts) > 11:
                rxn_sources[parts[11]] += 1
            if len(parts) > 12:
                rxn_tty[parts[12]] += 1
    print(f"\nRxNorm RXNCONSO.RRF Reference File:")
    print(f"  Total entries: {rxn_count}")
    print(f"  Sources (SAB): {rxn_sources.most_common(10)}")
    print(f"  Term Types (TTY): {rxn_tty.most_common(15)}")

    # Try to match some medication codes against RXNCONSO
    sample_med_codes = list(unique_med_codes)[:5]
    print(f"\n  Matching sample med codes against RXNCONSO:")
    rxn_by_rxcui = defaultdict(list)
    with open(rxn_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) > 14:
                rxcui = parts[0]
                if rxcui in sample_med_codes:
                    sab = parts[11] if len(parts) > 11 else ""
                    tty = parts[12] if len(parts) > 12 else ""
                    name = parts[14] if len(parts) > 14 else ""
                    rxn_by_rxcui[rxcui].append((sab, tty, name[:60]))
    for code in sample_med_codes[:3]:
        matches = rxn_by_rxcui.get(code, [])
        print(f"    Code {code}: {len(matches)} matches")
        for sab, tty, name in matches[:2]:
            print(f"      [{sab}/{tty}] {name}")

    # =========================================================================
    # SECTION 4: CLINICAL OBSERVATIONS DEEP DIVE
    # =========================================================================
    print(f"\n\nSECTION 4: CLINICAL OBSERVATIONS DEEP DIVE")
    sep()

    # Catalog all observation types
    obs_by_category = defaultdict(Counter)
    obs_type_counts = Counter()
    obs_value_types = Counter()
    for r in observations:
        cat = r.get("CATEGORY", "unknown") or "unknown"
        desc = r["DESCRIPTION"]
        obs_by_category[cat][desc] += 1
        obs_type_counts[desc] += 1
        obs_value_types[r.get("TYPE", "")] += 1

    print(f"\nObservation Categories:")
    for cat in sorted(obs_by_category.keys()):
        descs = obs_by_category[cat]
        print(f"  {cat}: {sum(descs.values())} records, {len(descs)} types")

    print(f"\nValue Types: {dict(obs_value_types)}")

    print(f"\nTop 30 Observation Types (by frequency):")
    for desc, count in obs_type_counts.most_common(30):
        print(f"  {desc}: {count}")

    # Identify clinically relevant observations
    clinical_obs = [
        "Body Height", "Body Weight", "Body Mass Index",
        "Systolic Blood Pressure", "Diastolic Blood Pressure",
        "Heart rate", "Respiratory rate",
        "Hemoglobin A1c/Hemoglobin.total in Blood",
        "Glucose", "Glucose [Mass/volume] in Blood",
        "Estimated Glomerular Filtration Rate",
        "Total Cholesterol", "Triglycerides",
        "Low Density Lipoprotein Cholesterol",
        "High Density Lipoprotein Cholesterol",
        "Creatinine",
    ]
    print(f"\nClinically Relevant Observations (value distributions):")
    for target_desc in clinical_obs:
        values = []
        for r in observations:
            if r["DESCRIPTION"] == target_desc and r.get("TYPE") == "numeric":
                try:
                    values.append(float(r["VALUE"]))
                except (ValueError, TypeError):
                    pass
        if values:
            values.sort()
            n = len(values)
            mean_val = sum(values) / n
            median_val = values[n // 2]
            print(f"  {target_desc}:")
            print(f"    Count: {n}, Min: {values[0]:.1f}, Max: {values[-1]:.1f}, "
                  f"Mean: {mean_val:.1f}, Median: {median_val:.1f}")

    # =========================================================================
    # SECTION 5: PATIENT DEMOGRAPHICS
    # =========================================================================
    print(f"\n\nSECTION 5: PATIENT DEMOGRAPHICS")
    sep()

    # Age distribution
    ages = []
    for p in patients:
        age = compute_age(p["BIRTHDATE"])
        if age is not None:
            ages.append(age)
    ages.sort()
    n = len(ages)

    print(f"\nAge Distribution (as of Nov 2021):")
    print(f"  Total patients: {n}")
    print(f"  Min: {ages[0]:.1f} years")
    print(f"  Max: {ages[-1]:.1f} years")
    print(f"  Mean: {sum(ages)/n:.1f} years")
    print(f"  Median: {ages[n//2]:.1f} years")

    # Age brackets
    brackets = Counter()
    for a in ages:
        if a < 18:
            brackets["0-17"] += 1
        elif a < 35:
            brackets["18-34"] += 1
        elif a < 50:
            brackets["35-49"] += 1
        elif a < 65:
            brackets["50-64"] += 1
        else:
            brackets["65+"] += 1
    print(f"  Age Brackets:")
    for b in ["0-17", "18-34", "35-49", "50-64", "65+"]:
        print(f"    {b}: {brackets.get(b, 0)} ({brackets.get(b,0)/n*100:.1f}%)")

    # Gender
    gender = Counter(p["GENDER"] for p in patients)
    print(f"\nGender: {dict(gender)}")

    # Race
    race = Counter(p["RACE"] for p in patients)
    print(f"\nRace:")
    for r_name, cnt in race.most_common():
        print(f"  {r_name}: {cnt} ({cnt/n*100:.1f}%)")

    # Ethnicity
    eth = Counter(p["ETHNICITY"] for p in patients)
    print(f"\nEthnicity: {dict(eth)}")

    # Marital status
    marital = Counter(p.get("MARITAL", "") or "unknown" for p in patients)
    print(f"\nMarital Status: {dict(marital)}")

    # Living vs deceased
    deceased = sum(1 for p in patients if p.get("DEATHDATE", "").strip())
    print(f"\nLiving: {n - deceased}, Deceased: {deceased} ({deceased/n*100:.1f}%)")

    # =========================================================================
    # SECTION 6: CONDITION ANALYSIS
    # =========================================================================
    print(f"\n\nSECTION 6: CONDITION ANALYSIS")
    sep()

    # Most common conditions
    cond_desc_counts = Counter(r["DESCRIPTION"] for r in conditions)
    print(f"\nTop 30 Conditions:")
    for desc, cnt in cond_desc_counts.most_common(30):
        print(f"  {desc}: {cnt}")

    # Conditions with no STOP date (chronic/ongoing)
    chronic_candidates = Counter()
    for r in conditions:
        if not r.get("STOP", "").strip():
            chronic_candidates[r["DESCRIPTION"]] += 1

    print(f"\nConditions with no STOP date (likely chronic/ongoing):")
    print(f"  Total records without STOP: {sum(chronic_candidates.values())}")
    print(f"  Top 20:")
    for desc, cnt in chronic_candidates.most_common(20):
        print(f"    {desc}: {cnt}")

    # Conditions per patient
    conds_per_patient = Counter(r["PATIENT"] for r in conditions)
    cond_counts = list(conds_per_patient.values())
    patients_no_conds = len(set(p["Id"] for p in patients) - set(conds_per_patient.keys()))
    print(f"\nConditions per Patient:")
    print(f"  Patients with conditions: {len(conds_per_patient)}")
    print(f"  Patients without conditions: {patients_no_conds}")
    print(f"  Min: {min(cond_counts)}, Max: {max(cond_counts)}, "
          f"Mean: {sum(cond_counts)/len(cond_counts):.1f}")

    # Unique conditions per patient
    patient_unique_conds = defaultdict(set)
    for r in conditions:
        patient_unique_conds[r["PATIENT"]].add(r["DESCRIPTION"])
    unique_cond_counts = [len(v) for v in patient_unique_conds.values()]
    print(f"  Unique conditions per patient - Min: {min(unique_cond_counts)}, "
          f"Max: {max(unique_cond_counts)}, Mean: {sum(unique_cond_counts)/len(unique_cond_counts):.1f}")

    # Key chronic diseases
    key_chronic = {
        "Diabetes": ["Diabetes", "diabetes"],
        "Hypertension": ["Hypertension", "hypertension"],
        "CKD": ["Chronic kidney disease", "chronic kidney"],
        "Heart Failure": ["Heart failure"],
        "COPD": ["Chronic obstructive"],
        "Coronary Heart Disease": ["Coronary Heart Disease"],
        "Asthma": ["Asthma"],
        "Stroke": ["Stroke"],
        "Atrial Fibrillation": ["Atrial Fibrillation"],
        "Obesity": ["Obesity", "Body mass index 30+"],
    }

    print(f"\nKey Chronic Disease Prevalence (patients with at least one record):")
    patient_disease_flags = defaultdict(set)
    for r in conditions:
        desc_lower = r["DESCRIPTION"].lower()
        for disease, keywords in key_chronic.items():
            for kw in keywords:
                if kw.lower() in desc_lower:
                    patient_disease_flags[disease].add(r["PATIENT"])
                    break

    for disease in key_chronic:
        count = len(patient_disease_flags.get(disease, set()))
        pct = count / len(patients) * 100
        print(f"  {disease}: {count} patients ({pct:.1f}%)")

    # Co-occurrence analysis
    print(f"\nCo-occurrence (patients with multiple chronic conditions):")
    patient_chronic_set = defaultdict(set)
    for disease, pat_set in patient_disease_flags.items():
        for p in pat_set:
            patient_chronic_set[p].add(disease)
    chronic_count_dist = Counter(len(v) for v in patient_chronic_set.values())
    for cnt in sorted(chronic_count_dist.keys()):
        print(f"  {cnt} chronic condition(s): {chronic_count_dist[cnt]} patients")

    # =========================================================================
    # SECTION 7: ENCOUNTER PATTERNS
    # =========================================================================
    print(f"\n\nSECTION 7: ENCOUNTER PATTERNS")
    sep()

    # Encounter types
    enc_types = Counter(r["ENCOUNTERCLASS"] for r in encounters)
    print(f"\nEncounter Types:")
    for etype, cnt in enc_types.most_common():
        print(f"  {etype}: {cnt} ({cnt/len(encounters)*100:.1f}%)")

    # Encounters per patient
    enc_per_patient = Counter(r["PATIENT"] for r in encounters)
    enc_counts = list(enc_per_patient.values())
    print(f"\nEncounters per Patient:")
    print(f"  Min: {min(enc_counts)}, Max: {max(enc_counts)}, "
          f"Mean: {sum(enc_counts)/len(enc_counts):.1f}")

    # Distribution
    brackets_enc = Counter()
    for c in enc_counts:
        if c <= 10:
            brackets_enc["1-10"] += 1
        elif c <= 25:
            brackets_enc["11-25"] += 1
        elif c <= 50:
            brackets_enc["26-50"] += 1
        elif c <= 100:
            brackets_enc["51-100"] += 1
        else:
            brackets_enc["100+"] += 1
    print(f"  Brackets:")
    for b in ["1-10", "11-25", "26-50", "51-100", "100+"]:
        print(f"    {b}: {brackets_enc.get(b, 0)}")

    # =========================================================================
    # SECTION 8: MEDICATION ANALYSIS
    # =========================================================================
    print(f"\n\nSECTION 8: MEDICATION ANALYSIS")
    sep()

    # Most prescribed
    med_desc_counts = Counter(r["DESCRIPTION"] for r in medications)
    print(f"\nTop 20 Medications:")
    for desc, cnt in med_desc_counts.most_common(20):
        print(f"  {desc[:70]}: {cnt}")

    # Active medications (no STOP date)
    active_meds = sum(1 for r in medications if not r.get("STOP", "").strip())
    print(f"\nActive medications (no STOP): {active_meds} ({active_meds/len(medications)*100:.1f}%)")

    # Medications per patient
    med_per_patient = Counter(r["PATIENT"] for r in medications)
    med_counts = list(med_per_patient.values())
    patients_no_meds = len(set(p["Id"] for p in patients) - set(med_per_patient.keys()))
    print(f"\nMedications per Patient:")
    print(f"  Patients with meds: {len(med_per_patient)}, without: {patients_no_meds}")
    print(f"  Min: {min(med_counts)}, Max: {max(med_counts)}, "
          f"Mean: {sum(med_counts)/len(med_counts):.1f}")

    # =========================================================================
    # SECTION 9: CANDIDATE FEATURE ENGINEERING
    # =========================================================================
    print(f"\n\nSECTION 9: CANDIDATE FEATURE ENGINEERING")
    sep()

    print(f"""
Candidate Features for ML (based on data exploration):

DEMOGRAPHICS:
  - age (computed from BIRTHDATE)
  - gender (binary encoding)
  - is_deceased (from DEATHDATE)

ENCOUNTER METRICS:
  - total_encounters
  - encounter_frequency (encounters per year of life)
  - wellness_encounter_count
  - ambulatory_encounter_count
  - emergency_encounter_count
  - inpatient_encounter_count
  - urgentcare_encounter_count

CONDITION METRICS:
  - total_conditions (all records)
  - unique_condition_count
  - chronic_condition_count (conditions without STOP date)
  - has_diabetes (flag)
  - has_hypertension (flag)
  - has_ckd (flag)
  - has_heart_failure (flag)
  - has_copd (flag)
  - has_obesity (flag)

MEDICATION METRICS:
  - total_medications
  - unique_medication_count
  - active_medication_count (no STOP date)

OBSERVATION METRICS (latest value per patient):
  - latest_bmi
  - latest_systolic_bp
  - latest_diastolic_bp
  - latest_hba1c
  - latest_glucose
  - latest_egfr (Estimated GFR)
  - latest_cholesterol
  - latest_hdl
  - latest_ldl
  - latest_triglycerides
  - latest_heart_rate

PROCEDURE METRICS:
  - total_procedures
  - unique_procedure_count
""")

    # =========================================================================
    # SECTION 10: HIGH-RISK PATIENT LABEL DEFINITION
    # =========================================================================
    print(f"\n\nSECTION 10: HIGH-RISK PATIENT LABEL DEFINITION")
    sep()

    # Build per-patient features needed for label
    patient_ids = [p["Id"] for p in patients]
    patient_ages = {}
    for p in patients:
        age = compute_age(p["BIRTHDATE"])
        patient_ages[p["Id"]] = age if age else 0

    # Chronic conditions per patient (conditions without STOP date)
    patient_chronic_conds = defaultdict(set)
    for r in conditions:
        if not r.get("STOP", "").strip():
            patient_chronic_conds[r["PATIENT"]].add(r["DESCRIPTION"])

    # Key disease flags per patient
    patient_has_diabetes = set()
    patient_has_hypertension = set()
    patient_has_ckd = set()
    patient_has_heart_failure = set()
    patient_has_copd = set()

    for r in conditions:
        desc_lower = r["DESCRIPTION"].lower()
        pid = r["PATIENT"]
        if "diabetes" in desc_lower:
            patient_has_diabetes.add(pid)
        if "hypertension" in desc_lower or "hypertensive" in desc_lower:
            patient_has_hypertension.add(pid)
        if "chronic kidney" in desc_lower:
            patient_has_ckd.add(pid)
        if "heart failure" in desc_lower:
            patient_has_heart_failure.add(pid)
        if "chronic obstructive" in desc_lower:
            patient_has_copd.add(pid)

    # Encounters per patient
    enc_per_patient = Counter(r["PATIENT"] for r in encounters)

    # Latest HbA1c per patient
    patient_hba1c = {}
    for r in observations:
        if "a1c" in r["DESCRIPTION"].lower() and r.get("TYPE") == "numeric":
            try:
                val = float(r["VALUE"])
                dt = r["DATE"]
                pid = r["PATIENT"]
                if pid not in patient_hba1c or dt > patient_hba1c[pid][1]:
                    patient_hba1c[pid] = (val, dt)
            except (ValueError, TypeError):
                pass

    # Latest systolic BP per patient
    patient_sbp = {}
    for r in observations:
        if r["DESCRIPTION"] == "Systolic Blood Pressure" and r.get("TYPE") == "numeric":
            try:
                val = float(r["VALUE"])
                dt = r["DATE"]
                pid = r["PATIENT"]
                if pid not in patient_sbp or dt > patient_sbp[pid][1]:
                    patient_sbp[pid] = (val, dt)
            except (ValueError, TypeError):
                pass

    # Define High-Risk Label
    # A patient is HIGH-RISK if they meet >= 2 of these criteria:
    # 1. Has diabetes
    # 2. Has hypertension
    # 3. Has CKD
    # 4. Has heart failure
    # 5. Has COPD
    # 6. Has >= 3 ongoing chronic conditions
    # 7. Latest HbA1c > 7.0 (poorly controlled diabetes)
    # 8. Latest systolic BP > 140 (uncontrolled hypertension)
    # 9. Age >= 65 with >= 2 chronic conditions

    print(f"\nProposed High-Risk Label Definition:")
    print(f"  A patient is HIGH-RISK if they meet >= 2 of the following criteria:")
    print(f"  1. Has diabetes")
    print(f"  2. Has hypertension")
    print(f"  3. Has CKD")
    print(f"  4. Has heart failure")
    print(f"  5. Has COPD")
    print(f"  6. Has >= 3 ongoing chronic conditions (no STOP date)")
    print(f"  7. Latest HbA1c > 7.0")
    print(f"  8. Latest Systolic BP > 140")
    print(f"  9. Age >= 65 with >= 2 chronic conditions")

    high_risk_patients = set()
    risk_criteria_counts = defaultdict(int)

    for pid in patient_ids:
        criteria_met = 0

        if pid in patient_has_diabetes:
            criteria_met += 1
            risk_criteria_counts["diabetes"] += 1
        if pid in patient_has_hypertension:
            criteria_met += 1
            risk_criteria_counts["hypertension"] += 1
        if pid in patient_has_ckd:
            criteria_met += 1
            risk_criteria_counts["ckd"] += 1
        if pid in patient_has_heart_failure:
            criteria_met += 1
            risk_criteria_counts["heart_failure"] += 1
        if pid in patient_has_copd:
            criteria_met += 1
            risk_criteria_counts["copd"] += 1
        if len(patient_chronic_conds.get(pid, set())) >= 3:
            criteria_met += 1
            risk_criteria_counts["3+_chronic"] += 1
        if pid in patient_hba1c and patient_hba1c[pid][0] > 7.0:
            criteria_met += 1
            risk_criteria_counts["hba1c>7"] += 1
        if pid in patient_sbp and patient_sbp[pid][0] > 140:
            criteria_met += 1
            risk_criteria_counts["sbp>140"] += 1
        if patient_ages.get(pid, 0) >= 65 and len(patient_chronic_conds.get(pid, set())) >= 2:
            criteria_met += 1
            risk_criteria_counts["age65+_chronic"] += 1

        if criteria_met >= 2:
            high_risk_patients.add(pid)

    total = len(patient_ids)
    hr = len(high_risk_patients)
    lr = total - hr

    print(f"\nLabel Distribution:")
    print(f"  Total patients: {total}")
    print(f"  High-Risk: {hr} ({hr/total*100:.1f}%)")
    print(f"  Low-Risk: {lr} ({lr/total*100:.1f}%)")

    print(f"\nCriteria Triggered:")
    for crit, cnt in sorted(risk_criteria_counts.items(), key=lambda x: -x[1]):
        print(f"  {crit}: {cnt} patients")

    # If imbalanced, try threshold adjustments
    if hr / total < 0.15:
        print(f"\n  WARNING: Class imbalance detected (<15% positive). "
              f"Consider lowering threshold to >= 1 criterion.")
        # Recalculate with threshold = 1
        hr1 = 0
        for pid in patient_ids:
            criteria_met = 0
            if pid in patient_has_diabetes: criteria_met += 1
            if pid in patient_has_hypertension: criteria_met += 1
            if pid in patient_has_ckd: criteria_met += 1
            if pid in patient_has_heart_failure: criteria_met += 1
            if pid in patient_has_copd: criteria_met += 1
            if len(patient_chronic_conds.get(pid, set())) >= 3: criteria_met += 1
            if pid in patient_hba1c and patient_hba1c[pid][0] > 7.0: criteria_met += 1
            if pid in patient_sbp and patient_sbp[pid][0] > 140: criteria_met += 1
            if patient_ages.get(pid, 0) >= 65 and len(patient_chronic_conds.get(pid, set())) >= 2: criteria_met += 1
            if criteria_met >= 1: hr1 += 1
        print(f"  With threshold >= 1: {hr1} ({hr1/total*100:.1f}%)")

    elif hr / total > 0.45:
        print(f"\n  WARNING: Too many positive ({hr/total*100:.1f}%). "
              f"Consider raising threshold to >= 3 criteria.")
        hr3 = 0
        for pid in patient_ids:
            criteria_met = 0
            if pid in patient_has_diabetes: criteria_met += 1
            if pid in patient_has_hypertension: criteria_met += 1
            if pid in patient_has_ckd: criteria_met += 1
            if pid in patient_has_heart_failure: criteria_met += 1
            if pid in patient_has_copd: criteria_met += 1
            if len(patient_chronic_conds.get(pid, set())) >= 3: criteria_met += 1
            if pid in patient_hba1c and patient_hba1c[pid][0] > 7.0: criteria_met += 1
            if pid in patient_sbp and patient_sbp[pid][0] > 140: criteria_met += 1
            if patient_ages.get(pid, 0) >= 65 and len(patient_chronic_conds.get(pid, set())) >= 2: criteria_met += 1
            if criteria_met >= 3: hr3 += 1
        print(f"  With threshold >= 3: {hr3} ({hr3/total*100:.1f}%)")
    else:
        print(f"\n  Class balance looks reasonable for ML training.")


if __name__ == "__main__":
    main()
