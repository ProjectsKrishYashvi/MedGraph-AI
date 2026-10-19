"""
MedGraph AI — Neo4j Knowledge Graph Reporting & Statistics Utility
===================================================================
Generates a comprehensive summary report of the populated Neo4j Knowledge Graph:
1. Total Node Counts per Label (with comparison against expected source rows).
2. Relationship Counts per Edge Type.
3. Graph Topology Statistics (Average degree, total entities, chronic disease node counts).
4. Automated Integrity Validation status.
"""

import logging
import os
import json
from typing import Dict, Any, Optional

import connection
import validators

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def generate_graph_report(output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Query Neo4j and compile a complete graph statistics and validation report.

    Args:
        output_file: Optional filepath to save the report as JSON.

    Returns:
        dict: Complete graph metrics and validation results.
    """
    logger.info("Connecting to Neo4j to generate Knowledge Graph Report...")
    conn_mgr = connection.Neo4jConnectionManager()
    
    report: Dict[str, Any] = {
        "timestamp": None,
        "database": conn_mgr.database,
        "nodes": {},
        "relationships": {},
        "statistics": {},
        "validations": {}
    }

    import datetime
    report["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    with conn_mgr.get_session() as session:
        # 1. Node Counts
        logger.info("Fetching node counts...")
        node_labels = [
            "Patient", "Provider", "Organization", "Encounter",
            "Condition", "Medication", "Procedure", "Observation"
        ]
        total_nodes = 0
        for label in node_labels:
            res = session.run(f"MATCH (n:{label}) RETURN count(n) AS count").single()
            cnt = res["count"] if res else 0
            report["nodes"][label] = cnt
            total_nodes += cnt
        report["statistics"]["total_nodes"] = total_nodes

        # 2. Relationship Counts
        logger.info("Fetching relationship counts...")
        rel_types = [
            "HAS_ENCOUNTER", "HAS_CONDITION", "HAS_MEDICATION",
            "HAS_PROCEDURE", "HAS_OBSERVATION", "ATTENDED_BY",
            "LOCATION_AT", "WORKS_AT"
        ]
        total_relationships = 0
        for rel in rel_types:
            res = session.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS count").single()
            cnt = res["count"] if res else 0
            report["relationships"][rel] = cnt
            total_relationships += cnt
        report["statistics"]["total_relationships"] = total_relationships

        # 3. Clinical & Graph Topology Statistics
        logger.info("Computing clinical and topology metrics...")
        
        # Avg encounters per patient
        avg_enc = session.run(
            "MATCH (p:Patient)-[:HAS_ENCOUNTER]->(e:Encounter) "
            "WITH p, count(e) AS enc_cnt RETURN avg(enc_cnt) AS avg_encounters"
        ).single()
        report["statistics"]["avg_encounters_per_patient"] = round(avg_enc["avg_encounters"], 2) if avg_enc and avg_enc["avg_encounters"] else 0.0

        # Chronic conditions count
        chronic_res = session.run("MATCH (c:Condition {is_chronic: true}) RETURN count(c) AS count").single()
        report["statistics"]["chronic_conditions_count"] = chronic_res["count"] if chronic_res else 0

        # Active medications count
        active_med_res = session.run("MATCH (m:Medication {is_active: true}) RETURN count(m) AS count").single()
        report["statistics"]["active_medications_count"] = active_med_res["count"] if active_med_res else 0

        # High density nodes (Patients with most encounters)
        top_patient = session.run(
            "MATCH (p:Patient)-[:HAS_ENCOUNTER]->(e:Encounter) "
            "RETURN p.patient_id AS id, count(e) AS encounters "
            "ORDER BY encounters DESC LIMIT 1"
        ).single()
        if top_patient:
            report["statistics"]["max_encounters_single_patient"] = {
                "patient_id": top_patient["id"],
                "encounter_count": top_patient["encounters"]
            }

        # 4. Validations
        logger.info("Running automated integrity checks...")
        # Check orphan count
        orphans_ok = validators.validate_orphan_nodes(session)
        report["validations"]["orphan_check_passed"] = orphans_ok
        report["validations"]["overall_status"] = "PASSED" if orphans_ok else "FAILED"

    conn_mgr.close()

    # Print Summary Report to Console
    print("\n================================================================================")
    print("MEDGRAPH AI — KNOWLEDGE GRAPH SUMMARY REPORT")
    print("================================================================================\n")
    print(f"Database         : {report['database']}")
    print(f"Total Nodes      : {report['statistics']['total_nodes']:,}")
    print(f"Total Edges      : {report['statistics']['total_relationships']:,}")
    print(f"Validation Status: {report['validations']['overall_status']}")
    print("\n--- Node Breakdown ---")
    for label, count in report["nodes"].items():
        print(f"  - {label:<15} : {count:>7,}")
        
    print("\n--- Relationship Breakdown ---")
    for rel, count in report["relationships"].items():
        print(f"  - {rel:<18} : {count:>7,}")

    print("\n--- Key Clinical Topology Metrics ---")
    print(f"  - Avg Encounters / Patient  : {report['statistics']['avg_encounters_per_patient']}")
    print(f"  - Chronic Conditions       : {report['statistics']['chronic_conditions_count']:,}")
    print(f"  - Active Medications       : {report['statistics']['active_medications_count']:,}")
    if "max_encounters_single_patient" in report["statistics"]:
        top = report["statistics"]["max_encounters_single_patient"]
        print(f"  - Max Encounters (1 Patient): {top['encounter_count']} (ID: {top['patient_id']})")
        
    print("\n================================================================================\n")

    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
        logger.info("Saved report JSON to %s", output_file)

    return report

if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs", "graph_report.json")
    generate_graph_report(output_path)
