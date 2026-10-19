import React from 'react';
import { Sliders, ArrowUpRight, ArrowDownRight, Info } from 'lucide-react';

export default function SHAPContributors({ contributions = [] }) {
  if (!contributions || contributions.length === 0) {
    return (
      <div className="clinical-card">
        <div className="card-header">
          <div className="card-title">
            <Sliders size={16} color="var(--accent-cyan)" />
            SHAP Explainability Factors
          </div>
        </div>
        <div className="card-body" style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textAlign: 'center' }}>
          No SHAP explanations available for this prediction.
        </div>
      </div>
    );
  }

  // Find max absolute shap value to scale bars proportionally
  const maxShap = Math.max(...contributions.map(c => Math.abs(c.shap_value)), 0.1);

  return (
    <div className="clinical-card">
      <div className="card-header">
        <div className="card-title">
          <Sliders size={16} color="var(--accent-cyan)" />
          SHAP Feature Attributions
        </div>
        <span className="badge badge-neutral">TreeSHAP Engine</span>
      </div>
      <div className="card-body">
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.85rem' }}>
          Key clinical features influencing this patient's calculated risk score:
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {contributions.map((item, idx) => {
            const isIncrease = item.direction === 'increases_risk';
            const absVal = Math.abs(item.shap_value);
            const barWidth = Math.min(Math.round((absVal / maxShap) * 100), 100);

            // Format feature name to look clinical
            const cleanName = item.feature
              .replace(/^latest_/, 'Latest ')
              .replace(/^has_/, 'Diagnosis: ')
              .replace(/_/g, ' ');

            return (
              <div key={idx} className="shap-item">
                <div className="shap-header">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    {isIncrease ? (
                      <ArrowUpRight size={14} color="var(--risk-high)" />
                    ) : (
                      <ArrowDownRight size={14} color="var(--risk-low)" />
                    )}
                    <span className="shap-name" style={{ textTransform: 'capitalize', fontSize: '0.78rem' }}>
                      {cleanName}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {item.feature_value !== null && item.feature_value !== undefined && (
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                        val: <strong style={{ color: 'var(--text-primary)' }}>{item.feature_value}</strong>
                      </span>
                    )}
                    <span 
                      className="shap-metric tabular-nums" 
                      style={{ color: isIncrease ? 'var(--risk-high)' : 'var(--risk-low)' }}
                    >
                      {item.shap_value > 0 ? `+${item.shap_value.toFixed(3)}` : item.shap_value.toFixed(3)}
                    </span>
                  </div>
                </div>

                <div className="shap-bar-track">
                  <div
                    className={`shap-bar-fill ${isIncrease ? 'increase' : 'decrease'}`}
                    style={{ width: `${barWidth}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        <div style={{ marginTop: '0.85rem', paddingTop: '0.65rem', borderTop: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <span style={{ width: '8px', height: '8px', background: 'var(--risk-high)', borderRadius: '2px' }} />
            Increases Readmission Probability
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <span style={{ width: '8px', height: '8px', background: 'var(--risk-low)', borderRadius: '2px' }} />
            Protective / Lowers Probability
          </span>
        </div>
      </div>
    </div>
  );
}
