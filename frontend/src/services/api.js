/**
 * MedGraph AI — Frontend API Client
 * Interfaces with FastAPI endpoints. Proxied via Vite /api -> http://localhost:8000
 */

const API_BASE = '/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchPopulationStats() {
  const res = await fetch(`${API_BASE}/population/stats`);
  if (!res.ok) throw new Error(`Failed to load population stats: ${res.statusText}`);
  return res.json();
}

export async function fetchPatients({ limit = 50, offset = 0, search = '', isHighRisk = null, condition = '' } = {}) {
  const params = new URLSearchParams();
  if (limit) params.set('limit', limit);
  if (offset) params.set('offset', offset);
  if (search) params.set('search', search);
  if (isHighRisk !== null && isHighRisk !== undefined) params.set('is_high_risk', isHighRisk);
  if (condition) params.set('condition', condition);

  const res = await fetch(`${API_BASE}/patients?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to load patients: ${res.statusText}`);
  return res.json();
}

export async function fetchPatientProfile(patientId) {
  const res = await fetch(`${API_BASE}/patients/${encodeURIComponent(patientId)}`);
  if (!res.ok) throw new Error(`Failed to load patient profile: ${res.statusText}`);
  return res.json();
}

export async function predictPatientRisk(patientId) {
  const res = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ patient_id: patientId }),
  });
  if (!res.ok) throw new Error(`Prediction failed: ${res.statusText}`);
  return res.json();
}

export async function fetchPatientInsights(patientId, query = '') {
  const body = { patient_id: patientId };
  if (query && query.trim()) {
    body.query = query.trim();
  }

  const res = await fetch(`${API_BASE}/insights`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Insights generation failed: ${res.statusText}`);
  return res.json();
}
