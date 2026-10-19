# CONTRIBUTING.md

# MedGraph AI Development Guidelines

Version: 1.0 (Frozen)

This document defines the coding standards, project conventions and implementation rules for MedGraph AI.

---

# Core Philosophy

This project prioritises:

- Correctness
- Maintainability
- Explainability
- Clean architecture
- Reproducibility

The goal is not to build the fastest possible prototype, but a project that demonstrates good software engineering practices.

---

# General Rules

- Follow the frozen architecture unless an implementation blocker is discovered.
- Never redesign components without explicit approval.
- Prefer readable code over clever code.
- Keep modules loosely coupled.
- Avoid unnecessary abstractions.
- Remove dead code rather than commenting it out.

---

# Project Structure

backend/
    api/
    services/
    graph/
    ml/
    rag/
    langgraph/
    models/
    schemas/
    utils/

frontend/
    app/
    components/
    lib/
    hooks/
    types/

data/
    raw/
    processed/
    reference/

notebooks/

docs/

---

# Naming Conventions

Classes:
PascalCase

Functions:
snake_case (Python)

React Components:
PascalCase

Variables:
descriptive_snake_case

Constants:
UPPER_CASE

---

# API Design

RESTful endpoints.

Use nouns instead of verbs.

Good:

/patients

/patients/{id}

/analytics

Avoid:

/getPatient

/loadPatient

---

# Error Handling

Never silently ignore errors.

Always provide meaningful messages.

Catch only expected exceptions.

---

# Logging

Use structured logging.

Do not print debugging statements in production code.

---

# Configuration

Never hardcode:

- paths
- secrets
- API keys
- database credentials

Use environment variables.

---

# Business Logic

Business logic must never exist inside API routes.

Routes should only:

- validate requests
- call services
- return responses

---

# Machine Learning

Training code and inference code must remain separate.

Feature engineering must be deterministic.

Random seeds should be fixed where appropriate.

---

# LangGraph

Each node should have one responsibility.

Avoid monolithic nodes.

Planner routing should remain explicit and understandable.

---

# Neo4j

Use parameterised Cypher queries.

Avoid duplicated queries.

Keep graph operations inside a dedicated graph layer.

---

# Frontend

Components should remain reusable.

Avoid embedding API logic directly into presentation components.

---

# Git

Small commits.

Clear commit messages.

One logical change per commit.

---

# Documentation

Every new module should include:

- purpose
- inputs
- outputs
- dependencies

---

# Testing

Every major feature should be manually verified before proceeding.

Critical modules should include automated tests where practical.

---

# Code Review Checklist

Before considering any feature complete:

- Is the code readable?
- Is it modular?
- Is it tested?
- Does it match the architecture?
- Does it introduce duplication?
- Can another engineer understand it?

If any answer is "No", revise before moving forward.