"""
MedGraph AI — Neo4j Graph Schema Initialization
================================================
Responsibility: Define the graph schema (constraints and indexes).
This module does NOT ingest any data.

Run this once before any data loading operation. It is idempotent —
running it multiple times on an existing database is safe because
all CREATE statements use IF NOT EXISTS.

Architecture Reference:
  DATABASE.md   — Graph relationships and data integrity rules
  ARCHITECTURE.md — Neo4j as primary analytical datastore
  CANONICAL_SCHEMA.md — Canonical entities and their primary keys
"""

import logging
import os
from typing import Optional

from neo4j import GraphDatabase, Driver

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Uniqueness Constraints
# ---------------------------------------------------------------------------
# A uniqueness constraint enforces PK integrity AND implicitly creates a
# B-tree index on the constrained property, making MERGE lookups O(1).
# Every node type that will be created via MERGE needs a constraint on its ID.
# ---------------------------------------------------------------------------
UNIQUENESS_CONSTRAINTS: list[tuple[str, str, str]] = [
    # (constraint_name, label, property)
    ("unique_patient_id",       "Patient",       "patient_id"),
    ("unique_encounter_id",     "Encounter",     "encounter_id"),
    ("unique_condition_id",     "Condition",     "condition_id"),
    ("unique_medication_id",    "Medication",    "medication_id"),
    ("unique_observation_id",   "Observation",   "observation_id"),
    ("unique_procedure_id",     "Procedure",     "procedure_id"),
    ("unique_provider_id",      "Provider",      "provider_id"),
    ("unique_organization_id",  "Organization",  "organization_id"),
]

# ---------------------------------------------------------------------------
# Standard (B-Tree) Indexes
# ---------------------------------------------------------------------------
# These indexes accelerate property lookups that are NOT covered by
# uniqueness constraints. They support the Graph Agent's Cypher queries
# for patient cohort analysis, temporal filtering, and clinical lookups.
# ---------------------------------------------------------------------------
STANDARD_INDEXES: list[tuple[str, str, str]] = [
    # (index_name, label, property)

    # Patient demographic analytics
    ("idx_patient_gender",          "Patient",      "gender"),
    ("idx_patient_race",            "Patient",      "race"),
    ("idx_patient_is_deceased",     "Patient",      "is_deceased"),

    # Encounter temporal and type filtering
    # (e.g., "all inpatient encounters in 2021", "encounters after date X")
    ("idx_encounter_type",          "Encounter",    "encounter_type"),
    ("idx_encounter_start",         "Encounter",    "start_datetime"),

    # Clinical event property lookups
    # (e.g., "all patients with SNOMED code X", "all HbA1c observations")
    ("idx_condition_snomed",        "Condition",    "snomed_code"),
    ("idx_medication_rxnorm",       "Medication",   "rxnorm_code"),
    ("idx_observation_name",        "Observation",  "observation_name"),
    ("idx_observation_date",        "Observation",  "observation_date"),

    # Provider specialty filtering
    # (e.g., "encounters attended by a cardiologist")
    ("idx_provider_specialty",      "Provider",     "specialty"),
]

# ---------------------------------------------------------------------------
# Full-Text Indexes
# ---------------------------------------------------------------------------
# Standard B-tree indexes only accelerate equality and range comparisons.
# The Graph Agent will use CONTAINS-style queries on clinical descriptions
# (e.g., WHERE c.condition_name CONTAINS 'diabetes').
# Full-text indexes (backed by Apache Lucene) handle these efficiently.
# ---------------------------------------------------------------------------
FULLTEXT_INDEXES: list[tuple[str, list[str], list[str]]] = [
    # (index_name, labels, properties)
    ("ft_condition_name",    ["Condition"],   ["condition_name"]),
    ("ft_medication_name",   ["Medication"],  ["medication_name"]),
    ("ft_procedure_name",    ["Procedure"],   ["procedure_name"]),
    ("ft_organization_name", ["Organization"],["organization_name"]),
]


def _create_uniqueness_constraints(driver: Driver) -> None:
    """Create uniqueness constraints for all primary key properties."""
    with driver.session() as session:
        for name, label, prop in UNIQUENESS_CONSTRAINTS:
            cypher = (
                f"CREATE CONSTRAINT {name} IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
            )
            session.run(cypher)
            logger.info("Constraint applied: %s (%s.%s)", name, label, prop)


def _create_standard_indexes(driver: Driver) -> None:
    """Create standard B-tree indexes for frequently queried properties."""
    with driver.session() as session:
        for name, label, prop in STANDARD_INDEXES:
            cypher = (
                f"CREATE INDEX {name} IF NOT EXISTS "
                f"FOR (n:{label}) ON (n.{prop})"
            )
            session.run(cypher)
            logger.info("Index applied: %s (%s.%s)", name, label, prop)


def _create_fulltext_indexes(driver: Driver) -> None:
    """
    Create full-text indexes for clinical description searches.

    Full-text indexes in Neo4j use a different syntax from standard indexes
    and do not support IF NOT EXISTS before Neo4j 5.14.
    We check for existence explicitly to remain idempotent.
    """
    with driver.session() as session:
        # Fetch existing full-text index names
        existing = {
            record["name"]
            for record in session.run("SHOW FULLTEXT INDEXES YIELD name")
        }

        for name, labels, props in FULLTEXT_INDEXES:
            if name in existing:
                logger.info("Full-text index already exists, skipping: %s", name)
                continue
            labels_str = "|".join(labels)
            props_str = ", ".join([f"n.{p}" for p in props])
            cypher = (
                f"CREATE FULLTEXT INDEX {name} "
                f"FOR (n:{labels_str}) ON EACH [{props_str}]"
            )
            session.run(cypher)
            logger.info("Full-text index applied: %s", name)


def initialize_schema(
    uri: str,
    username: str,
    password: str,
    database: str = "neo4j",
) -> None:
    """
    Initialize the MedGraph AI Neo4j graph schema.

    Creates all uniqueness constraints, standard indexes, and full-text
    indexes required by the graph data model. Safe to run multiple times —
    all operations are idempotent.

    Args:
        uri:      Neo4j Bolt URI (e.g., "bolt://localhost:7687")
        username: Neo4j username
        password: Neo4j password
        database: Target database name (default: "neo4j")

    Raises:
        neo4j.exceptions.ServiceUnavailable: if Neo4j is not reachable.
        neo4j.exceptions.AuthError: if credentials are incorrect.
    """
    logger.info("Connecting to Neo4j at %s (database: %s)", uri, database)

    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        driver.verify_connectivity()
        logger.info("Connection verified.")

        logger.info("Creating uniqueness constraints...")
        _create_uniqueness_constraints(driver)

        logger.info("Creating standard indexes...")
        _create_standard_indexes(driver)

        logger.info("Creating full-text indexes...")
        _create_fulltext_indexes(driver)

    logger.info("Schema initialization complete.")


def get_schema_summary() -> dict:
    """
    Return a summary of the schema definition for introspection.

    This is a pure-Python utility — it does NOT connect to Neo4j.
    Useful for documentation, debugging, and testing.
    """
    return {
        "uniqueness_constraints": [
            {"name": n, "label": l, "property": p}
            for n, l, p in UNIQUENESS_CONSTRAINTS
        ],
        "standard_indexes": [
            {"name": n, "label": l, "property": p}
            for n, l, p in STANDARD_INDEXES
        ],
        "fulltext_indexes": [
            {"name": n, "labels": ls, "properties": ps}
            for n, ls, ps in FULLTEXT_INDEXES
        ],
    }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    # Connection parameters — can be overridden via environment variables
    NEO4J_URI      = os.getenv("NEO4J_URI",     "bolt://localhost:7687")
    NEO4J_USER     = os.getenv("NEO4J_USER",    "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD","medgraph123")
    NEO4J_DATABASE = os.getenv("NEO4J_DATABASE","neo4j")

    initialize_schema(
        uri=NEO4J_URI,
        username=NEO4J_USER,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
    )
