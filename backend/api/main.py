"""
MedGraph AI — FastAPI Application
===================================
Production-quality REST API exposing the MedGraph AI backend.

Endpoints:
  GET  /                          — API info
  GET  /health                    — health check (DB + model status)
  GET  /patients/{patient_id}     — patient profile from Neo4j
  POST /predict                   — XGBoost risk prediction
  POST /insights                  — full LangGraph workflow (predict + guidelines + report)
  GET  /population/stats          — population-level analytics from features.parquet

Run with:
  uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
import os
import sys
import time
from typing import Optional, List, Dict, Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# Resolve paths
_API_DIR     = os.path.dirname(os.path.abspath(__file__))          # backend/api/
_BACKEND_DIR = os.path.dirname(_API_DIR)                            # backend/
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)                       # project root

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_PROJECT_ROOT, ".env"), override=False)
except ImportError:
    pass

# Ensure all sub-packages are importable regardless of how uvicorn loads the module
for _p in [_PROJECT_ROOT, _API_DIR, _BACKEND_DIR,
           os.path.join(_BACKEND_DIR, "ml"),
           os.path.join(_BACKEND_DIR, "graph"),
           os.path.join(_BACKEND_DIR, "agents"),
           os.path.join(_BACKEND_DIR, "rag")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from models import (
        PredictRequest, PredictResponse,
        InsightsRequest, InsightsResponse,
        PatientSummary, PatientListItem, PatientListResponse,
        GuidelineChunk, SHAPContribution,
        PopulationStatsResponse,
    )
except ImportError:
    from backend.api.models import (
        PredictRequest, PredictResponse,
        InsightsRequest, InsightsResponse,
        PatientSummary, PatientListItem, PatientListResponse,
        GuidelineChunk, SHAPContribution,
        PopulationStatsResponse,
    )

try:
    import predict as ml_predict
except ImportError:
    from backend.ml import predict as ml_predict

try:
    from workflow import run_workflow
except ImportError:
    from backend.agents.workflow import run_workflow

try:
    from connection import get_driver
except ImportError:
    from backend.graph.connection import get_driver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="MedGraph AI",
    description=(
        "Clinical analytics API combining Neo4j knowledge graph, "
        "XGBoost readmission risk prediction, SHAP explainability, "
        "and clinical guideline RAG retrieval."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """Pre-warm ML model and RAG retriever on startup to avoid cold-start latency."""
    logger.info("MedGraph AI starting up — pre-warming ML pipeline...")
    try:
        ml_predict.load_pipeline()
        logger.info("XGBoost pipeline loaded.")
    except Exception as exc:
        logger.warning("XGBoost pipeline not available: %s", exc)

    try:
        from retriever import get_retriever
        get_retriever()._get_client()   # Connect to Qdrant
        logger.info("Qdrant client connected.")
    except Exception as exc:
        logger.warning("Qdrant not available: %s", exc)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["info"])
def root():
    return {
        "service": "MedGraph AI",
        "version": "1.0.0",
        "description": "Clinical analytics API — Graph + ML + RAG",
        "docs": "/docs",
    }


@app.get("/health", tags=["info"])
def health_check():
    """Check availability of all backend components."""
    status = {
        "api":    "ok",
        "neo4j":  "unknown",
        "model":  "unknown",
        "qdrant": "unknown",
    }

    # Neo4j
    try:
        driver = get_driver()
        with driver.session() as sess:
            sess.run("RETURN 1")
        status["neo4j"] = "ok"
    except Exception as exc:
        status["neo4j"] = f"error: {exc}"

    # XGBoost model
    try:
        ml_predict.load_pipeline()
        status["model"] = "ok"
    except Exception as exc:
        status["model"] = f"error: {exc}"

    # Qdrant
    try:
        from retriever import get_retriever
        client = get_retriever()._get_client()
        client.get_collections()
        status["qdrant"] = "ok"
    except Exception as exc:
        status["qdrant"] = f"error: {exc}"

    overall = "healthy" if all(v == "ok" for v in status.values()) else "degraded"
    return {"status": overall, "components": status}


@app.get("/patients", response_model=PatientListResponse, tags=["patients"])
def list_patients(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    is_high_risk: Optional[bool] = None,
    condition: Optional[str] = None,
):
    """
    Search and filter patients from the pre-built feature store.
    Supports filtering by risk classification and specific chronic conditions.
    """
    features_path = os.path.join(
        _BACKEND_DIR, "..", "data", "processed", "features.parquet"
    )
    if not os.path.exists(features_path):
        raise HTTPException(
            status_code=503,
            detail="Feature store not available — run the ETL pipeline first."
        )

    try:
        df = pd.read_parquet(features_path)

        if search:
            s_clean = search.strip().lower()
            df = df[df["patient_id"].str.lower().str.contains(s_clean, na=False)]

        if is_high_risk is not None:
            col = "is_high_risk" if "is_high_risk" in df.columns else "high_risk"
            if col in df.columns:
                target_val = 1 if is_high_risk else 0
                df = df[df[col] == target_val]

        if condition:
            cond_col = f"has_{condition.lower()}"
            if cond_col in df.columns:
                df = df[df[cond_col] == 1]

        total = len(df)
        subset = df.iloc[offset : offset + limit]

        items = []
        for _, row in subset.iterrows():
            items.append(
                PatientListItem(
                    patient_id=str(row["patient_id"]),
                    age=round(float(row["age"]), 1) if pd.notnull(row.get("age")) else None,
                    gender="Female" if row.get("is_female") == 1 else "Male",
                    race=str(row.get("race", "unknown")),
                    total_encounters=int(row["total_encounters"]) if pd.notnull(row.get("total_encounters")) else 0,
                    total_conditions=int(row["total_conditions"]) if pd.notnull(row.get("total_conditions")) else 0,
                    total_medications=int(row["total_medications"]) if pd.notnull(row.get("total_medications")) else 0,
                    is_high_risk=bool(row.get("is_high_risk", 0) == 1),
                    has_diabetes=bool(row.get("has_diabetes", 0) == 1),
                    has_hypertension=bool(row.get("has_hypertension", 0) == 1),
                    has_ckd=bool(row.get("has_ckd", 0) == 1),
                    has_heart_failure=bool(row.get("has_heart_failure", 0) == 1),
                    has_copd=bool(row.get("has_copd", 0) == 1),
                    has_obesity=bool(row.get("has_obesity", 0) == 1),
                )
            )

        return PatientListResponse(total=total, limit=limit, offset=offset, patients=items)
    except Exception as exc:
        logger.error("list_patients error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/patients/{patient_id}", tags=["patients"])
def get_patient(patient_id: str):
    """
    Retrieve a patient's clinical profile from the Neo4j graph.
    Returns demographics, conditions, medications, encounters, and lab observations.
    """
    try:
        driver = get_driver()
        with driver.session() as session:
            # Demographics
            result = session.run(
                "MATCH (p:Patient {patient_id: $pid}) RETURN p", pid=patient_id
            )
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found.")
            patient = dict(record["p"])

            # Conditions
            conds = [
                dict(r) for r in session.run("""
                    MATCH (p:Patient {patient_id: $pid})-[:HAS_ENCOUNTER]->(e:Encounter)
                          -[:HAS_CONDITION]->(c:Condition)
                    RETURN DISTINCT c.condition_name AS name, c.onset_date AS onset_date,
                           c.stop_date AS stop_date, c.snomed_code AS snomed_code,
                           c.snomed_code AS icd10_code
                    ORDER BY c.onset_date DESC LIMIT 20
                """, pid=patient_id)
            ]

            # Medications
            meds = [
                dict(r) for r in session.run("""
                    MATCH (p:Patient {patient_id: $pid})-[:HAS_ENCOUNTER]->(e:Encounter)
                          -[:HAS_MEDICATION]->(m:Medication)
                    WHERE m.stop_date IS NULL OR m.stop_date = ''
                    RETURN DISTINCT m.medication_name AS name, m.start_date AS start_date,
                           m.rxnorm_code AS rxnorm_code
                    ORDER BY m.start_date DESC LIMIT 15
                """, pid=patient_id)
            ]

        return {
            "patient_id": patient_id,
            "demographics": patient,
            "conditions": conds,
            "medications": meds,
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_patient error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/predict", response_model=PredictResponse, tags=["predictions"])
def predict_risk(request: PredictRequest):
    """
    Run XGBoost readmission risk prediction for a patient.

    Retrieves the patient's pre-computed feature vector from features.parquet
    and returns risk probability + top SHAP contributors.
    """
    patient_id = request.patient_id
    try:
        # Load features for this specific patient
        features_path = os.path.join(
            _BACKEND_DIR, "..", "data", "processed", "features.parquet"
        )
        if not os.path.exists(features_path):
            raise HTTPException(
                status_code=503,
                detail="Feature store not available — run the ETL pipeline first."
            )

        df = pd.read_parquet(features_path)
        patient_row = df[df["patient_id"] == patient_id]

        if patient_row.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Patient {patient_id} not found in feature store."
            )

        # Convert to feature dict (exclude non-feature and target columns)
        exclude_cols = {"patient_id", "label", "high_risk", "is_high_risk", "risk_criteria_met"}
        feature_vector = patient_row.drop(
            columns=[c for c in exclude_cols if c in patient_row.columns]
        ).iloc[0].to_dict()

        result = ml_predict.predict_patient_risk(feature_vector, top_n=5)

        return PredictResponse(
            patient_id=patient_id,
            risk_probability=result["risk_probability"],
            is_high_risk=result["is_high_risk"],
            top_shap_contributions=[
                SHAPContribution(**c) for c in result["top_shap_contributions"]
            ],
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("predict_risk error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/insights", response_model=InsightsResponse, tags=["insights"])
def get_insights(request: InsightsRequest):
    """
    Run the full MedGraph AI LangGraph workflow for a patient.

    Pipeline: Graph retrieval → Risk prediction → Guideline RAG → LLM report.
    Returns all intermediate outputs + the final clinical report.

    Requires GEMINI_API_KEY environment variable for report generation.
    """
    t_start = time.time()
    try:
        final_state = run_workflow(
            patient_id=request.patient_id,
            query=request.query,
        )

        # Build patient summary
        patient_summary = None
        pd_data = final_state.get("patient_data")
        if pd_data:
            p = pd_data.get("patient", {})
            s = pd_data.get("summary", {})
            patient_summary = PatientSummary(
                patient_id=request.patient_id,
                age=p.get("age"),
                gender=p.get("gender"),
                race=p.get("race"),
                city=p.get("city"),
                state=p.get("state"),
                total_encounters=s.get("total_encounters"),
                total_conditions=s.get("total_conditions"),
                total_medications=s.get("total_medications"),
                total_procedures=s.get("total_procedures"),
            )

        # Build risk result
        risk_response = None
        rr = final_state.get("risk_result")
        if rr:
            risk_response = PredictResponse(
                patient_id=request.patient_id,
                risk_probability=rr["risk_probability"],
                is_high_risk=rr["is_high_risk"],
                top_shap_contributions=[
                    SHAPContribution(**c) for c in rr.get("top_shap_contributions", [])
                ],
            )

        # Guideline chunks
        guidelines = [
            GuidelineChunk(
                text=g["text"],
                source=g["source"],
                score=g["score"],
                condition_tags=g.get("condition_tags", []),
            )
            for g in (final_state.get("guidelines") or [])
        ]

        elapsed = time.time() - t_start
        logger.info(
            "Insights workflow for %s completed in %.2fs", request.patient_id, elapsed
        )

        return InsightsResponse(
            patient_id=request.patient_id,
            patient=patient_summary,
            risk_result=risk_response,
            guidelines=guidelines,
            report=final_state.get("report", "[No report generated]"),
            errors=final_state.get("errors", []),
        )

    except Exception as exc:
        logger.error("get_insights error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/population/stats", response_model=PopulationStatsResponse, tags=["population"])
def population_stats():
    """
    Population-level analytics computed from the pre-built feature store.

    Returns high-risk count, condition prevalence, and demographic averages.
    """
    features_path = os.path.join(
        _BACKEND_DIR, "..", "data", "processed", "features.parquet"
    )
    if not os.path.exists(features_path):
        raise HTTPException(
            status_code=503,
            detail="Feature store not available — run the ETL pipeline first."
        )

    try:
        df = pd.read_parquet(features_path)

        total = len(df)
        label_col = "is_high_risk" if "is_high_risk" in df.columns else ("high_risk" if "high_risk" in df.columns else "label")
        high_risk = int(df[label_col].sum()) if label_col in df.columns else 0

        condition_cols = {
            "has_diabetes":      "Diabetes",
            "has_hypertension":  "Hypertension",
            "has_ckd":           "Chronic Kidney Disease",
            "has_heart_failure": "Heart Failure",
            "has_copd":          "COPD",
            "has_obesity":       "Obesity",
        }
        condition_prevalence = {
            label: int(df[col].sum())
            for col, label in condition_cols.items()
            if col in df.columns
        }

        avg_age = round(float(df["age"].mean()), 1) if "age" in df.columns else None
        avg_enc = (
            round(float(df["total_encounters"].mean()), 1)
            if "total_encounters" in df.columns else None
        )

        return PopulationStatsResponse(
            total_patients=total,
            high_risk_count=high_risk,
            high_risk_percentage=round(high_risk / total * 100, 2) if total else 0.0,
            condition_prevalence=condition_prevalence,
            avg_age=avg_age,
            avg_encounters=avg_enc,
        )

    except Exception as exc:
        logger.error("population_stats error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
