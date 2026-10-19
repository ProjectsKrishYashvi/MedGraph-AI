# MedGraph AI — Clinical Decision Support & Healthcare Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.x-008CC1.svg)](https://neo4j.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0%2B-orange.svg)](https://xgboost.readthedocs.io/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-green.svg)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)

> **MedGraph AI** is an enterprise-grade clinical decision support platform that combines **Knowledge Graphs (Neo4j)**, **Predictive Analytics (XGBoost + TreeSHAP)**, **Retrieval-Augmented Generation (Qdrant RAG)**, and **Multi-Agent Orchestration (LangGraph + Gemini)** to synthesize patient records, predict readmission risk, and generate evidence-based clinical summaries.

---

## 🏥 Key Capabilities

- **Encounter-Centric Knowledge Graph**: Models longitudinal patient trajectories in **Neo4j** connecting patients to hospital encounters, SNOMED-CT diagnoses, RxNorm medications, and vital observations.
- **Predictive Risk Stratification**: An **XGBoost** classifier trained across 38 clinical features to predict 30-day hospital readmission risk.
- **Explainable AI (TreeSHAP)**: Provides exact local Shapley feature attributions (directional impact) for every single prediction so clinicians understand *why* a risk score was assigned.
- **Clinical Guideline RAG**: Employs **Qdrant** and **FastEmbed** (`bge-small-en-v1.5`) to index and semantically retrieve evidence from the **ADA** (Diabetes), **KDIGO 2024** (Chronic Kidney Disease), and **WHO PEN** (Cardiovascular protocols).
- **Deterministic Multi-Agent Pipeline**: Powered by **LangGraph** with a strict architectural principle: all reasoning, graph queries, ML inference, and guideline retrieval occur deterministically *before* the language model (Gemini) generates the final synthesis.
- **Modern Clinician Dashboard**: Built with **React 18 + Vite**, featuring real-time population surveillance, cohort registry filtering, interactive risk gauges, SHAP waterfall charts, and prompt blueprint inspection.

---

## 🏗️ System Architecture

```
                       Raw Synthea EHR Data
                                │
                        [PySpark / Pandas ETL]
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
[Neo4j Knowledge Graph]                       [features.parquet (1,163 pts)]
        │                                               │
        │                                               ▼
        │                                   [XGBoost Model + TreeSHAP]
        │                                               │
        ▼                                               ▼
┌───────────────────────────────────────────────────────────────┐
│        LangGraph Multi-Agent Orchestration Pipeline           │
│                                                               │
│  1. GraphAgent      ──► Queries Neo4j for longitudinal profile│
│  2. PredictionAgent ──► Generates readmission risk & SHAP     │
│  3. GuidelineAgent  ──► Queries Qdrant RAG (ADA / KDIGO / WHO)│
│  4. ReportAgent     ──► Synthesizes briefing via Gemini REST  │
└───────────────────────────────────────────────────────────────┘
                                │
                                ▼
                   [FastAPI REST Backend (8000)]
                                │
                                ▼
                 [React + Vite Dashboard (5173)]
```

---

## 🛠️ Tech Stack Breakdown

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Data Engine & ETL** | PySpark / Pandas | Ingestion, validation, and feature engineering from Synthea EHR into canonical Parquet tables. |
| **Knowledge Graph** | Neo4j Enterprise | Models longitudinal patient entities (`Patient`, `Encounter`, `Condition`, `Medication`, `Observation`). |
| **Risk Prediction** | XGBoost Classifier | Calibrated probability prediction for chronic disease readmission across 38 features. |
| **Model Explainability** | TreeSHAP | Local feature attribution calculating exact marginal risk increase/decrease per biomarker. |
| **Vector Database (RAG)** | Qdrant (Local) | Storage and cosine similarity search over chunked clinical guidelines (134 vectors). |
| **Embedding Model** | FastEmbed (`bge-small-en-v1.5`) | CPU-optimized ONNX runtime generating 384-dimensional dense vector embeddings. |
| **Agent Orchestration** | LangGraph | Sequential `StateGraph` coordinating 4 specialized clinical agents with typed state. |
| **Generative AI** | Google Gemini (REST) | Zero-SDK REST generation of evidence-grounded clinical briefings. |
| **Backend REST API** | FastAPI + Uvicorn | Asynchronous Python API layer with Pydantic v2 data validation and CORS middleware. |
| **Frontend Application** | React 18 + Vite | High-density clinical analytics dashboard with dark obsidian medical theme. |

---

## 🚀 Quick Start & Setup

### 1. Prerequisites
- Python 3.9+
- Node.js 18+ and npm
- Neo4j 5.x running locally on `bolt://localhost:7687`

### 2. Configure Environment
Copy the example environment file:
```bash
cp .env.example .env
```
Edit `.env` with your settings:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

### 3. Backend Setup & Startup
Install Python dependencies:
```bash
pip install -r requirements.txt
```
Start the FastAPI server:
```bash
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```
*API will be live at `http://localhost:8000` (Interactive Swagger docs: `http://localhost:8000/docs`)*

### 4. Frontend Setup & Startup
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```
*Dashboard will be accessible at `http://localhost:5173`*

---

## 🧪 API Endpoints

- `GET /health` — Multi-system health telemetry check (API, Neo4j, XGBoost, Qdrant).
- `GET /population/stats` — Cohort surveillance metrics and chronic comorbidity prevalence.
- `GET /patients` — Paginated registry with multi-parameter filtering (by risk tier, condition, search query).
- `GET /patients/{id}` — Deep-dive patient profile with full longitudinal encounter timeline from Neo4j.
- `POST /predict` — XGBoost risk probability calculation and top-5 SHAP feature contributions.
- `POST /insights` — Full LangGraph multi-agent execution returning graph data, risk predictions, retrieved guidelines, and synthesized decision briefing.

---

## 📄 License
This project is licensed under the MIT License.
