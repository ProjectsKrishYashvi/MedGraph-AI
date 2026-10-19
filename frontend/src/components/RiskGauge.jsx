import React from 'react';
import { ShieldAlert, CheckCircle, Cpu, AlertCircle } from 'lucide-react';

export default function RiskGauge({ riskResult }) {
  if (!riskResult) {
    return (
      <div className="clinical-card" style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        No risk prediction computed yet.
      </div>
    );
  }

  const { risk_probability = 0, is_high_risk = false } = riskResult;
  const pct = Math.round(risk_probability * 1000) / 10; // e.g. 28.4%

  // Gauge calculation (semi-circle arc)
  const radius = 62;
  const circumference = Math.PI * radius;
  const strokeDashoffset = circumference - (risk_probability * circumference);

  const riskColor = is_high_risk ? 'var(--risk-high)' : 'var(--risk-low)';

  return (
    <div className="clinical-card">
      <div className="card-header">
        <div className="card-title">
          <Cpu size={16} color="var(--accent-cyan)" />
          XGBoost Risk Assessment
        </div>
        <span className="badge badge-neutral">Inference Model v1.0</span>
      </div>
      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.85rem' }}>
        
        {/* Arc Gauge */}
        <div style={{ position: 'relative', width: '160px', height: '95px', display: 'flex', justifyContent: 'center' }}>
          <svg width="160" height="95" viewBox="0 0 160 95" style={{ overflow: 'visible' }}>
            {/* Background Arc */}
            <path
              d="M 18 85 A 62 62 0 0 1 142 85"
              fill="none"
              stroke="var(--bg-inset)"
              strokeWidth="12"
              strokeLinecap="round"
            />
            {/* Value Arc */}
            <path
              d="M 18 85 A 62 62 0 0 1 142 85"
              fill="none"
              stroke={riskColor}
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              style={{ transition: 'stroke-dashoffset 0.8s ease-in-out' }}
            />
          </svg>
          <div style={{ position: 'absolute', bottom: '0px', textAlign: 'center' }}>
            <div className="tabular-nums" style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>
              {pct}%
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginTop: '0.2rem' }}>
              Readmission Probability
            </div>
          </div>
        </div>

        {/* Classification Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
          {is_high_risk ? (
            <div className="badge badge-high" style={{ fontSize: '0.8rem', padding: '0.35rem 0.8rem' }}>
              <ShieldAlert size={14} />
              High Risk Readmission Alert
            </div>
          ) : (
            <div className="badge badge-low" style={{ fontSize: '0.8rem', padding: '0.35rem 0.8rem' }}>
              <CheckCircle size={14} />
              Low Readmission Risk Tier
            </div>
          )}
        </div>

        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'center', maxWidth: '320px', lineHeight: 1.4 }}>
          Decision Threshold: <span className="tabular-nums" style={{ color: 'var(--text-secondary)' }}>0.50</span> (50%). 
          Validated across 1,163 longitudinal cohorts using 38 non-leaking features.
        </div>
      </div>
    </div>
  );
}
