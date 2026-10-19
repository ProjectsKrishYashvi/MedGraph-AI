import React from 'react';
import { Activity, Database, Server, Cpu, Layers, Search, ShieldCheck } from 'lucide-react';

export default function Header({ 
  telemetry, 
  activeTab, 
  setActiveTab, 
  patientSearch, 
  setPatientSearch, 
  onSearchSubmit,
  selectedPatientId 
}) {
  const getPillStatusClass = (status) => {
    if (status === 'ok') return 'pulse-dot';
    if (status?.startsWith('error')) return 'pulse-dot error';
    return 'pulse-dot degraded';
  };

  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-icon-wrapper">
          <Activity size={20} />
        </div>
        <div>
          <div className="brand-title">MedGraph AI</div>
          <div className="brand-subtitle">Clinical Intelligence & Risk Decision Support</div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        {/* Navigation Tabs */}
        <div style={{ display: 'flex', background: 'var(--bg-inset)', padding: '0.2rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
          <button 
            className={`btn ${activeTab === 'population' ? 'btn-primary' : 'btn-outline'}`}
            style={{ padding: '0.35rem 0.85rem', fontSize: '0.78rem', border: 'none' }}
            onClick={() => setActiveTab('population')}
          >
            <Layers size={14} />
            Population Overview
          </button>
          <button 
            className={`btn ${activeTab === 'registry' ? 'btn-primary' : 'btn-outline'}`}
            style={{ padding: '0.35rem 0.85rem', fontSize: '0.78rem', border: 'none' }}
            onClick={() => setActiveTab('registry')}
          >
            <Database size={14} />
            Patient Registry
          </button>
          <button 
            className={`btn ${activeTab === 'patient' ? 'btn-primary' : 'btn-outline'}`}
            style={{ padding: '0.35rem 0.85rem', fontSize: '0.78rem', border: 'none' }}
            onClick={() => setActiveTab('patient')}
            disabled={!selectedPatientId}
          >
            <ShieldCheck size={14} />
            {selectedPatientId ? `Patient Review` : `Patient Review`}
          </button>
        </div>

        {/* Search Bar */}
        <form onSubmit={onSearchSubmit} style={{ display: 'flex', alignItems: 'center', position: 'relative' }}>
          <input
            type="text"
            placeholder="Search Patient ID..."
            value={patientSearch}
            onChange={(e) => setPatientSearch(e.target.value)}
            style={{
              background: 'var(--bg-inset)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '0.4rem 0.75rem 0.4rem 2rem',
              color: 'var(--text-primary)',
              fontSize: '0.78rem',
              width: '230px',
              outline: 'none',
              fontFamily: 'var(--font-mono)'
            }}
          />
          <Search size={14} color="var(--text-muted)" style={{ position: 'absolute', left: '0.65rem' }} />
        </form>

        {/* Telemetry Pills */}
        <div className="telemetry-bar">
          <div className="telemetry-pill" title="FastAPI Health">
            <span className={getPillStatusClass(telemetry?.api)} />
            <Server size={12} />
            <span>API</span>
          </div>
          <div className="telemetry-pill" title="Neo4j Knowledge Graph">
            <span className={getPillStatusClass(telemetry?.neo4j)} />
            <Database size={12} />
            <span>Neo4j</span>
          </div>
          <div className="telemetry-pill" title="XGBoost & SHAP Inference">
            <span className={getPillStatusClass(telemetry?.model)} />
            <Cpu size={12} />
            <span>XGBoost</span>
          </div>
          <div className="telemetry-pill" title="Qdrant Vector Database">
            <span className={getPillStatusClass(telemetry?.qdrant)} />
            <Layers size={12} />
            <span>Qdrant</span>
          </div>
        </div>
      </div>
    </header>
  );
}
