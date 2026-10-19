import React, { useState } from 'react';
import { HeartPulse, Pill, Activity, Calendar, ShieldCheck, ChevronRight } from 'lucide-react';

export default function PatientGraphTimeline({ conditions = [], medications = [], encounters = [] }) {
  const [activeSubTab, setActiveSubTab] = useState('conditions');

  return (
    <div className="clinical-card">
      <div className="card-header">
        <div className="card-title">
          <Activity size={16} color="var(--accent-teal)" />
          Knowledge Graph Longitudinal Trajectory
        </div>
        
        <div style={{ display: 'flex', gap: '0.35rem', background: 'var(--bg-inset)', padding: '0.2rem', borderRadius: 'var(--radius-sm)' }}>
          <button
            className={`btn ${activeSubTab === 'conditions' ? 'btn-primary' : 'btn-outline'}`}
            style={{ padding: '0.2rem 0.55rem', fontSize: '0.72rem', border: 'none' }}
            onClick={() => setActiveSubTab('conditions')}
          >
            Diagnoses ({conditions.length})
          </button>
          <button
            className={`btn ${activeSubTab === 'medications' ? 'btn-primary' : 'btn-outline'}`}
            style={{ padding: '0.2rem 0.55rem', fontSize: '0.72rem', border: 'none' }}
            onClick={() => setActiveSubTab('medications')}
          >
            Medications ({medications.length})
          </button>
          <button
            className={`btn ${activeSubTab === 'encounters' ? 'btn-primary' : 'btn-outline'}`}
            style={{ padding: '0.2rem 0.55rem', fontSize: '0.72rem', border: 'none' }}
            onClick={() => setActiveSubTab('encounters')}
          >
            Encounters ({encounters.length})
          </button>
        </div>
      </div>

      <div className="card-body" style={{ maxHeight: '310px', overflowY: 'auto' }}>
        {/* Conditions */}
        {activeSubTab === 'conditions' && (
          <div>
            {conditions.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textAlign: 'center', padding: '1.5rem 0' }}>
                No active condition records found in Neo4j.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {conditions.map((c, i) => (
                  <div 
                    key={i} 
                    style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'space-between',
                      padding: '0.55rem 0.75rem',
                      background: 'var(--bg-inset)',
                      borderRadius: 'var(--radius-sm)',
                      borderLeft: '3px solid var(--accent-cyan)'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.8rem' }}>
                        {c.name || c.condition_name}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', gap: '0.5rem', marginTop: '0.15rem' }}>
                        {c.snomed_code && <span>SNOMED: {c.snomed_code}</span>}
                        {c.onset_date && <span>Onset: {c.onset_date.substring(0, 10)}</span>}
                      </div>
                    </div>
                    <span className="badge badge-neutral" style={{ fontSize: '0.65rem' }}>
                      {c.stop_date ? 'Resolved' : 'Active'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Medications */}
        {activeSubTab === 'medications' && (
          <div>
            {medications.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textAlign: 'center', padding: '1.5rem 0' }}>
                No current medication orders found in Neo4j.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {medications.map((m, i) => (
                  <div 
                    key={i} 
                    style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'space-between',
                      padding: '0.55rem 0.75rem',
                      background: 'var(--bg-inset)',
                      borderRadius: 'var(--radius-sm)',
                      borderLeft: '3px solid var(--accent-teal)'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.8rem' }}>
                        {m.name || m.medication_name}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'flex', gap: '0.5rem', marginTop: '0.15rem' }}>
                        {m.rxnorm_code && <span>RxNorm: {m.rxnorm_code}</span>}
                        {m.start_date && <span>Started: {m.start_date.substring(0, 10)}</span>}
                      </div>
                    </div>
                    <span className="badge badge-low" style={{ fontSize: '0.65rem' }}>
                      Prescribed
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Encounters */}
        {activeSubTab === 'encounters' && (
          <div>
            {encounters.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textAlign: 'center', padding: '1.5rem 0' }}>
                No recent clinical visits found in Neo4j.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {encounters.map((e, i) => (
                  <div 
                    key={i} 
                    style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'space-between',
                      padding: '0.55rem 0.75rem',
                      background: 'var(--bg-inset)',
                      borderRadius: 'var(--radius-sm)',
                      borderLeft: '3px solid var(--border-medium)'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.8rem', textTransform: 'capitalize' }}>
                        {e.encounter_type || 'Clinical Encounter'}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                        Date: {e.start_datetime ? e.start_datetime.substring(0, 10) : 'Recorded visit'}
                      </div>
                    </div>
                    <span className="badge badge-neutral" style={{ fontSize: '0.65rem' }}>
                      Visit #{i + 1}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
