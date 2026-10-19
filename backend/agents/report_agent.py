"""
MedGraph AI — Report Agent
============================
LangGraph node that synthesizes all upstream data into a structured
clinical insights report using the Gemini REST API.

Design principle: the LLM is the LAST step — it only does natural language
generation. All reasoning (graph retrieval, risk prediction, guideline search)
has already been performed by upstream agents.

API: Gemini 1.5 Flash via direct REST call (no Google SDK required).
Set GEMINI_API_KEY environment variable before running.
"""

import json
import logging
import os
from typing import Dict, Any, List

import sys
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _AGENTS_DIR not in sys.path:
    sys.path.insert(0, _AGENTS_DIR)

try:
    from state import MedGraphState
except ImportError:
    from backend.agents.state import MedGraphState

logger = logging.getLogger(__name__)

GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-flash-latest",
    "gemini-3.5-flash",
]


def _build_prompt(
    patient_data: Dict[str, Any],
    risk_result: Dict[str, Any],
    guidelines: List[Dict],
    query: str,
) -> str:
    """
    Construct a structured clinical prompt combining all upstream evidence.
    """
    patient   = patient_data.get("patient", {})
    conditions = patient_data.get("conditions", [])
    medications = patient_data.get("medications", [])
    summary   = patient_data.get("summary", {})

    # Format conditions
    cond_list = "\n".join(
        f"  - {c.get('condition_name', 'Unknown')} (onset: {c.get('onset_date', 'N/A')})"
        for c in conditions[:10]
    ) or "  None recorded."

    # Format medications
    med_list = "\n".join(
        f"  - {m.get('medication_name', 'Unknown')}"
        for m in medications[:10]
    ) or "  None recorded."

    # Format SHAP contributors
    shap_text = ""
    if risk_result and risk_result.get("top_shap_contributions"):
        shap_lines = []
        for item in risk_result["top_shap_contributions"]:
            direction = "increases risk" if item["direction"] == "increases_risk" else "reduces risk"
            val = f"{item['feature_value']}" if item.get("feature_value") is not None else "N/A"
            shap_lines.append(
                f"  - {item['feature']} (value: {val}) -> {direction} (SHAP impact: {abs(item['shap_value']):.3f})"
            )
        shap_text = "\n".join(shap_lines)
    else:
        shap_text = "  Not available."

    # Format guidelines
    guideline_text = ""
    if guidelines:
        gl_parts = []
        for i, g in enumerate(guidelines[:3], start=1):
            gl_parts.append(
                f"[{i}] Guideline Source: {g.get('source', 'Clinical Guideline')} (relevance score: {g.get('score', 0):.3f}):\n{g.get('text', '')[:400]}..."
            )
        guideline_text = "\n\n".join(gl_parts)
    else:
        guideline_text = "No guideline evidence retrieved."

    # Risk summary
    if risk_result:
        risk_prob  = risk_result.get("risk_probability", 0)
        is_high    = risk_result.get("is_high_risk", False)
        risk_label = "HIGH RISK" if is_high else "LOW RISK"
        risk_pct   = f"{risk_prob * 100:.1f}%"
    else:
        risk_label = "UNKNOWN"
        risk_pct   = "N/A"

    clinical_question = query.strip() if query and query.strip() else "Provide a comprehensive clinical risk synthesis and evidence-based management recommendations."

    prompt = f"""You are MedGraph AI, an advanced clinical decision support system. Based on the structured patient data, predictive ML risk assessment, and clinical guideline evidence below, generate an evidence-grounded, professional clinical decision briefing for an attending physician.

CRITICAL INSTRUCTIONS:
- Do NOT diagnose or prescribe directly. Provide objective analytical synthesis, highlight risk factors, and reference clinical guidelines.
- Maintain professional, clinical-grade medical terminology.
- Complete all sections fully. Do not truncate, omit sections, or stop mid-sentence.
- Strictly format your entire output using the exact 4 markdown sections specified below.

==================================================
PATIENT DEMOGRAPHIC & CLINICAL PROFILE
==================================================
Age: {patient.get('age', 'N/A')} years | Gender: {patient.get('gender', 'N/A')} | Race: {patient.get('race', 'N/A')}
Location: {patient.get('city', '')}, {patient.get('state', '')}
Total Encounters: {summary.get('total_encounters', 'N/A')} | Total Active Diagnoses: {summary.get('total_conditions', 'N/A')}

ACTIVE CONDITIONS:
{cond_list}

CURRENT MEDICATIONS:
{med_list}

==================================================
PREDICTIVE ML RISK ASSESSMENT (XGBoost + SHAP)
==================================================
Calculated Risk Status: {risk_label}
Model Probability: {risk_pct}

Top SHAP Clinical Feature Attribution Drivers:
{shap_text}

==================================================
RETRIEVED CLINICAL GUIDELINE EVIDENCE (RAG)
==================================================
{guideline_text}

==================================================
FOCUSED CLINICAL INQUIRY
==================================================
{clinical_question}

==================================================
REQUIRED OUTPUT FORMAT
==================================================
Generate the briefing strictly following this 4-part structure without conversational preamble:

### 1. Patient Risk Summary
Provide a 2-3 sentence clinical summary explaining the patient's predicted risk score and the primary demographic or physiological factors driving it.

### 2. Key Clinical Concerns
Provide 3-4 bullet points (- ) highlighting active comorbidities, medication considerations, or elevated biomarkers.

### 3. Evidence-Based Recommendations
Provide 2-3 guideline-backed recommendations (- ) referencing the retrieved evidence regarding target biomarkers, lifestyle, or clinical considerations.

### 4. Monitoring & Follow-Up Priorities
Provide 2-3 actionable bullet points (- ) specifying monitoring intervals (e.g., HbA1c, eGFR, BP) and prioritized next clinical steps.
"""
    return prompt


def _call_gemini(prompt: str, api_key: str) -> str:
    """
    Call Gemini via REST API with automated fallback across compatible models.

    Returns the generated text, or an error message if the call fails.
    """
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature":     0.2,
            "maxOutputTokens": 2048,
            "topP":            0.85,
        },
    }

    last_error = ""
    for model_name in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=35)
            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

            # If 404 (deprecated), 429 (rate limit), 500, or 503 (high demand spike), try next candidate
            if response.status_code in (404, 429, 500, 503):
                try:
                    err_msg = response.json().get("error", {}).get("message", response.text)
                    logger.warning("Gemini model %s returned HTTP %d: %s. Trying fallback model...", model_name, response.status_code, err_msg)
                except Exception:
                    pass
                continue

            try:
                err_json = response.json()
                last_error = err_json.get("error", {}).get("message", response.text)
            except Exception:
                last_error = f"{response.status_code} {response.reason}"
        except requests.exceptions.Timeout:
            logger.warning("Gemini model %s timed out after 35s. Trying next model...", model_name)
            continue
        except Exception as exc:
            return f"[Report generation failed: {exc}]"

    return f"[Gemini API error: {last_error or 'No compatible Gemini model found.'}]"


def report_node(state: MedGraphState) -> MedGraphState:
    """
    LangGraph node: generate a clinical insights report via Gemini.

    Requires state["patient_data"], state["risk_result"], state["guidelines"].
    Populates state["report"] with the LLM-generated clinical summary.
    """
    logger.info("[ReportAgent] Generating clinical report for patient: %s", state["patient_id"])

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        stub_report = (
            "[Report not generated — GEMINI_API_KEY environment variable is not set. "
            "Set it with: set GEMINI_API_KEY=your_key_here]"
        )
        logger.warning("[ReportAgent] GEMINI_API_KEY not set — returning stub report.")
        return {**state, "report": stub_report}

    patient_data = state.get("patient_data")
    risk_result  = state.get("risk_result") or {}
    guidelines   = state.get("guidelines") or []
    query        = state.get("query", "")

    if not patient_data:
        return {
            **state,
            "report": "[Report skipped — no patient data available.]",
        }

    try:
        prompt = _build_prompt(patient_data, risk_result, guidelines, query)
        report = _call_gemini(prompt, api_key)
        logger.info("[ReportAgent] Report generated (%d chars).", len(report))
        return {**state, "report": report}

    except Exception as exc:
        error_msg = f"ReportAgent error: {exc}"
        logger.error(error_msg)
        return {
            **state,
            "report": f"[Report generation error: {exc}]",
            "errors": state.get("errors", []) + [error_msg],
        }
