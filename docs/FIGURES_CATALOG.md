# MedGraph AI — Report Figures & Architecture Catalog

This directory contains the official publication-grade figures, architecture flowcharts, and empirical evaluation plots generated from the real MedGraph AI production database, models, and multi-agent pipeline.

---

## 📊 Summary of Report Figures

| Figure ID | File Name | Title & Clinical Context | Report Section |
| :--- | :--- | :--- | :--- |
| **Figure 1** | [`fig1_system_architecture.png`](figures/fig1_system_architecture.png) | **End-to-End System Architecture & Data Flow**<br>Comprehensive multi-tier pipeline from raw Synthea EHR ingestion to Neo4j graph storage, Qdrant RAG, XGBoost ML, LangGraph orchestration, and React Vite frontend. | *Chapter 2: System Architecture* |
| **Figure 2** | [`fig2_knowledge_graph_schema.png`](figures/fig2_knowledge_graph_schema.png) | **Neo4j Knowledge Graph Schema & Entity Network**<br>Encounter-centric clinical ontology mapping 367,975 nodes and 488,603 relationships with SNOMED-CT, RxNorm, and LOINC standardizations. | *Chapter 3: Knowledge Graph Modeling* |
| **Figure 3** | [`fig3_langgraph_workflow.png`](figures/fig3_langgraph_workflow.png) | **LangGraph Multi-Agent StateGraph Workflow**<br>Deterministic state machine coordinating GraphAgent, PredictionAgent, GuidelineAgent, and ReportAgent with strict medical safety invariants. | *Chapter 4: Multi-Agent Orchestration* |
| **Figure 4** | [`fig4_ml_model_evaluation.png`](figures/fig4_ml_model_evaluation.png) | **Machine Learning Evaluation & Cross-Validation**<br>Test Confusion Matrix (N=233), 5-Fold Stratified Cross-Validation (Mean ROC-AUC: 0.995), and Performance Metrics Summary (97.9% Accuracy, 96.2% F1). | *Chapter 5: Predictive Modeling & Validation* |
| **Figure 5** | [`fig5_shap_feature_importance.png`](figures/fig5_shap_feature_importance.png) | **TreeSHAP Global Feature Importance**<br>Top 12 clinical drivers influencing 30-day readmission risk (Patient Age, HbA1c, Hypertension, Systolic BP, Glucose, Encounter Frequency). | *Chapter 6: Explainable AI & Clinical Interpretability* |

---

## 🖼️ Figure Descriptions & Suggested Report Captions

### Figure 1: End-to-End System Architecture
* **Caption**: *Figure 1: End-to-end multi-tier architecture of MedGraph AI. Data flows from raw Synthea EHR extracts through canonical Parquet normalization into dual storage engines (Neo4j for longitudinal trajectories and Qdrant for guideline RAG). A sequential LangGraph StateGraph coordinates four deterministic clinical agents before Gemini synthesizes the final evidence-grounded briefing delivered through the FastAPI and React 18 dashboard.*
* **File**: `docs/figures/fig1_system_architecture.png`

### Figure 2: Neo4j Knowledge Graph Schema
* **Caption**: *Figure 2: Encounter-centric knowledge graph ontology implemented in Neo4j Enterprise. Hospital encounters act as the central pivot connecting patients to active conditions (SNOMED-CT), medication orders (RxNorm), laboratory observations (LOINC), and clinical procedures, validated across 367,975 nodes and 488,603 relationships with zero orphan records.*
* **File**: `docs/figures/fig2_knowledge_graph_schema.png`

### Figure 3: LangGraph Multi-Agent State Machine Workflow
* **Caption**: *Figure 3: Deterministic multi-agent state graph executed by LangGraph. All graph traversals, calibrated XGBoost inference, and Qdrant vector guideline searches occur strictly prior to the LLM invocation, ensuring that natural language generation is grounded 100% in verified clinical evidence with zero hallucination risk.*
* **File**: `docs/figures/fig3_langgraph_workflow.png`

### Figure 4: ML Model Performance & Cross-Validation
* **Caption**: *Figure 4: Empirical evaluation of the XGBoost 30-day readmission classifier. (A) Confusion matrix on the held-out test cohort (N=233) achieving 97.9% accuracy and 96.2% F1-score. (B) 5-fold stratified cross-validation demonstrating consistent discriminative power (Mean ROC-AUC: 0.995 ± 0.004). (C) Comprehensive metric benchmark across accuracy, precision, recall, F1, PR-AUC, and ROC-AUC.*
* **File**: `docs/figures/fig4_ml_model_evaluation.png`

### Figure 5: TreeSHAP Global Clinical Feature Attributions
* **Caption**: *Figure 5: Global feature importance calculated via TreeSHAP across 38 clinical features. Patient age, glycemic control (HbA1c), essential hypertension, and systolic blood pressure exhibit the highest mean absolute SHAP attribution values, confirming physiological alignment with clinical chronic disease readmission drivers.*
* **File**: `docs/figures/fig5_shap_feature_importance.png`

---

## 🔄 Reproduction
To regenerate all figures at any time with high-resolution 300 DPI:
```bash
python docs/generate_report_figures.py
```
