"""
MedGraph AI — Pydantic Request & Response Models
=================================================
All API request/response schemas in one place for clarity and reuse.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------

class SHAPContribution(BaseModel):
    feature:       str
    shap_value:    float
    direction:     str       # "increases_risk" | "decreases_risk"
    feature_value: Optional[float] = None


class GuidelineChunk(BaseModel):
    text:            str
    source:          str
    score:           float
    condition_tags:  List[str] = []


class PatientSummary(BaseModel):
    patient_id:         str
    age:                Optional[float]
    gender:             Optional[str]
    race:               Optional[str]
    city:               Optional[str]
    state:              Optional[str]
    total_encounters:   Optional[int]
    total_conditions:   Optional[int]
    total_medications:  Optional[int]
    total_procedures:   Optional[int]


class PatientListItem(BaseModel):
    patient_id:         str
    age:                Optional[float] = None
    gender:             Optional[str] = None
    race:               Optional[str] = None
    total_encounters:   Optional[int] = 0
    total_conditions:   Optional[int] = 0
    total_medications:  Optional[int] = 0
    is_high_risk:       bool = False
    has_diabetes:       bool = False
    has_hypertension:   bool = False
    has_ckd:            bool = False
    has_heart_failure:  bool = False
    has_copd:           bool = False
    has_obesity:        bool = False


class PatientListResponse(BaseModel):
    total:    int
    limit:    int
    offset:   int
    patients: List[PatientListItem]


# ---------------------------------------------------------------------------
# /predict
# ---------------------------------------------------------------------------

class PredictRequest(BaseModel):
    patient_id: str = Field(..., description="Neo4j Patient node ID")


class PredictResponse(BaseModel):
    patient_id:              str
    risk_probability:        float
    is_high_risk:            bool
    top_shap_contributions:  List[SHAPContribution]


# ---------------------------------------------------------------------------
# /insights
# ---------------------------------------------------------------------------

class InsightsRequest(BaseModel):
    patient_id: str  = Field(..., description="Neo4j Patient node ID")
    query:      str  = Field(
        default="Provide a comprehensive clinical risk summary and evidence-based management recommendations.",
        description="Clinical question to focus the AI report."
    )


class InsightsResponse(BaseModel):
    patient_id:   str
    patient:      Optional[PatientSummary]
    risk_result:  Optional[PredictResponse]
    guidelines:   List[GuidelineChunk]
    report:       str
    errors:       List[str] = []


# ---------------------------------------------------------------------------
# /population
# ---------------------------------------------------------------------------

class PopulationStatsResponse(BaseModel):
    total_patients:        int
    high_risk_count:       int
    high_risk_percentage:  float
    condition_prevalence:  Dict[str, int]
    avg_age:               Optional[float]
    avg_encounters:        Optional[float]
