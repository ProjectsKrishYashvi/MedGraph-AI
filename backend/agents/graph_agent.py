"""
MedGraph AI — Graph Agent
==========================
LangGraph node that retrieves a complete patient clinical profile
from the Neo4j knowledge graph.

Queries:
- Patient demographics and metadata
- Active conditions (all diagnosed conditions)
- Current medications
- Recent encounters (last 10)
- Latest lab observations
- Total procedure count
"""

import logging
import os
import sys
from typing import Dict, Any

_AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
_GRAPH_DIR = os.path.abspath(os.path.join(_AGENTS_DIR, "..", "graph"))
for _p in [_AGENTS_DIR, _GRAPH_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from connection import get_driver
except ImportError:
    from backend.graph.connection import get_driver

try:
    from state import MedGraphState
except ImportError:
    from backend.agents.state import MedGraphState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cypher Queries
# ---------------------------------------------------------------------------

PATIENT_PROFILE_QUERY = """
MATCH (p:Patient {patient_id: $patient_id})
RETURN p {
    .patient_id,
    .age,
    .gender,
    .race,
    .ethnicity,
    .city,
    .state,
    .birth_date,
    .death_date,
    .marital_status
} AS patient
"""

CONDITIONS_QUERY = """
MATCH (p:Patient {patient_id: $patient_id})-[:HAS_ENCOUNTER]->(e:Encounter)
      -[:HAS_CONDITION]->(c:Condition)
RETURN DISTINCT c.condition_name AS condition_name,
                c.snomed_code    AS snomed_code,
                c.snomed_code    AS icd10_code,
                c.onset_date     AS onset_date,
                c.stop_date      AS stop_date
ORDER BY c.onset_date DESC
LIMIT 20
"""

MEDICATIONS_QUERY = """
MATCH (p:Patient {patient_id: $patient_id})-[:HAS_ENCOUNTER]->(e:Encounter)
      -[:HAS_MEDICATION]->(m:Medication)
WHERE m.stop_date IS NULL OR m.stop_date = ''
RETURN DISTINCT m.medication_name AS medication_name,
                m.rxnorm_code     AS rxnorm_code,
                m.start_date      AS start_date
ORDER BY m.start_date DESC
LIMIT 15
"""

RECENT_ENCOUNTERS_QUERY = """
MATCH (p:Patient {patient_id: $patient_id})-[:HAS_ENCOUNTER]->(e:Encounter)
RETURN e.encounter_id   AS encounter_id,
       e.encounter_type AS encounter_type,
       e.start_datetime AS start_datetime
ORDER BY e.start_datetime DESC
LIMIT 10
"""

LATEST_OBSERVATIONS_QUERY = """
MATCH (p:Patient {patient_id: $patient_id})-[:HAS_ENCOUNTER]->(e:Encounter)
      -[:HAS_OBSERVATION]->(o:Observation)
WITH o.observation_type AS obs_type,
     o.numeric_value    AS value,
     o.units            AS units,
     o.observation_date AS obs_date,
     ROW_NUMBER() OVER (PARTITION BY o.observation_type ORDER BY o.observation_date DESC) AS rn
WHERE rn = 1
RETURN obs_type, value, units, obs_date
ORDER BY obs_type
"""

SUMMARY_COUNTS_QUERY = """
MATCH (p:Patient {patient_id: $patient_id})-[:HAS_ENCOUNTER]->(e:Encounter)
WITH p, COUNT(DISTINCT e) AS total_encounters
OPTIONAL MATCH (p)-[:HAS_ENCOUNTER]->(:Encounter)-[:HAS_CONDITION]->(c:Condition)
WITH p, total_encounters, COUNT(DISTINCT c) AS total_conditions
OPTIONAL MATCH (p)-[:HAS_ENCOUNTER]->(:Encounter)-[:HAS_MEDICATION]->(m:Medication)
WITH p, total_encounters, total_conditions, COUNT(DISTINCT m) AS total_medications
OPTIONAL MATCH (p)-[:HAS_ENCOUNTER]->(:Encounter)-[:HAS_PROCEDURE]->(pr:Procedure)
RETURN total_encounters,
       total_conditions,
       total_medications,
       COUNT(DISTINCT pr) AS total_procedures
"""


# ---------------------------------------------------------------------------
# Graph Agent Node
# ---------------------------------------------------------------------------

def graph_node(state: MedGraphState) -> MedGraphState:
    """
    LangGraph node: retrieve patient clinical data from Neo4j.

    Populates state["patient_data"] with a structured dict containing
    demographics, conditions, medications, encounters, observations,
    and summary counts.

    Falls back gracefully with an error entry if Neo4j is unreachable.
    """
    patient_id = state["patient_id"]
    logger.info("[GraphAgent] Fetching patient: %s", patient_id)

    try:
        driver = get_driver()

        with driver.session() as session:
            # Demographics
            p_result = session.run(PATIENT_PROFILE_QUERY, patient_id=patient_id)
            patient_record = p_result.single()
            if not patient_record:
                raise ValueError(f"Patient {patient_id} not found in Neo4j.")
            patient = dict(patient_record["patient"])

            # Conditions
            conditions = [
                dict(r) for r in session.run(CONDITIONS_QUERY, patient_id=patient_id)
            ]

            # Medications
            medications = [
                dict(r) for r in session.run(MEDICATIONS_QUERY, patient_id=patient_id)
            ]

            # Recent encounters
            encounters = [
                dict(r) for r in session.run(RECENT_ENCOUNTERS_QUERY, patient_id=patient_id)
            ]

            # Latest observations
            try:
                observations = [
                    dict(r) for r in session.run(LATEST_OBSERVATIONS_QUERY, patient_id=patient_id)
                ]
            except Exception:
                # ROW_NUMBER() requires Neo4j 5.x — fallback gracefully
                observations = []

            # Summary counts
            counts_record = session.run(SUMMARY_COUNTS_QUERY, patient_id=patient_id).single()
            summary = dict(counts_record) if counts_record else {}

        patient_data = {
            "patient":      patient,
            "conditions":   conditions,
            "medications":  medications,
            "encounters":   encounters,
            "observations": observations,
            "summary":      summary,
        }

        logger.info(
            "[GraphAgent] Retrieved: %d conditions, %d medications, %d encounters",
            len(conditions), len(medications), len(encounters),
        )

        return {**state, "patient_data": patient_data}

    except Exception as exc:
        error_msg = f"GraphAgent Neo4j fallback: {exc}"
        logger.warning(error_msg)
        try:
            import pandas as pd
            features_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "features.parquet")
            )
            if os.path.exists(features_path):
                df = pd.read_parquet(features_path)
                row = df[df["patient_id"] == patient_id]
                if not row.empty:
                    r = row.iloc[0]
                    patient = {
                        "patient_id": patient_id,
                        "age": round(float(r["age"]), 1) if pd.notnull(r.get("age")) else None,
                        "gender": "F" if r.get("is_female") == 1 else "M",
                        "race": str(r.get("race", "unknown")),
                        "city": "",
                        "state": "",
                    }
                    summary = {
                        "total_encounters": int(r.get("total_encounters", 0)),
                        "total_conditions": int(r.get("total_conditions", 0)),
                        "total_medications": int(r.get("total_medications", 0)),
                        "total_procedures": int(r.get("total_procedures", 0)),
                    }
                    conds = []
                    for c_name, c_col in [
                        ("Diabetes", "has_diabetes"),
                        ("Hypertension", "has_hypertension"),
                        ("Chronic Kidney Disease", "has_ckd"),
                        ("Heart Failure", "has_heart_failure"),
                        ("COPD", "has_copd"),
                        ("Obesity", "has_obesity")
                    ]:
                        if r.get(c_col) == 1:
                            conds.append({"condition_name": c_name, "snomed_code": "", "onset_date": ""})

                    patient_data = {
                        "patient":      patient,
                        "conditions":   conds,
                        "medications":  [],
                        "encounters":   [],
                        "observations": [],
                        "summary":      summary,
                    }
                    logger.info("[GraphAgent] Recovered patient data from features.parquet fallback.")
                    return {**state, "patient_data": patient_data}
        except Exception as f_err:
            logger.error("features.parquet fallback also failed: %s", f_err)

        return {
            **state,
            "patient_data": None,
            "errors": state.get("errors", []) + [error_msg],
        }
