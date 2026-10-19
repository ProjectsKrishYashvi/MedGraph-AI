"""
MedGraph AI — LangGraph Shared State Definition
================================================
Defines the TypedDict that flows through every node in the workflow.
All agents read from and write to this shared state object.

Design principle: agents only write to their own output keys —
they never overwrite keys owned by another agent.
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class MedGraphState(TypedDict):
    """
    Shared state passed between all LangGraph nodes.

    Fields populated progressively as the workflow executes:
    - graph_node:       patient_data
    - prediction_node:  risk_result
    - guideline_node:   guidelines
    - report_node:      report
    """

    # Input
    patient_id: str                          # Primary key — drives all downstream lookups
    query: Optional[str]                     # Optional free-text clinical question

    # Graph Agent output — raw patient clinical data from Neo4j
    patient_data: Optional[Dict[str, Any]]

    # Prediction Agent output — XGBoost risk score + SHAP explanations
    risk_result: Optional[Dict[str, Any]]

    # Guideline Agent output — retrieved clinical guideline chunks
    guidelines: Optional[List[Dict[str, Any]]]

    # Report Agent output — final LLM-generated clinical summary
    report: Optional[str]

    # Error tracking — each agent appends to this list on failure
    errors: List[str]
