import React, { useState } from 'react';
import { 
  FileText, 
  Send, 
  Sparkles, 
  AlertCircle, 
  RefreshCw, 
  Copy, 
  Check, 
  Code, 
  ChevronDown, 
  ChevronUp,
  Activity,
  ShieldCheck
} from 'lucide-react';

export default function ClinicalReport({ 
  report = '', 
  loading = false, 
  onRunQuery, 
  patientId 
}) {
  const [customQuery, setCustomQuery] = useState('');
  const [copied, setCopied] = useState(false);
  const [showPromptModal, setShowPromptModal] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!customQuery.trim() || loading) return;
    onRunQuery(customQuery);
  };

  const handleCopy = () => {
    if (!report) return;
    navigator.clipboard.writeText(report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Preset quick questions clinicians frequently ask
  const presetQueries = [
    "Evaluate cardiovascular risk and blood pressure targets",
    "Assess glycemic control and metformin dosing in CKD",
    "Review active medications for contraindications or drug interactions",
    "Provide monitoring timeline and follow-up priorities",
  ];

  // Robust inline markdown parser for **bold** text and code snippets
  const parseInline = (text) => {
    if (!text) return null;
    const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={i} style={{ color: '#ffffff', fontWeight: 600 }}>
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={i} style={{ 
            background: 'rgba(148, 163, 184, 0.15)', 
            padding: '0.1rem 0.35rem', 
            borderRadius: '3px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.85em',
            color: 'var(--accent-cyan-light)'
          }}>
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  // Structured parser that transforms Gemini output into clean clinical cards
  const renderFormattedReport = (rawText) => {
    if (!rawText) return <p style={{ color: 'var(--text-muted)' }}>No report generated yet. Select a patient or run an inquiry above.</p>;

    // Handle error stub or notice
    if (rawText.startsWith('[')) {
      return (
        <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.08)', borderLeft: '3px solid var(--risk-high)', borderRadius: 'var(--radius-sm)', color: '#fca5a5', fontSize: '0.8rem', lineHeight: 1.6 }}>
          <div style={{ fontWeight: 600, marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <AlertCircle size={15} />
            Clinical Report Notice
          </div>
          <div>{rawText}</div>
        </div>
      );
    }

    // Split text by lines
    const lines = rawText.split('\n');
    const sections = [];
    let currentSection = { title: null, number: null, lines: [] };

    lines.forEach((rawLine) => {
      const line = rawLine.trim();
      if (!line) return;

      // Detect header formats like:
      // ### 1. Patient Risk Summary
      // #### 2. Key Clinical Concerns
      // 1. **Patient Risk Summary**
      // ## Evidence-Based Recommendations
      const headerMatch = line.match(/^(?:#{1,4}\s*)?(?:(\d+)[\.\)]\s*)?(?:\*\*)?([A-Z0-9\s&/\-]+?)(?:\*\*)?:?$/i);
      const isExplicitHeader = line.startsWith('#') || /^\d+[\.\)]\s+\*\*/.test(line);

      if (isExplicitHeader) {
        if (currentSection.lines.length > 0 || currentSection.title) {
          sections.push(currentSection);
        }
        
        // Clean title
        let cleanTitle = line.replace(/^#+\s*/, '').replace(/^\d+[\.\)]\s*/, '').replace(/\*\*/g, '').replace(/:$/, '').trim();
        const numMatch = line.match(/(?:^#+\s*)?(\d+)[\.\)]/);
        const sectionNum = numMatch ? numMatch[1] : null;

        currentSection = {
          title: cleanTitle,
          number: sectionNum ? `0${sectionNum}` : null,
          lines: []
        };
      } else {
        currentSection.lines.push(line);
      }
    });

    if (currentSection.lines.length > 0 || currentSection.title) {
      sections.push(currentSection);
    }

    // If no explicit sections were parsed, render line-by-line fallback
    if (sections.length === 0 || (sections.length === 1 && !sections[0].title)) {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', color: '#e2e8f0', fontSize: '0.84rem', lineHeight: 1.65 }}>
          {lines.map((l, idx) => {
            const t = l.trim();
            if (!t) return null;
            if (t.startsWith('- ') || t.startsWith('* ')) {
              return (
                <div key={idx} style={{ display: 'flex', gap: '0.5rem', paddingLeft: '0.5rem' }}>
                  <span style={{ color: 'var(--accent-cyan)' }}>•</span>
                  <span>{parseInline(t.substring(2))}</span>
                </div>
              );
            }
            return <p key={idx} style={{ margin: 0 }}>{parseInline(t)}</p>;
          })}
        </div>
      );
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {sections.map((sec, sIdx) => {
          return (
            <div 
              key={sIdx} 
              style={{
                background: 'rgba(15, 23, 42, 0.55)',
                border: '1px solid rgba(51, 65, 85, 0.5)',
                borderRadius: 'var(--radius-md)',
                padding: '0.9rem 1.1rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.65rem'
              }}
            >
              {sec.title && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', borderBottom: '1px solid rgba(51, 65, 85, 0.4)', paddingBottom: '0.45rem' }}>
                  {sec.number && (
                    <span style={{
                      background: 'rgba(14, 165, 233, 0.15)',
                      color: 'var(--accent-cyan-light)',
                      border: '1px solid rgba(14, 165, 233, 0.3)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '0.1rem 0.4rem',
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      fontFamily: 'var(--font-mono)'
                    }}>
                      {sec.number}
                    </span>
                  )}
                  <h4 style={{ 
                    color: 'var(--accent-cyan-light)', 
                    fontSize: '0.85rem', 
                    fontWeight: 600, 
                    letterSpacing: '0.02em',
                    margin: 0,
                    textTransform: 'uppercase'
                  }}>
                    {sec.title}
                  </h4>
                </div>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', color: '#e2e8f0', fontSize: '0.835rem', lineHeight: 1.65 }}>
                {sec.lines.map((line, lIdx) => {
                  if (line.startsWith('- ') || line.startsWith('* ')) {
                    const bulletText = line.substring(2).trim();
                    return (
                      <div key={lIdx} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.55rem', paddingLeft: '0.25rem' }}>
                        <span style={{ color: 'var(--accent-teal)', fontSize: '0.9rem', lineHeight: '1.2' }}>•</span>
                        <div style={{ flex: 1 }}>{parseInline(bulletText)}</div>
                      </div>
                    );
                  }
                  return (
                    <p key={lIdx} style={{ margin: 0 }}>
                      {parseInline(line)}
                    </p>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="clinical-card">
      {/* Header */}
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="card-title">
          <FileText size={16} color="var(--accent-cyan)" />
          Synthesized Decision Support Briefing
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button 
            className="btn btn-outline"
            style={{ padding: '0.2rem 0.55rem', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
            onClick={() => setShowPromptModal(true)}
            title="Inspect the complete clinical prompt template sent to Gemini"
          >
            <Code size={13} color="var(--accent-cyan)" />
            <span>Prompt Blueprint</span>
          </button>
          
          {report && !report.startsWith('[') && (
            <button 
              className="btn btn-outline"
              style={{ padding: '0.2rem 0.55rem', fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
              onClick={handleCopy}
              title="Copy synthesized report"
            >
              {copied ? <Check size={13} color="var(--risk-low)" /> : <Copy size={13} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          )}

          <span className="badge badge-cyan">LangGraph Agent Pipeline</span>
        </div>
      </div>

      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        
        {/* Report Content Panel with custom scroll */}
        <div style={{ 
          background: 'var(--bg-inset)', 
          padding: '1.25rem', 
          borderRadius: 'var(--radius-md)', 
          border: '1px solid var(--border-subtle)', 
          minHeight: '200px',
          maxHeight: '440px',
          overflowY: 'auto'
        }}>
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '180px', gap: '0.75rem', color: 'var(--accent-cyan-light)' }}>
              <RefreshCw size={24} className="spin" style={{ animation: 'spin 1.2s linear infinite' }} />
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  Synthesizing Multimodal Evidence...
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  Aggregating Neo4j Knowledge Graph, XGBoost risk probabilities, and Qdrant RAG guidelines
                </div>
              </div>
            </div>
          ) : (
            renderFormattedReport(report)
          )}
        </div>

        {/* Quick Clinical Questions */}
        <div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.5rem', fontWeight: 600 }}>
            Targeted Clinical Inquiries
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            {presetQueries.map((q, i) => (
              <button
                key={i}
                className="btn btn-outline"
                style={{ padding: '0.25rem 0.6rem', fontSize: '0.72rem', borderRadius: 'var(--radius-sm)' }}
                onClick={() => {
                  setCustomQuery(q);
                  onRunQuery(q);
                }}
                disabled={loading}
              >
                <span>{q}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Interactive Query Input */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            type="text"
            placeholder="Ask a specific clinical decision question for this patient..."
            value={customQuery}
            onChange={(e) => setCustomQuery(e.target.value)}
            disabled={loading}
            style={{
              flex: 1,
              background: 'var(--bg-inset)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '0.55rem 0.85rem',
              color: 'var(--text-primary)',
              fontSize: '0.8rem',
              outline: 'none',
              fontFamily: 'var(--font-sans)',
            }}
          />
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={loading || !customQuery.trim()}
            style={{ padding: '0.55rem 1rem' }}
          >
            <Send size={14} />
            <span>Generate Analysis</span>
          </button>
        </form>
      </div>

      {/* Prompt Blueprint Modal (For Review & Academic Presentation) */}
      {showPromptModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '1.5rem'
        }}>
          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-highlight)',
            borderRadius: 'var(--radius-lg)',
            maxWidth: '820px',
            width: '100%',
            maxHeight: '85vh',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: 'var(--shadow-lg)'
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '1.2rem 1.5rem',
              borderBottom: '1px solid var(--border-subtle)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <ShieldCheck size={20} color="var(--accent-cyan)" />
                <div>
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                    Clinical Prompt Architecture & Blueprint
                  </h3>
                  <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                    Exact Gemini prompt template and multi-agent synthesis injection schema
                  </div>
                </div>
              </div>
              <button 
                className="btn btn-outline" 
                style={{ padding: '0.3rem 0.7rem', fontSize: '0.75rem' }}
                onClick={() => setShowPromptModal(false)}
              >
                Close
              </button>
            </div>

            {/* Modal Content */}
            <div style={{ padding: '1.25rem 1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.8rem', color: '#cbd5e1' }}>
              <div>
                <span style={{ fontWeight: 600, color: 'var(--accent-teal)' }}>Core Design Principle: </span>
                The LLM (Gemini) is strictly a <strong>synthesis and natural language generation layer</strong>. It does <em>not</em> perform ungrounded diagnostics or medical guessing. All medical facts are hard-grounded from upstream nodes (Neo4j Graph, XGBoost ML with SHAP explanations, and Qdrant RAG vector clinical guidelines).
              </div>

              <div style={{ 
                background: 'var(--bg-inset)', 
                border: '1px solid var(--border-subtle)', 
                borderRadius: 'var(--radius-md)', 
                padding: '1rem',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.74rem',
                lineHeight: 1.6,
                color: '#94a3b8',
                whiteSpace: 'pre-wrap'
              }}>
{`You are MedGraph AI, an advanced clinical decision support system. Based on the structured patient data, predictive ML risk assessment, and clinical guideline evidence below, generate an evidence-grounded, professional clinical decision briefing for an attending physician.

CRITICAL INSTRUCTIONS:
- Do NOT diagnose or prescribe directly. Provide objective analytical synthesis, highlight risk factors, and reference clinical guidelines.
- Maintain professional, clinical-grade medical terminology.
- Complete all sections fully. Do not truncate, omit sections, or stop mid-sentence.
- Strictly format your entire output using the exact 4 markdown sections specified below.

==================================================
PATIENT DEMOGRAPHIC & CLINICAL PROFILE
==================================================
Age: {patient.age} years | Gender: {patient.gender} | Race: {patient.race}
Location: {patient.city}, {patient.state}
Total Encounters: {summary.total_encounters} | Total Active Diagnoses: {summary.total_conditions}

ACTIVE CONDITIONS:
{condition_name} (onset: {onset_date}) ...

CURRENT MEDICATIONS:
{medication_name} ...

==================================================
PREDICTIVE ML RISK ASSESSMENT (XGBoost + SHAP)
==================================================
Calculated Risk Status: {HIGH RISK | LOW RISK}
Model Probability: {risk_percentage}%

Top SHAP Clinical Feature Attribution Drivers:
  - {feature_name} (value: {val}) -> {increases/reduces risk} (SHAP impact: {shap_val})

==================================================
RETRIEVED CLINICAL GUIDELINE EVIDENCE (RAG)
==================================================
[1] Guideline Source: {source} (relevance score: {score}):
{guideline_clinical_text}...

==================================================
FOCUSED CLINICAL INQUIRY
==================================================
{clinical_question}

==================================================
REQUIRED OUTPUT FORMAT
==================================================
Generate the briefing strictly following this 4-part structure without conversational preamble:

### 1. Patient Risk Summary
Provide a 2-3 sentence clinical summary explaining the patient's predicted risk score and the primary demographic or physiological factors driving it.

### 2. Key Clinical Concerns
Provide 3-4 bullet points (- ) highlighting active comorbidities, medication considerations, or elevated biomarkers.

### 3. Evidence-Based Recommendations
Provide 2-3 guideline-backed recommendations (- ) referencing the retrieved evidence regarding target biomarkers, lifestyle, or clinical considerations.

### 4. Monitoring & Follow-Up Priorities
Provide 2-3 actionable bullet points (- ) specifying monitoring intervals (e.g., HbA1c, eGFR, BP) and prioritized next clinical steps.`}
              </div>
            </div>
          </div>
        </div>
      )}
      
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

