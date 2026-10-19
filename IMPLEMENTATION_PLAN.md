# MILESTONES.md

# MedGraph AI Development Milestones

Version: 2.0 (Frozen)

---

# Purpose

This document defines the implementation order for MedGraph AI.

The project is developed in phases that follow the natural dependency chain of the system.

The focus is on building the core intelligence first and the application around it later.

Each phase must be completed, validated and approved before moving to the next.

---

# Development Philosophy

Understand before implementing.

Build the data foundation before building intelligence.

Build intelligence before building interfaces.

Package and deploy only after the core system is complete.

Every phase should produce a meaningful deliverable that can be independently tested.

---

# Phase 0 — Research & Data Understanding

## Objective

Develop a complete understanding of the healthcare dataset before writing production code.

## Tasks

- Explore every Synthea CSV
- Understand relationships between datasets
- Identify primary keys and foreign keys
- Validate assumptions
- Identify useful healthcare entities
- Explore clinical observations
- Identify candidate ML features
- Investigate class distribution
- Decide how the "High-Risk Patient" label should be defined (after inspecting the data)

## Deliverables

- Dataset understanding
- Entity relationship understanding
- Canonical data model
- Feature engineering plan
- Risk label definition

## Exit Criteria

- Every dataset is understood.
- Relationships are documented.
- No major unknowns remain.

---

# Phase 1 — ETL & Canonical Data Layer

## Objective

Transform raw healthcare data into reusable datasets.

## Tasks

- Build PySpark ETL pipeline
- Clean missing values
- Normalize datasets
- Map ICD-10 codes
- Map RxNorm codes
- Engineer ML features
- Export processed datasets

## Deliverables

- Processed healthcare dataset
- Feature table
- Reproducible ETL pipeline

## Exit Criteria

- ETL runs successfully end-to-end.
- Processed data is validated.
- Feature table is complete.

---

# Phase 2 — Healthcare Knowledge Graph

## Objective

Construct and validate the Healthcare Knowledge Graph.

## Tasks

- Design graph schema
- Populate Neo4j
- Create relationships
- Validate graph integrity
- Develop reusable Cypher queries

## Deliverables

- Complete Healthcare Knowledge Graph

## Exit Criteria

- All entities imported.
- Relationship counts validated.
- Patient journeys reconstructed successfully.

---

# Phase 3 — Predictive Analytics

## Objective

Develop an explainable patient risk prediction pipeline.

## Tasks

- Finalize target definition
- Train XGBoost model
- Evaluate performance
- Generate SHAP explanations
- Save trained model

## Deliverables

- Trained prediction model
- Explainability pipeline

## Exit Criteria

- Model performance documented.
- SHAP explanations validated.
- Model ready for inference.

---

# Phase 4 — Clinical Knowledge Retrieval

## Objective

Build evidence retrieval from clinical guidelines.

## Tasks

- Prepare guideline documents
- Chunk documents
- Generate embeddings
- Store vectors in Qdrant
- Evaluate retrieval quality

## Deliverables

- Working RAG subsystem

## Exit Criteria

- Relevant guideline sections retrieved consistently.

---

# Phase 5 — Agentic Orchestration

## Objective

Connect all intelligence components using LangGraph.

## Tasks

- Implement Planner
- Implement Graph Agent
- Implement Prediction Agent
- Implement Guideline Agent
- Implement Report Generator
- Implement conditional routing

## Deliverables

- Complete LangGraph workflow

## Exit Criteria

- Multiple query paths execute correctly.
- Planner routes appropriately.

---

# Phase 6 — Backend Application

## Objective

Expose project functionality through FastAPI.

## Tasks

- Design REST API
- Implement services
- Connect Neo4j
- Connect ML inference
- Connect Qdrant
- Connect LangGraph

## Deliverables

- Stable backend API

## Exit Criteria

- All endpoints tested.
- Response formats standardised.

---

# Phase 7 — Frontend Application

## Objective

Build the interactive analytics dashboard.

## Tasks

- Patient search
- Patient profile
- Graph visualization
- Analytics dashboard
- AI insight interface

## Deliverables

- Complete frontend

## Exit Criteria

- End-to-end user workflows functional.

---

# Phase 8 — Refinement

## Objective

Improve quality, performance and reliability.

## Tasks

- Refactoring
- Performance optimisation
- Validation
- Error handling
- UX improvements
- Testing

## Deliverables

- Production-quality academic project

## Exit Criteria

- Stable and polished system.

---

# Phase 9 — Packaging & Deployment

## Objective

Prepare the project for demonstration and sharing.

## Tasks

- Docker
- Documentation
- README
- Screenshots
- Demo data
- Deployment

## Deliverables

- Deployable project package

## Exit Criteria

- Project reproducible on another machine.

---

# Phase Completion Rules

A phase is complete only when:

- All deliverables are finished.
- Exit criteria are satisfied.
- Manual testing is complete.
- Architecture remains consistent.
- Approval has been received.

The next phase must not begin without approval.