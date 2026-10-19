"""
MedGraph AI — LangGraph Workflow Orchestration
================================================
Assembles the four agents into a sequential LangGraph StateGraph.

Pipeline:
  START → graph_node → prediction_node → guideline_node → report_node → END

Design decisions:
- Linear pipeline (no conditional routing): all agents always run.
  Agents handle missing upstream data gracefully via error entries.
- No retry logic at the workflow level — agents fail fast and log errors.
- The workflow can be invoked directly or through the FastAPI endpoint.
"""

import logging
import os
import sys

from langgraph.graph import StateGraph, START, END

# Resolve paths
_AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _AGENTS_DIR not in sys.path:
    sys.path.insert(0, _AGENTS_DIR)

try:
    from state import MedGraphState
    from graph_agent import graph_node
    from prediction_agent import prediction_node
    from guideline_agent import guideline_node
    from report_agent import report_node
except ImportError:
    from backend.agents.state import MedGraphState
    from backend.agents.graph_agent import graph_node
    from backend.agents.prediction_agent import prediction_node
    from backend.agents.guideline_agent import guideline_node
    from backend.agents.report_agent import report_node

logger = logging.getLogger(__name__)


def build_workflow() -> StateGraph:
    """
    Construct and compile the MedGraph AI LangGraph workflow.

    Returns:
        Compiled StateGraph ready for invocation.
    """
    graph = StateGraph(MedGraphState)

    # Register nodes
    graph.add_node("graph_node",      graph_node)
    graph.add_node("prediction_node", prediction_node)
    graph.add_node("guideline_node",  guideline_node)
    graph.add_node("report_node",     report_node)

    # Define linear execution order
    graph.add_edge(START,             "graph_node")
    graph.add_edge("graph_node",      "prediction_node")
    graph.add_edge("prediction_node", "guideline_node")
    graph.add_edge("guideline_node",  "report_node")
    graph.add_edge("report_node",     END)

    return graph.compile()


# Module-level compiled workflow singleton
_workflow = None


def get_workflow():
    """Return the compiled workflow singleton."""
    global _workflow
    if _workflow is None:
        _workflow = build_workflow()
        logger.info("MedGraph AI LangGraph workflow compiled.")
    return _workflow


def run_workflow(patient_id: str, query: str = "") -> MedGraphState:
    """
    Run the full MedGraph AI workflow for a given patient.

    Args:
        patient_id: Neo4j Patient node primary key.
        query:      Optional clinical question to focus the report.

    Returns:
        Final MedGraphState with all agent outputs populated.
    """
    logger.info("=== MedGraph AI Workflow: patient_id=%s ===", patient_id)

    initial_state: MedGraphState = {
        "patient_id":   patient_id,
        "query":        query,
        "patient_data": None,
        "risk_result":  None,
        "guidelines":   None,
        "report":       None,
        "errors":       [],
    }

    workflow = get_workflow()
    final_state = workflow.invoke(initial_state)

    if final_state.get("errors"):
        logger.warning("Workflow completed with errors: %s", final_state["errors"])
    else:
        logger.info("Workflow completed successfully for patient: %s", patient_id)

    return final_state


# ---------------------------------------------------------------------------
# CLI entry point for testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    # Use a known patient ID from the dataset — override via command line arg
    test_patient_id = sys.argv[1] if len(sys.argv) > 1 else None

    if not test_patient_id:
        print("Usage: python workflow.py <patient_id>")
        print("\nFetch a sample patient ID from Neo4j:")
        print("  MATCH (p:Patient) RETURN p.patient_id LIMIT 1")
        sys.exit(1)

    result = run_workflow(
        patient_id=test_patient_id,
        query="What are the key clinical risks and management priorities for this patient?",
    )

    print("\n" + "=" * 70)
    print("MEDGRAPH AI — WORKFLOW OUTPUT")
    print("=" * 70)

    print("\n--- PATIENT DATA ---")
    if result.get("patient_data"):
        p = result["patient_data"]["patient"]
        print(f"  Age: {p.get('age')} | Gender: {p.get('gender')} | Race: {p.get('race')}")
        print(f"  Conditions: {len(result['patient_data'].get('conditions', []))}")
        print(f"  Medications: {len(result['patient_data'].get('medications', []))}")

    print("\n--- RISK RESULT ---")
    if result.get("risk_result"):
        r = result["risk_result"]
        print(f"  Probability: {r['risk_probability']:.4f} | High-Risk: {r['is_high_risk']}")
        print("  Top SHAP Contributors:")
        for c in r.get("top_shap_contributions", []):
            print(f"    {c['feature']}: {c['shap_value']:+.3f} [{c['direction']}]")

    print("\n--- GUIDELINES ---")
    for i, g in enumerate(result.get("guidelines", [])[:2], 1):
        print(f"  [{i}] {g['source']} (score: {g['score']})")

    print("\n--- CLINICAL REPORT ---")
    print(result.get("report", "[No report generated]"))

    if result.get("errors"):
        print("\n--- ERRORS ---")
        for err in result["errors"]:
            print(f"  ⚠ {err}")

    print("=" * 70)
