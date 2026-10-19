import React from 'react';
import { BookOpen, CheckCircle, ExternalLink, ShieldCheck } from 'lucide-react';

export default function GuidelineEvidence({ guidelines = [] }) {
  if (!guidelines || guidelines.length === 0) {
    return (
      <div className="clinical-card">
        <div className="card-header">
          <div className="card-title">
            <BookOpen size={16} color="var(--accent-teal)" />
            Clinical Guideline Evidence (RAG)
          </div>
        </div>
        <div className="card-body" style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textAlign: 'center' }}>
          No clinical guideline evidence retrieved for this patient profile.
        </div>
      </div>
    );
  }

  return (
    <div className="clinical-card">
      <div className="card-header">
        <div className="card-title">
          <BookOpen size={16} color="var(--accent-teal)" />
          Evidence-Based Clinical Guidelines (RAG)
        </div>
        <span className="badge badge-neutral tabular-nums">
          {guidelines.length} Guideline Passages Retrieved
        </span>
      </div>

      <div className="card-body">
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.85rem' }}>
          Semantically matched against WHO PEN, KDIGO CKD 2024, and ADA Standards of Care via Qdrant vector store:
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {guidelines.map((g, idx) => {
            const scorePct = Math.round(g.score * 1000) / 10;
            return (
              <div key={idx} className="guideline-card">
                <div className="guideline-source-row">
                  <div className="guideline-source">{g.source}</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span className="badge badge-cyan tabular-nums" style={{ fontSize: '0.7rem' }}>
                      Cosine Score: {g.score.toFixed(4)}
                    </span>
                  </div>
                </div>

                <div className="guideline-excerpt">
                  {g.text}
                </div>

                {g.condition_tags && g.condition_tags.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginTop: '0.35rem' }}>
                    {g.condition_tags.map((t, i) => (
                      <span key={i} className="badge badge-neutral" style={{ fontSize: '0.65rem' }}>
                        #{t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
