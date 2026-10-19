# MedGraph AI
### Intelligent Healthcare Analytics Platform

Version: 1.0 (Frozen)

---

# Overview

MedGraph AI is an AI-powered healthcare analytics platform that transforms fragmented synthetic Electronic Health Records (EHRs) into an interconnected Healthcare Knowledge Graph, performs predictive risk analytics, retrieves evidence from clinical guidelines using Retrieval-Augmented Generation (RAG), and generates explainable patient summaries through a Large Language Model.

The platform is designed for educational, research, and healthcare analytics purposes.

It is **not** intended for clinical diagnosis, treatment recommendation, or real-world patient care.

---

# Motivation

Healthcare information is naturally connected.

Every patient has:

- encounters
- diagnoses
- medications
- laboratory observations
- procedures
- providers

Traditional relational dashboards display these as isolated tables.

MedGraph AI instead represents healthcare as a connected graph, enabling relationship-centric exploration, analytics, and evidence-grounded explanations.

---

# Objectives

The project aims to:

- Build a scalable healthcare ETL pipeline.
- Construct a Healthcare Knowledge Graph.
- Perform clinical risk prediction.
- Retrieve relevant clinical guideline evidence.
- Generate explainable AI-assisted patient summaries.
- Provide an interactive healthcare analytics dashboard.

---

# Scope

## Included

### Data Engineering

- Import synthetic EHR data
- Data cleaning
- Data normalization
- Feature engineering

### Knowledge Graph

- Patient graph construction
- Relationship visualization
- Patient timeline exploration

### Analytics

- Population analytics
- Disease statistics
- Medication trends
- Encounter analytics

### Machine Learning

- High-risk patient classification
- Explainable predictions using SHAP

### Retrieval-Augmented Generation

- Guideline retrieval
- Evidence-grounded explanations

### AI

- LangGraph orchestration
- Natural-language patient summaries

### Frontend

- Interactive dashboard
- Patient profile
- Graph visualization
- Analytics pages

---

# Out of Scope

The following are explicitly NOT part of Version 1:

- Medical diagnosis
- Treatment recommendation
- Drug prescription
- Clinical decision making
- Real patient data
- Medical image analysis
- Wearable integration
- Speech recognition
- IoT devices
- Hospital deployment

---

# Target Users

Primary Users

- Healthcare researchers
- Students
- Healthcare data analysts
- Academic evaluators

Secondary Users

- Recruiters
- Data engineering interviewers

---

# Technology Stack

## Frontend

- Next.js
- React
- Tailwind CSS
- Cytoscape.js
- Chart.js

## Backend

- FastAPI

## Data Engineering

- PySpark

## Database

- Neo4j

## Vector Database

- Qdrant

## Machine Learning

- XGBoost
- SHAP

## AI

- LangGraph
- OpenAI / Gemini API

## Deployment

- Docker

---

# Data Sources

Primary Dataset

- Synthea (CSV)

Supporting Datasets

- ICD-10-CM
- RxNorm

Clinical Knowledge

- WHO PEN Guidelines
- KDIGO CKD Guideline
- WHO Hypertension Guideline

---

# Core Workflow

Synthea CSV

↓

PySpark ETL

↓

Data Normalization

↓

Neo4j Knowledge Graph

↓

Clinical Analytics

↓

Risk Prediction

↓

Clinical Guideline Retrieval

↓

LLM Explanation

↓

Interactive Dashboard

---

# Key Features

1. Automated ETL Pipeline
2. Healthcare Knowledge Graph
3. Patient Timeline
4. Population Analytics
5. High-Risk Patient Classification
6. Explainable AI (SHAP)
7. Clinical Guideline Retrieval
8. AI-generated Patient Summary
9. Interactive Dashboard
10. Graph Visualization

---

# What Makes MedGraph AI Different

Unlike a traditional chatbot,

MedGraph AI combines:

- Data Engineering
- Knowledge Graphs
- Machine Learning
- RAG
- Agentic Workflow
- Explainable AI

into a single analytics platform.

The LLM is not the primary source of intelligence.

Instead, it synthesizes information produced by multiple specialized components.

---

# Guiding Principles

Every technology included in the project must solve a genuine engineering problem.

No component exists solely to increase perceived complexity.

The architecture prioritizes:

- Explainability
- Modularity
- Scalability
- Maintainability
- Evidence-grounded responses

over novelty.

---

# Success Criteria

The project will be considered successful if it can:

- Import healthcare data.
- Construct a complete patient graph.
- Display interactive healthcare analytics.
- Predict patient risk.
- Explain predictions using SHAP.
- Retrieve relevant clinical guideline evidence.
- Generate coherent evidence-grounded summaries.
- Operate through a unified dashboard.

---

# Future Extensions

Potential Version 2 enhancements:

- FHIR support
- Real hospital datasets
- Drug interaction engine
- Semantic Scholar integration
- Multi-modal healthcare data
- Time-series forecasting
- Clinical pathway analytics

These are intentionally excluded from Version 1.