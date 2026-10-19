import React, { useState } from 'react';
import { Search, Filter, ShieldAlert, CheckCircle, ChevronRight, ArrowUpDown } from 'lucide-react';

export default function PatientRegistry({ 
  patients = [], 
  total = 0, 
  loading = false, 
  selectedPatientId, 
  onSelectPatient,
  currentFilter,
  onFilterChange,
  searchTerm,
  onSearchChange,
  page = 0,
  onPageChange
}) {
  const pageSize = 25;
  const totalPages = Math.ceil(total / pageSize) || 1;

  const filters = [
    { id: 'all', label: 'All Patients' },
    { id: 'high_risk', label: 'High Risk Alert' },
    { id: 'diabetes', label: 'Diabetes' },
    { id: 'hypertension', label: 'Hypertension' },
    { id: 'ckd', label: 'Chronic Kidney Disease' },
    { id: 'heart_failure', label: 'Heart Failure' },
  ];

  return (
    <div className="clinical-card">
      <div className="card-header">
        <div className="card-title">
          <Filter size={16} color="var(--accent-cyan)" />
          Patient Registry & Cohort Stratification
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span className="badge badge-neutral tabular-nums">
            Showing {patients.length} of {total.toLocaleString()} patients
          </span>
        </div>
      </div>

      <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border-subtle)', display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(15, 23, 42, 0.2)' }}>
        {/* Preset Filter Pills */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
          {filters.map((f) => (
            <button
              key={f.id}
              className={`btn ${currentFilter === f.id ? 'btn-primary' : 'btn-outline'}`}
              style={{ padding: '0.3rem 0.65rem', fontSize: '0.75rem' }}
              onClick={() => onFilterChange(f.id)}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Search Field */}
        <div style={{ position: 'relative', width: '260px' }}>
          <input
            type="text"
            placeholder="Filter patient ID..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            style={{
              width: '100%',
              background: 'var(--bg-inset)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '0.4rem 0.75rem 0.4rem 2rem',
              color: 'var(--text-primary)',
              fontSize: '0.78rem',
              fontFamily: 'var(--font-mono)',
              outline: 'none',
            }}
          />
          <Search size={14} color="var(--text-muted)" style={{ position: 'absolute', left: '0.65rem', top: '50%', transform: 'translateY(-50%)' }} />
        </div>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto', minHeight: '380px' }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Loading patient records from feature store...
          </div>
        ) : patients.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No patient records match the selected filter criteria.
          </div>
        ) : (
          <table className="clinical-table">
            <thead>
              <tr>
                <th>Patient ID</th>
                <th>Demographics</th>
                <th>Conditions Detected</th>
                <th>Encounters</th>
                <th>Medications</th>
                <th>Risk Tier</th>
                <th style={{ textAlign: 'right' }}>Clinical Action</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((p) => {
                const isSelected = p.patient_id === selectedPatientId;
                return (
                  <tr 
                    key={p.patient_id}
                    className={isSelected ? 'selected' : ''}
                    onClick={() => onSelectPatient(p.patient_id)}
                  >
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--accent-cyan-light)', fontSize: '0.78rem' }}>
                      {p.patient_id.substring(0, 13)}...
                    </td>
                    <td>
                      <span className="tabular-nums" style={{ fontWeight: 600 }}>{p.age ?? '—'}y</span>
                      <span style={{ color: 'var(--text-muted)', margin: '0 0.35rem' }}>/</span>
                      <span>{p.gender}</span>
                      <span style={{ color: 'var(--text-muted)', margin: '0 0.35rem' }}>/</span>
                      <span style={{ color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{p.race}</span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', alignItems: 'center' }}>
                        {p.has_diabetes && <span className="badge badge-neutral" style={{ fontSize: '0.65rem' }}>DM</span>}
                        {p.has_hypertension && <span className="badge badge-neutral" style={{ fontSize: '0.65rem' }}>HTN</span>}
                        {p.has_ckd && <span className="badge badge-high" style={{ fontSize: '0.65rem' }}>CKD</span>}
                        {p.has_heart_failure && <span className="badge badge-high" style={{ fontSize: '0.65rem' }}>HF</span>}
                        {p.has_copd && <span className="badge badge-neutral" style={{ fontSize: '0.65rem' }}>COPD</span>}
                        {!p.has_diabetes && !p.has_hypertension && !p.has_ckd && !p.has_heart_failure && !p.has_copd && (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>None recorded</span>
                        )}
                      </div>
                    </td>
                    <td className="tabular-nums" style={{ color: 'var(--text-secondary)' }}>{p.total_encounters}</td>
                    <td className="tabular-nums" style={{ color: 'var(--text-secondary)' }}>{p.total_medications}</td>
                    <td>
                      {p.is_high_risk ? (
                        <span className="badge badge-high">
                          <ShieldAlert size={12} />
                          High Risk
                        </span>
                      ) : (
                        <span className="badge badge-low">
                          <CheckCircle size={12} />
                          Low Risk
                        </span>
                      )}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        className="btn btn-outline"
                        style={{ padding: '0.25rem 0.6rem', fontSize: '0.72rem' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectPatient(p.patient_id);
                        }}
                      >
                        <span>Review</span>
                        <ChevronRight size={13} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination Bar */}
      <div style={{ padding: '0.75rem 1.25rem', borderTop: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-secondary)', background: 'rgba(15, 23, 42, 0.3)' }}>
        <div>
          Page <span className="tabular-nums" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{page + 1}</span> of <span className="tabular-nums">{totalPages}</span>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            className="btn btn-outline"
            style={{ padding: '0.25rem 0.65rem', fontSize: '0.75rem' }}
            disabled={page === 0 || loading}
            onClick={() => onPageChange(page - 1)}
          >
            Previous
          </button>
          <button
            className="btn btn-outline"
            style={{ padding: '0.25rem 0.65rem', fontSize: '0.75rem' }}
            disabled={page >= totalPages - 1 || loading}
            onClick={() => onPageChange(page + 1)}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
