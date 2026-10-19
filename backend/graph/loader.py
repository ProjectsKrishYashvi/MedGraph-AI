"""
MedGraph AI — Knowledge Graph Loader Orchestrator
=================================================
Orchestrates loading canonical Parquet datasets produced during Phase 1 into Neo4j.

Order of operations:
1. Nodes created first (Organizations, Providers, Patients, Encounters, Conditions, Medications, Procedures, Observations).
2. Relationships created second (Encounter as central hub).
3. Graph validation suite invoked post-load.
"""

import logging
import os
import pandas as pd
from typing import Dict, Any

import connection
import queries
import batch_loader
import validators

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

def load_parquet(name: str) -> pd.DataFrame:
    """Read a canonical Parquet dataset from data/processed/."""
    file_path = os.path.join(PROCESSED_DIR, f"{name}.parquet")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Missing canonical parquet dataset: {file_path}")
    logger.info("Reading %s.parquet...", name)
    return pd.read_parquet(file_path)

def df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a pandas DataFrame to a list of dictionaries with ISO string dates."""
    # Convert datetime columns to string format for Cypher compatibility
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
    return df.to_dict(orient="records")

def load_knowledge_graph(batch_size: int = 5000) -> None:
    """Main loading function to ingest all canonical datasets into Neo4j."""
    logger.info("Initializing Graph Data Ingestion...")
    
    # 1. Read Canonical Datasets
    patients_df = load_parquet("patients")
    providers_df = load_parquet("providers")
    organizations_df = load_parquet("organizations")
    encounters_df = load_parquet("encounters")
    conditions_df = load_parquet("conditions")
    medications_df = load_parquet("medications")
    procedures_df = load_parquet("procedures")
    observations_df = load_parquet("observations")

    expected_node_counts = {
        "Patient": len(patients_df),
        "Provider": len(providers_df),
        "Organization": len(organizations_df),
        "Encounter": len(encounters_df),
        "Condition": len(conditions_df),
        "Medication": len(medications_df),
        "Procedure": len(procedures_df),
        "Observation": len(observations_df)
    }

    conn_mgr = connection.Neo4jConnectionManager()
    
    with conn_mgr.get_session() as session:
        # =====================================================================
        # PHASE A: LOAD NODES FIRST
        # =====================================================================
        logger.info("\n--- PHASE A: Loading Nodes ---")
        
        batch_loader.execute_batch_write(
            session, queries.CREATE_ORGANIZATION_NODES, 
            df_to_records(organizations_df), "Organization Nodes", batch_size
        )
        batch_loader.execute_batch_write(
            session, queries.CREATE_PROVIDER_NODES, 
            df_to_records(providers_df), "Provider Nodes", batch_size
        )
        batch_loader.execute_batch_write(
            session, queries.CREATE_PATIENT_NODES, 
            df_to_records(patients_df), "Patient Nodes", batch_size
        )
        batch_loader.execute_batch_write(
            session, queries.CREATE_ENCOUNTER_NODES, 
            df_to_records(encounters_df), "Encounter Nodes", batch_size
        )
        batch_loader.execute_batch_write(
            session, queries.CREATE_CONDITION_NODES, 
            df_to_records(conditions_df), "Condition Nodes", batch_size
        )
        batch_loader.execute_batch_write(
            session, queries.CREATE_MEDICATION_NODES, 
            df_to_records(medications_df), "Medication Nodes", batch_size
        )
        batch_loader.execute_batch_write(
            session, queries.CREATE_PROCEDURE_NODES, 
            df_to_records(procedures_df), "Procedure Nodes", batch_size
        )
        batch_loader.execute_batch_write(
            session, queries.CREATE_OBSERVATION_NODES, 
            df_to_records(observations_df), "Observation Nodes", batch_size
        )

        # =====================================================================
        # PHASE B: LOAD RELATIONSHIPS SECOND
        # =====================================================================
        logger.info("\n--- PHASE B: Loading Relationships ---")
        
        batch_loader.execute_batch_write(
            session, queries.LINK_PATIENT_ENCOUNTER, 
            df_to_records(encounters_df[['patient_id', 'encounter_id']]), "Patient -> Encounter", batch_size
        )
        batch_loader.execute_batch_write(
            session, queries.LINK_ENCOUNTER_CONDITION, 
            df_to_records(conditions_df[['encounter_id', 'condition_id']]), "Encounter -> Condition", batch_size
        )
        batch_loader.execute_batch_write(
            session, queries.LINK_ENCOUNTER_MEDICATION, 
            df_to_records(medications_df[['encounter_id', 'medication_id']]), "Encounter -> Medication", batch_size
        )
        batch_loader.execute_batch_write(
            session, queries.LINK_ENCOUNTER_PROCEDURE, 
            df_to_records(procedures_df[['encounter_id', 'procedure_id']]), "Encounter -> Procedure", batch_size
        )
        batch_loader.execute_batch_write(
            session, queries.LINK_ENCOUNTER_OBSERVATION, 
            df_to_records(observations_df[['encounter_id', 'observation_id']]), "Encounter -> Observation", batch_size
        )
        batch_loader.execute_batch_write(
            session, queries.LINK_ENCOUNTER_PROVIDER, 
            df_to_records(encounters_df[['encounter_id', 'provider_id']].dropna()), "Encounter -> Provider", batch_size
        )
        batch_loader.execute_batch_write(
            session, queries.LINK_ENCOUNTER_ORGANIZATION, 
            df_to_records(encounters_df[['encounter_id', 'organization_id']].dropna()), "Encounter -> Organization", batch_size
        )
        batch_loader.execute_batch_write(
            session, queries.LINK_PROVIDER_ORGANIZATION, 
            df_to_records(providers_df[['provider_id', 'organization_id']].dropna()), "Provider -> Organization", batch_size
        )

        # =====================================================================
        # PHASE C: RUN GRAPH VALIDATION
        # =====================================================================
        logger.info("\n--- PHASE C: Running Post-Ingestion Validation ---")
        validators.run_all_graph_validations(session, expected_node_counts)

    conn_mgr.close()
    logger.info("Graph Ingestion Pipeline Finished Successfully!")

if __name__ == "__main__":
    load_knowledge_graph()
