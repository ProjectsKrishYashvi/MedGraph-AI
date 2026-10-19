import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import PopulationOverview from './components/PopulationOverview';
import PatientRegistry from './components/PatientRegistry';
import PatientProfileCard from './components/PatientProfileCard';
import RiskGauge from './components/RiskGauge';
import SHAPContributors from './components/SHAPContributors';
import PatientGraphTimeline from './components/PatientGraphTimeline';
import GuidelineEvidence from './components/GuidelineEvidence';
import ClinicalReport from './components/ClinicalReport';

import { 
  fetchHealth, 
  fetchPopulationStats, 
  fetchPatients, 
  fetchPatientProfile, 
  predictPatientRisk, 
  fetchPatientInsights 
} from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('population'); // 'population' | 'registry' | 'patient'
  const [telemetry, setTelemetry] = useState({ api: 'ok', neo4j: 'unknown', model: 'unknown', qdrant: 'unknown' });
  const [populationStats, setPopulationStats] = useState(null);

  // Registry state
  const [patients, setPatients] = useState([]);
  const [totalPatients, setTotalPatients] = useState(0);
  const [registryLoading, setRegistryLoading] = useState(false);
  const [registryFilter, setRegistryFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [patientSearchInput, setPatientSearchInput] = useState('');
  const [page, setPage] = useState(0);

  // Active Patient Deep-Dive state
  const [selectedPatientId, setSelectedPatientId] = useState(null);
  const [patientProfile, setPatientProfile] = useState(null);
  const [riskResult, setRiskResult] = useState(null);
  const [guidelines, setGuidelines] = useState([]);
  const [report, setReport] = useState('');
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // 1. Initial Telemetry & Population Stats
  useEffect(() => {
    async function initTelemetry() {
      try {
        const health = await fetchHealth();
        if (health && health.components) {
          setTelemetry(health.components);
        }
      } catch (err) {
        console.warn('Health check failed:', err);
      }

      try {
        const stats = await fetchPopulationStats();
        setPopulationStats(stats);
      } catch (err) {
        console.warn('Population stats failed:', err);
      }
    }
    initTelemetry();
  }, []);

  // 2. Fetch Patients for Registry
  useEffect(() => {
    async function loadPatients() {
      setRegistryLoading(true);
      try {
        const isHighRisk = registryFilter === 'high_risk' ? true : null;
        const condition = ['diabetes', 'hypertension', 'ckd', 'heart_failure'].includes(registryFilter)
          ? registryFilter
          : '';

        const data = await fetchPatients({
          limit: 25,
          offset: page * 25,
          search: searchTerm,
          isHighRisk,
          condition
        });

        setPatients(data.patients || []);
        setTotalPatients(data.total || 0);

        // Pre-select first patient if none selected
        if (!selectedPatientId && data.patients && data.patients.length > 0) {
          setSelectedPatientId(data.patients[0].patient_id);
        }
      } catch (err) {
        console.error('Failed to load patients:', err);
      } finally {
        setRegistryLoading(false);
      }
    }
    loadPatients();
  }, [registryFilter, searchTerm, page]);

  // 3. Load Active Patient Data when selected
  useEffect(() => {
    if (!selectedPatientId) return;

    async function loadPatientDetails() {
      setLoadingInsights(true);
      setErrorMsg('');
      try {
        // Fetch raw profile from Neo4j
        const profileData = await fetchPatientProfile(selectedPatientId);
        setPatientProfile(profileData);

        // Run full insights workflow (LangGraph 4 agents)
        const insightsData = await fetchPatientInsights(selectedPatientId);
        if (insightsData.risk_result) {
          setRiskResult(insightsData.risk_result);
        }
        setGuidelines(insightsData.guidelines || []);
        setReport(insightsData.report || '');
      } catch (err) {
        console.error('Error loading patient details:', err);
        // Fallback: try direct predict if insights workflow failed
        try {
          const pred = await predictPatientRisk(selectedPatientId);
          setRiskResult(pred);
        } catch (predErr) {
          console.error('Fallback predict also failed:', predErr);
        }
        setErrorMsg(err.message || 'Error running clinical evaluation');
      } finally {
        setLoadingInsights(false);
      }
    }

    loadPatientDetails();
  }, [selectedPatientId]);

  // Handlers
  const handleSelectPatient = (pid) => {
    setSelectedPatientId(pid);
    setActiveTab('patient');
  };

  const handleHeaderSearch = (e) => {
    e.preventDefault();
    if (patientSearchInput.trim()) {
      handleSelectPatient(patientSearchInput.trim());
    }
  };

  const handleRunCustomQuery = async (customQuestion) => {
    if (!selectedPatientId) return;
    setLoadingInsights(true);
    try {
      const insightsData = await fetchPatientInsights(selectedPatientId, customQuestion);
      setReport(insightsData.report || '');
      if (insightsData.guidelines) {
        setGuidelines(insightsData.guidelines);
      }
    } catch (err) {
      console.error('Failed to run custom query:', err);
      setErrorMsg(err.message || 'Custom inquiry failed');
    } finally {
      setLoadingInsights(false);
    }
  };

  return (
    <div className="app-container">
      <Header 
        telemetry={telemetry}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        patientSearch={patientSearchInput}
        setPatientSearch={setPatientSearchInput}
        onSearchSubmit={handleHeaderSearch}
        selectedPatientId={selectedPatientId}
      />

      <main className="main-content">
        {/* VIEW 1: POPULATION OVERVIEW */}
        {activeTab === 'population' && (
          <PopulationOverview 
            stats={populationStats}
            onSelectConditionFilter={(condName) => {
              const map = {
                'Diabetes': 'diabetes',
                'Hypertension': 'hypertension',
                'Chronic Kidney Disease': 'ckd',
                'Heart Failure': 'heart_failure',
              };
              setRegistryFilter(map[condName] || 'all');
              setActiveTab('registry');
            }}
            onViewRegistry={() => setActiveTab('registry')}
          />
        )}

        {/* VIEW 2: PATIENT REGISTRY TABLE */}
        {activeTab === 'registry' && (
          <PatientRegistry 
            patients={patients}
            total={totalPatients}
            loading={registryLoading}
            selectedPatientId={selectedPatientId}
            onSelectPatient={handleSelectPatient}
            currentFilter={registryFilter}
            onFilterChange={(f) => {
              setRegistryFilter(f);
              setPage(0);
            }}
            searchTerm={searchTerm}
            onSearchChange={(term) => {
              setSearchTerm(term);
              setPage(0);
            }}
            page={page}
            onPageChange={setPage}
          />
        )}

        {/* VIEW 3: PATIENT CLINICAL DEEP-DIVE */}
        {activeTab === 'patient' && (
          <div className="deep-dive-grid">
            {/* Left Column: Diagnostics, Graph & Risk Attributions */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <PatientProfileCard 
                patient={patientProfile?.demographics}
                summary={{
                  total_encounters: patientProfile?.demographics?.total_encounters ?? (patientProfile?.encounters?.length || 0),
                  total_conditions: patientProfile?.conditions?.length || 0,
                  total_medications: patientProfile?.medications?.length || 0,
                  total_procedures: patientProfile?.demographics?.total_procedures || 0,
                }}
              />

              <RiskGauge riskResult={riskResult} />

              <SHAPContributors contributions={riskResult?.top_shap_contributions} />

              <PatientGraphTimeline 
                conditions={patientProfile?.conditions}
                medications={patientProfile?.medications}
                encounters={patientProfile?.encounters}
              />
            </div>

            {/* Right Column: Multi-Agent Decision Support & RAG Guidelines */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <ClinicalReport 
                report={report}
                loading={loadingInsights}
                onRunQuery={handleRunCustomQuery}
                patientId={selectedPatientId}
              />

              <GuidelineEvidence guidelines={guidelines} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
