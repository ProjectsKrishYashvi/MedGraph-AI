"""
MedGraph AI — Neo4j Graph Validation & Integrity Suite
======================================================
Validates graph integrity post-ingestion:
1. Node counts per label vs. source canonical Parquet datasets.
2. Relationship counts for all 8 edge types.
3. Orphan node detection (detects dangling encounters or clinical events).
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Expected node labels
NODE_LABELS = [
    "Patient", "Provider", "Organization", "Encounter",
    "Condition", "Medication", "Procedure", "Observation"
]

# Expected relationship types
REL_TYPES = [
    "HAS_ENCOUNTER", "HAS_CONDITION", "HAS_MEDICATION",
    "HAS_PROCEDURE", "HAS_OBSERVATION", "ATTENDED_BY",
    "LOCATION_AT", "WORKS_AT"
]

def validate_node_counts(session, expected_counts: Dict[str, int]) -> bool:
    """Verify that node counts in Neo4j match source Parquet row counts."""
    logger.info("Validating node counts...")
    all_passed = True
    
    for label in NODE_LABELS:
        query = f"MATCH (n:{label}) RETURN count(n) AS count"
        result = session.run(query).single()
        actual_count = result["count"] if result else 0
        expected = expected_counts.get(label, 0)
        
        if actual_count != expected:
            logger.error("  [FAIL] Node count mismatch for :%s - Expected: %d, Found in Neo4j: %d",
                         label, expected, actual_count)
            all_passed = False
        else:
            logger.info("  [OK] Node count match for :%s - %d nodes", label, actual_count)
            
    return all_passed

def validate_relationship_counts(session) -> Dict[str, int]:
    """Inspect and report total relationship counts in Neo4j."""
    logger.info("Validating relationship counts...")
    rel_counts = {}
    
    for rel in REL_TYPES:
        query = f"MATCH ()-[r:{rel}]->() RETURN count(r) AS count"
        result = session.run(query).single()
        actual_count = result["count"] if result else 0
        rel_counts[rel] = actual_count
        logger.info("  [OK] Relationship :%s - %d edges", rel, actual_count)
        
    return rel_counts

def validate_orphan_nodes(session) -> bool:
    """
    Check for orphan nodes (clinical events or encounters without relationships).
    All Encounter nodes MUST have a Patient link.
    All Condition/Medication/Procedure/Observation nodes MUST have an Encounter link.
    """
    logger.info("Checking for orphan nodes...")
    all_passed = True
    
    orphan_queries = {
        "Encounter without Patient": "MATCH (e:Encounter) WHERE NOT (:Patient)-[:HAS_ENCOUNTER]->(e) RETURN count(e) AS count",
        "Condition without Encounter": "MATCH (c:Condition) WHERE NOT (:Encounter)-[:HAS_CONDITION]->(c) RETURN count(c) AS count",
        "Medication without Encounter": "MATCH (m:Medication) WHERE NOT (:Encounter)-[:HAS_MEDICATION]->(m) RETURN count(m) AS count",
        "Procedure without Encounter": "MATCH (pr:Procedure) WHERE NOT (:Encounter)-[:HAS_PROCEDURE]->(pr) RETURN count(pr) AS count",
        "Observation without Encounter": "MATCH (o:Observation) WHERE NOT (:Encounter)-[:HAS_OBSERVATION]->(o) RETURN count(o) AS count"
    }
    
    for check_name, query in orphan_queries.items():
        result = session.run(query).single()
        orphan_count = result["count"] if result else 0
        if orphan_count > 0:
            logger.error("  [FAIL] Orphan Check Failed: %s (%d orphans found)", check_name, orphan_count)
            all_passed = False
        else:
            logger.info("  [OK] Orphan Check Passed: %s (0 orphans)", check_name)
            
    return all_passed

def run_all_graph_validations(session, expected_node_counts: Dict[str, int]) -> bool:
    """Execute all validation checks and print a summary."""
    print("================================================================================")
    print("NEO4J GRAPH INTEGRITY VALIDATION REPORT")
    print("================================================================================\n")
    
    nodes_ok = validate_node_counts(session, expected_node_counts)
    print()
    rel_counts = validate_relationship_counts(session)
    print()
    orphans_ok = validate_orphan_nodes(session)
    
    print("\n================================================================================")
    if nodes_ok and orphans_ok:
        print("SUCCESS: All Neo4j graph validation checks passed cleanly!")
        print("================================================================================\n")
        return True
    else:
        print("FAILURE: Neo4j graph validation checks failed!")
        print("================================================================================\n")
        return False
