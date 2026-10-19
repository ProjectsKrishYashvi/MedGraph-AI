"""
MedGraph AI — Cypher Query Registry
====================================
Centralized registry of parameterized Cypher queries used during graph ingestion
and graph analytics queries.

Uses UNWIND pattern for high-performance batched ingestion.
"""

# =============================================================================
# NODE INGESTION QUERIES (Batched UNWIND)
# =============================================================================

CREATE_PATIENT_NODES = """
UNWIND $batch AS row
MERGE (p:Patient {patient_id: row.patient_id})
SET p.birth_date = row.birth_date,
    p.death_date = row.death_date,
    p.gender = row.gender,
    p.race = row.race,
    p.ethnicity = row.ethnicity,
    p.marital_status = row.marital_status,
    p.city = row.city,
    p.state = row.state,
    p.age = row.age
"""

CREATE_PROVIDER_NODES = """
UNWIND $batch AS row
MERGE (pr:Provider {provider_id: row.provider_id})
SET pr.organization_id = row.organization_id,
    pr.provider_name = row.provider_name,
    pr.gender = row.gender,
    pr.specialty = row.specialty
"""

CREATE_ORGANIZATION_NODES = """
UNWIND $batch AS row
MERGE (o:Organization {organization_id: row.organization_id})
SET o.organization_name = row.organization_name,
    o.city = row.city,
    o.state = row.state
"""

CREATE_ENCOUNTER_NODES = """
UNWIND $batch AS row
MERGE (e:Encounter {encounter_id: row.encounter_id})
SET e.patient_id = row.patient_id,
    e.provider_id = row.provider_id,
    e.organization_id = row.organization_id,
    e.encounter_type = row.encounter_type,
    e.start_datetime = row.start_datetime,
    e.end_datetime = row.end_datetime
"""

CREATE_CONDITION_NODES = """
UNWIND $batch AS row
MERGE (c:Condition {condition_id: row.condition_id})
SET c.encounter_id = row.encounter_id,
    c.patient_id = row.patient_id,
    c.snomed_code = row.snomed_code,
    c.condition_name = row.condition_name,
    c.onset_date = row.onset_date,
    c.stop_date = row.stop_date,
    c.is_chronic = (row.stop_date IS NULL)
"""

CREATE_MEDICATION_NODES = """
UNWIND $batch AS row
MERGE (m:Medication {medication_id: row.medication_id})
SET m.encounter_id = row.encounter_id,
    m.patient_id = row.patient_id,
    m.rxnorm_code = row.rxnorm_code,
    m.medication_name = row.medication_name,
    m.start_date = row.start_date,
    m.stop_date = row.stop_date,
    m.is_active = (row.stop_date IS NULL)
"""

CREATE_PROCEDURE_NODES = """
UNWIND $batch AS row
MERGE (pr:Procedure {procedure_id: row.procedure_id})
SET pr.encounter_id = row.encounter_id,
    pr.patient_id = row.patient_id,
    pr.procedure_name = row.procedure_name,
    pr.procedure_date = row.procedure_date
"""

CREATE_OBSERVATION_NODES = """
UNWIND $batch AS row
MERGE (o:Observation {observation_id: row.observation_id})
SET o.encounter_id = row.encounter_id,
    o.patient_id = row.patient_id,
    o.observation_name = row.observation_name,
    o.observation_value = row.observation_value,
    o.observation_unit = row.observation_unit,
    o.observation_date = row.observation_date
"""

# =============================================================================
# RELATIONSHIP INGESTION QUERIES (Batched UNWIND)
# =============================================================================
# Architecture: Encounter is the central hub.
# (Patient)-[:HAS_ENCOUNTER]->(Encounter)
# (Encounter)-[:HAS_CONDITION]->(Condition)
# (Encounter)-[:HAS_MEDICATION]->(Medication)
# (Encounter)-[:HAS_PROCEDURE]->(Procedure)
# (Encounter)-[:HAS_OBSERVATION]->(Observation)
# (Encounter)-[:ATTENDED_BY]->(Provider)
# (Encounter)-[:LOCATION_AT]->(Organization)
# (Provider)-[:WORKS_AT]->(Organization)
# =============================================================================

LINK_PATIENT_ENCOUNTER = """
UNWIND $batch AS row
MATCH (p:Patient {patient_id: row.patient_id})
MATCH (e:Encounter {encounter_id: row.encounter_id})
MERGE (p)-[:HAS_ENCOUNTER]->(e)
"""

LINK_ENCOUNTER_CONDITION = """
UNWIND $batch AS row
MATCH (e:Encounter {encounter_id: row.encounter_id})
MATCH (c:Condition {condition_id: row.condition_id})
MERGE (e)-[:HAS_CONDITION]->(c)
"""

LINK_ENCOUNTER_MEDICATION = """
UNWIND $batch AS row
MATCH (e:Encounter {encounter_id: row.encounter_id})
MATCH (m:Medication {medication_id: row.medication_id})
MERGE (e)-[:HAS_MEDICATION]->(m)
"""

LINK_ENCOUNTER_PROCEDURE = """
UNWIND $batch AS row
MATCH (e:Encounter {encounter_id: row.encounter_id})
MATCH (p:Procedure {procedure_id: row.procedure_id})
MERGE (e)-[:HAS_PROCEDURE]->(p)
"""

LINK_ENCOUNTER_OBSERVATION = """
UNWIND $batch AS row
MATCH (e:Encounter {encounter_id: row.encounter_id})
MATCH (o:Observation {observation_id: row.observation_id})
MERGE (e)-[:HAS_OBSERVATION]->(o)
"""

LINK_ENCOUNTER_PROVIDER = """
UNWIND $batch AS row
MATCH (e:Encounter {encounter_id: row.encounter_id})
MATCH (pr:Provider {provider_id: row.provider_id})
MERGE (e)-[:ATTENDED_BY]->(pr)
"""

LINK_ENCOUNTER_ORGANIZATION = """
UNWIND $batch AS row
MATCH (e:Encounter {encounter_id: row.encounter_id})
MATCH (o:Organization {organization_id: row.organization_id})
MERGE (e)-[:LOCATION_AT]->(o)
"""

LINK_PROVIDER_ORGANIZATION = """
UNWIND $batch AS row
MATCH (pr:Provider {provider_id: row.provider_id})
MATCH (o:Organization {organization_id: row.organization_id})
MERGE (pr)-[:WORKS_AT]->(o)
"""
