# ARCHITECTURE.md

# MedGraph AI Architecture

Version: 1.0 (Frozen)

---

# System Overview

MedGraph AI is a modular healthcare analytics platform built around a healthcare knowledge graph.

Rather than sending user questions directly to an LLM, the platform first performs structured data retrieval, predictive analytics, and evidence retrieval before generating an explainable response.

The LLM acts only as the final report generation component.

---

# High-Level Architecture

                     User
                       │
                       ▼
              Next.js Frontend
                       │
                 REST API Calls
                       │
                       ▼
                 FastAPI Backend
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   Neo4j Graph     XGBoost ML      LangGraph
        │              │              │
        │              │              ▼
        │              │         Qdrant Vector DB
        │              │              │
        └──────────────┴──────────────┘
                       │
                 Report Generator
                       │
                  LLM Response
                       │
                       ▼
              Next.js Dashboard

---

# Core Components

## 1. Data Layer

Responsible for storing all healthcare data.

Data Sources

- Synthea CSV
- ICD-10
- RxNorm
- Clinical Guideline PDFs

---

## 2. ETL Layer

Technology

PySpark

Responsibilities

- Read CSV files
- Remove inconsistencies
- Normalize values
- Map ICD codes
- Normalize medication names
- Generate ML features
- Load Neo4j

Output

Unified healthcare dataset.

---

## 3. Graph Database

Technology

Neo4j

Purpose

Represent healthcare as relationships.

Stores

Patients

Encounters

Conditions

Medications

Observations

Procedures

Providers

Organizations

The graph is considered the primary analytical datastore.

---

## 4. Machine Learning Layer

Technology

XGBoost

Purpose

Predict whether a patient belongs to a high-risk cohort.

Input

Patient features generated during ETL.

Output

Risk probability.

The prediction is never used directly.

It is always accompanied by SHAP explanations.

---

## 5. Explainability Layer

Technology

SHAP

Purpose

Explain why the model predicted a particular risk score.

Example

High Risk because

- Diabetes
- CKD
- Age
- Frequent encounters

The dashboard always displays these explanations.

---

## 6. Vector Database

Technology

Qdrant

Purpose

Store embeddings of clinical guideline documents.

Contains

- WHO PEN
- KDIGO
- WHO Hypertension

Workflow

PDF

↓

Chunk

↓

Embedding

↓

Qdrant

During inference

Question

↓

Similarity Search

↓

Relevant Chunks

---

## 7. LangGraph Orchestrator

Purpose

Coordinate multiple independent reasoning steps.

The orchestrator is responsible for sequencing specialised components.

It does not replace business logic.

---

# LangGraph Workflow

                User Query
                     │
                     ▼
              Planner Node
                     │
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
 Graph Agent   Prediction Agent  Guideline Agent
      │              │              │
   Neo4j         XGBoost         Qdrant
      │              │              │
      └──────────────┼──────────────┘
                     ▼
             Report Generator
                     │
                    LLM
                     │
                     ▼
               Final Response

---

## Graph Agent

Responsibilities

- Query Neo4j
- Retrieve patient history
- Retrieve encounters
- Retrieve medications
- Retrieve observations
- Return structured graph data

---

## Prediction Agent

Responsibilities

- Load patient features
- Run XGBoost model
- Compute SHAP explanations
- Return prediction

---

## Guideline Agent

Responsibilities

- Search Qdrant
- Retrieve relevant guideline chunks
- Return evidence

---

## Report Generator

Responsibilities

Combine

Graph

+

Prediction

+

Evidence

↓

Generate evidence-grounded explanation.

Only this node interacts with the LLM.

---

# Frontend

Technology

Next.js

Responsibilities

Provide an interactive user interface.

Modules

- Dashboard
- Patient Search
- Patient Profile
- Patient Timeline
- Graph Visualization
- Population Analytics
- AI Insights

---

# Backend

Technology

FastAPI

Responsibilities

Expose REST endpoints.

Coordinate

Neo4j

ML

LangGraph

Qdrant

Authentication is intentionally omitted in Version 1.

---

# Data Flow

Raw Synthea CSV

↓

PySpark ETL

↓

Data Cleaning

↓

ICD Mapping

↓

RxNorm Mapping

↓

Feature Engineering

↓

Neo4j

↓

Analytics

↓

LangGraph

↓

LLM

↓

Dashboard

---

# AI Flow

User Question

↓

Planner

↓

Graph Retrieval

↓

Risk Prediction

↓

Guideline Retrieval

↓

LLM

↓

Explanation

---

# Retrieval Flow

Clinical Guideline PDF

↓

Chunking

↓

Embedding

↓

Qdrant

↓

Similarity Search

↓

Relevant Context

↓

LLM

---

# Prediction Flow

Patient

↓

Feature Extraction

↓

XGBoost

↓

Risk Score

↓

SHAP

↓

Explanation

↓

Dashboard

---

# Design Principles

Every layer has exactly one responsibility.

PySpark

↓

ETL

Neo4j

↓

Relationships

Qdrant

↓

Semantic Retrieval

XGBoost

↓

Prediction

LangGraph

↓

Workflow Orchestration

LLM

↓

Natural Language Generation

No component duplicates the responsibility of another.

---

# Architectural Constraints

Version 1 must NOT

- Diagnose diseases
- Recommend treatments
- Prescribe medications
- Replace clinicians

The system provides analytics and explainable insights only.

---

# Scalability

The architecture should support

- Larger Synthea datasets
- Additional guidelines
- Multiple prediction models
- Additional graph entities
- Future FHIR integration

without major architectural changes.

---

# Summary

MedGraph AI follows a layered architecture where structured analytics always precede AI generation.

The LLM is intentionally positioned as the final explanation component rather than the primary reasoning engine.

This design improves explainability, modularity, maintainability, and trustworthiness while avoiding the limitations of LLM-only healthcare applications.