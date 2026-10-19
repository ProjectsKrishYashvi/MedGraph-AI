import React from 'react';
import { User, MapPin, Calendar, HeartPulse, Activity, Pill, Stethoscope, Copy, Check } from 'lucide-react';

export default function PatientProfileCard({ patient, summary }) {
  const [copied, setCopied] = React.useState(false);

  if (!patient) return null;

  const handleCopy = () => {
    if (patient.patient_id) {
      navigator.clipboard.writeText(patient.patient_id);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  return (
    <div className="clinical-card">
      <div className="card-header">
        <div className="card-title">
          <User size={16} color="var(--accent-cyan)" />
          Patient Master Profile
        </div>
        <button 
          className="btn btn-outline" 
          style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }}
          onClick={handleCopy}
          title="Copy Patient ID"
        >
          {copied ? <Check size={12} color="var(--risk-low)" /> : <Copy size={12} />}
          <span>{copied ? 'Copied' : 'Copy ID'}</span>
        </button>
      </div>
      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        
        {/* Top Demographics Bar */}
        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--accent-cyan-light)', marginBottom: '0.35rem', wordBreak: 'break-all' }}>
            ID: {patient.patient_id}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', fontSize: '0.85rem' }}>
            <span style={{ fontWeight: 700, color: '#ffffff' }} className="tabular-nums">
              {patient.age ? `${patient.age} years` : 'Age unknown'}
            </span>
            <span style={{ color: 'var(--text-muted)' }}>•</span>
            <span style={{ color: 'var(--text-secondary)' }}>{patient.gender === 'F' ? 'Female' : patient.gender === 'M' ? 'Male' : patient.gender}</span>
            <span style={{ color: 'var(--text-muted)' }}>•</span>
            <span style={{ color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{patient.race}</span>
            {patient.city && (
              <>
                <span style={{ color: 'var(--text-muted)' }}>•</span>
                <span style={{ color: 'var(--text-secondary)', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                  <MapPin size={12} /> {patient.city}, {patient.state}
                </span>
              </>
            )}
          </div>
        </div>

        {/* Clinical Utilization Metric Counters */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem', background: 'var(--bg-inset)', padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem', fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.2rem' }}>
              <Activity size={12} color="var(--accent-cyan)" />
              Visits
            </div>
            <div className="tabular-nums" style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {summary?.total_encounters ?? 0}
            </div>
          </div>

          <div style={{ textAlign: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem', fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.2rem' }}>
              <HeartPulse size={12} color="var(--accent-teal)" />
              Diagnoses
            </div>
            <div className="tabular-nums" style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {summary?.total_conditions ?? 0}
            </div>
          </div>

          <div style={{ textAlign: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem', fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.2rem' }}>
              <Pill size={12} color="var(--risk-mod)" />
              Meds
            </div>
            <div className="tabular-nums" style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {summary?.total_medications ?? 0}
            </div>
          </div>

          <div style={{ textAlign: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.25rem', fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.2rem' }}>
              <Stethoscope size={12} color="var(--accent-cyan-light)" />
              Procedures
            </div>
            <div className="tabular-nums" style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {summary?.total_procedures ?? 0}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
