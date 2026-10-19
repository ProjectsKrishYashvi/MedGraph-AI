import React from 'react';
import { Users, AlertTriangle, Calendar, Activity, BarChart3, ArrowRight } from 'lucide-react';

export default function PopulationOverview({ stats, onSelectConditionFilter, onViewRegistry }) {
  if (!stats) return null;

  const total = stats.total_patients || 1163;
  const conditions = stats.condition_prevalence || {};

  const conditionList = Object.entries(conditions).map(([name, count]) => ({
    name,
    count,
    percentage: Math.round((count / total) * 100 * 10) / 10,
  })).sort((a, b) => b.count - a.count);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">
            <span>Total Monitored Cohort</span>
            <Users size={16} color="var(--accent-cyan)" />
          </div>
          <div className="kpi-value tabular-nums">{total.toLocaleString()}</div>
          <div className="kpi-meta">Synthea Massachusetts Longitudinal Cohort</div>
        </div>

        <div className="kpi-card risk-accent">
          <div className="kpi-label">
            <span>High-Risk Readmission Rate</span>
            <AlertTriangle size={16} color="var(--risk-high)" />
          </div>
          <div className="kpi-value tabular-nums" style={{ color: 'var(--risk-high)' }}>
            {stats.high_risk_percentage}%
          </div>
          <div className="kpi-meta">
            <span className="tabular-nums" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
              {stats.high_risk_count}
            </span> of {total} patients classified high-risk
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">
            <span>Mean Patient Age</span>
            <Calendar size={16} color="var(--accent-teal)" />
          </div>
          <div className="kpi-value tabular-nums">{stats.avg_age} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>yrs</span></div>
          <div className="kpi-meta">Adult & Pediatric Multi-Generational Stratum</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">
            <span>Encounter Density</span>
            <Activity size={16} color="var(--accent-cyan)" />
          </div>
          <div className="kpi-value tabular-nums">{stats.avg_encounters}</div>
          <div className="kpi-meta">Average clinical visits per patient record</div>
        </div>
      </div>

      {/* Surveillance Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '1.25rem' }}>
        {/* Condition Prevalence */}
        <div className="clinical-card">
          <div className="card-header">
            <div className="card-title">
              <BarChart3 size={16} color="var(--accent-cyan)" />
              Chronic Comorbidity Surveillance
            </div>
            <span className="badge badge-neutral">Prevalence Analysis</span>
          </div>
          <div className="card-body">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {conditionList.map((item) => (
                <div 
                  key={item.name}
                  onClick={() => onSelectConditionFilter && onSelectConditionFilter(item.name)}
                  style={{ 
                    cursor: 'pointer',
                    padding: '0.4rem 0.5rem',
                    borderRadius: 'var(--radius-sm)',
                    transition: 'background 0.15s ease'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(30, 41, 59, 0.5)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  title={`Filter registry by ${item.name}`}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem', fontSize: '0.8rem' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{item.name}</span>
                    <div style={{ display: 'flex', gap: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                      <span style={{ color: 'var(--accent-cyan)' }} className="tabular-nums">{item.count} pts</span>
                      <span style={{ color: 'var(--text-muted)' }} className="tabular-nums">({item.percentage}%)</span>
                    </div>
                  </div>
                  <div style={{ height: '6px', background: 'var(--bg-inset)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div 
                      style={{ 
                        width: `${Math.min(item.percentage * 2, 100)}%`, 
                        height: '100%', 
                        background: item.percentage > 25 ? 'var(--accent-cyan)' : 'var(--accent-teal)',
                        borderRadius: '3px'
                      }} 
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Clinical Stratification Context */}
        <div className="clinical-card">
          <div className="card-header">
            <div className="card-title">
              <Activity size={16} color="var(--accent-teal)" />
              Clinical Risk Stratification Protocol
            </div>
          </div>
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.825rem', color: 'var(--text-secondary)' }}>
            <p>
              MedGraph AI leverages a dual-layer risk evaluation protocol:
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              <div style={{ padding: '0.65rem', background: 'var(--bg-inset)', borderLeft: '3px solid var(--risk-high)', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>Tier 1: High-Risk Alert (Readmission Probability &ge; 50%)</div>
                <div>Triggered by complex multimorbid conditions, high encounter density, abnormal glycemic/renal markers (HbA1c &gt; 8%, eGFR &lt; 60).</div>
              </div>
              <div style={{ padding: '0.65rem', background: 'var(--bg-inset)', borderLeft: '3px solid var(--risk-low)', borderRadius: 'var(--radius-sm)' }}>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>Tier 2: Standard Ambulatory Care (&lt; 50%)</div>
                <div>Patients with controlled vital signs, single chronic or uncomplicated health profiles. Recommended for routine preventive review.</div>
              </div>
            </div>
            <button 
              className="btn btn-primary"
              style={{ marginTop: '0.5rem', alignSelf: 'flex-start' }}
              onClick={onViewRegistry}
            >
              Browse Full Patient Registry
              <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
