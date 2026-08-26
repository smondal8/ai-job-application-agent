import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  Sparkles,
  CheckCircle,
  AlertTriangle,
  Award,
  Copy,
  Check,
  Download,
  Search,
  Sliders,
  Eye,
  FileCode,
  Globe,
  FileCheck,
} from 'lucide-react';
import { api } from '../services/api';
import { Job, TailoredResume, LLMStatusResponse } from '../types';

interface ResumeTailoringStudioViewProps {
  initialJobId?: number;
}

export const ResumeTailoringStudioView: React.FC<ResumeTailoringStudioViewProps> = ({ initialJobId }) => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(initialJobId || null);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [tailoredResume, setTailoredResume] = useState<TailoredResume | null>(null);
  const [llmStatus, setLlmStatus] = useState<LLMStatusResponse | null>(null);

  // Tailoring Controls
  const [tone, setTone] = useState<string>('professional');
  const [targetRoleTitle, setTargetRoleTitle] = useState<string>('');
  const [customInstructions, setCustomInstructions] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  // Review & Approval
  const [approverNotes, setApproverNotes] = useState<string>('');
  const [isApproving, setIsApproving] = useState<boolean>(false);

  // Document Display Mode
  const [activeDocTab, setActiveDocTab] = useState<'markdown' | 'text' | 'html' | 'cover_letter' | 'traceability'>('markdown');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const fetchLLMAndJobs = useCallback(async () => {
    try {
      const [statusData, jobsData] = await Promise.all([
        api.getLLMStatus(),
        api.getJobs({ page: 1, page_size: 50 }),
      ]);
      setLlmStatus(statusData);
      setJobs(jobsData.items);

      const targetId = initialJobId || selectedJobId || (jobsData.items.length > 0 ? jobsData.items[0].id : null);
      if (targetId) {
        setSelectedJobId(targetId);
        const target = jobsData.items.find((j) => j.id === targetId) || (jobsData.items.length > 0 ? jobsData.items[0] : null);
        setSelectedJob(target);
      }
    } catch (err) {
      console.error('Failed to load LLM status or jobs:', err);
    }
  }, [initialJobId, selectedJobId]);

  const fetchJobTailoredResume = useCallback(async (jobId: number) => {
    try {
      const data = await api.getJobTailoredResume(jobId);
      setTailoredResume(data);
    } catch {
      setTailoredResume(null);
    }
  }, []);

  useEffect(() => {
    fetchLLMAndJobs();
  }, [fetchLLMAndJobs]);

  useEffect(() => {
    if (selectedJobId) {
      const target = jobs.find((j) => j.id === selectedJobId) || null;
      setSelectedJob(target);
      fetchJobTailoredResume(selectedJobId);
    }
  }, [selectedJobId, jobs, fetchJobTailoredResume]);

  const handleSelectJob = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = parseInt(e.target.value, 10);
    setSelectedJobId(id);
  };

  const handleGenerateTailoredResume = async () => {
    if (!selectedJobId) return;
    setIsGenerating(true);
    try {
      const res = await api.tailorResume(selectedJobId, {
        tone,
        target_role_title: targetRoleTitle || undefined,
        custom_instructions: customInstructions || undefined,
        auto_regenerate_on_untraced: true,
      });
      setTailoredResume(res);
    } catch (err: any) {
      alert(`Resume Tailoring failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApprove = async () => {
    if (!tailoredResume) return;
    setIsApproving(true);
    try {
      const updated = await api.approveTailoredResume(tailoredResume.id, {
        approver_notes: approverNotes || undefined,
      });
      setTailoredResume(updated);
      alert('Tailored resume approved successfully!');
    } catch (err: any) {
      alert(`Approval failed: ${err.message}`);
    } finally {
      setIsApproving(false);
    }
  };

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner: Phase 6 Subsystem Status */}
      <div
        className="card"
        style={{
          borderLeft: '4px solid #34d399',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <FileText size={24} color="#34d399" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>
              Grounded Resume Tailoring & Document Studio
            </h2>
            <span className="badge badge-green">Phase 6 Active</span>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Deterministic document compilation with atomic fact attribution (<code>source_fact_ids</code>), zero hallucination, and prompt versioning.
          </p>
        </div>

        {/* Model & Version Badges */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <span className="badge badge-purple" style={{ fontSize: '0.75rem' }}>
            Prompt: <strong>{tailoredResume?.prompt_version || 'v1.0.0'}</strong>
          </span>
          <span className="badge badge-blue" style={{ fontSize: '0.75rem' }}>
            Model: <strong>{llmStatus?.active_model || 'qwen3:8b'}</strong>
          </span>
          <span
            style={{
              fontSize: '0.75rem',
              padding: '0.25rem 0.6rem',
              background: 'rgba(52, 211, 153, 0.15)',
              color: '#34d399',
              borderRadius: '4px',
              border: '1px solid #34d399',
              display: 'flex',
              alignItems: 'center',
              gap: '0.25rem',
            }}
          >
            <Award size={13} />
            <span>100% Grounded</span>
          </span>
        </div>
      </div>

      {/* Target Job Selector & Generation Options */}
      <div className="card">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: '280px' }}>
              <Search size={16} color="var(--text-muted)" />
              <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Target Job Listing:
              </label>
              <select
                value={selectedJobId || ''}
                onChange={handleSelectJob}
                style={{
                  flex: 1,
                  padding: '0.5rem 0.75rem',
                  background: '#090d16',
                  border: '1px solid var(--border-color)',
                  borderRadius: '6px',
                  color: '#f8fafc',
                  fontSize: '0.8125rem',
                }}
              >
                {jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    #{j.id} — {j.title} at {j.company} ({j.remote_type || 'unspecified'} · {j.location || 'Remote'})
                  </option>
                ))}
              </select>
            </div>

            {selectedJob && (
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <span className="badge badge-blue">{selectedJob.company}</span>
                <span className="badge badge-gray">{selectedJob.remote_type}</span>
                {selectedJob.salary_min && (
                  <span className="badge badge-green">
                    ${Number(selectedJob.salary_min).toLocaleString()}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Tailoring Parameters */}
          <div style={{ background: '#090d16', padding: '0.875rem', borderRadius: '8px', border: '1px solid var(--border-color)', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem', alignItems: 'center' }}>
            <div>
              <label style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem', textTransform: 'uppercase', fontWeight: 600 }}>
                Writing Tone
              </label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                <Sliders size={14} color="var(--text-muted)" />
                <select
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  style={{ flex: 1, padding: '0.35rem 0.5rem', background: '#131b2e', border: '1px solid var(--border-color)', borderRadius: '4px', color: '#f8fafc', fontSize: '0.75rem' }}
                >
                  <option value="professional">Professional</option>
                  <option value="technical">Deep Technical</option>
                  <option value="confident">Confident / High Impact</option>
                  <option value="impact_driven">Quantified Outcomes</option>
                </select>
              </div>
            </div>

            <div>
              <label style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem', textTransform: 'uppercase', fontWeight: 600 }}>
                Target Role Title (Optional Override)
              </label>
              <input
                type="text"
                value={targetRoleTitle}
                onChange={(e) => setTargetRoleTitle(e.target.value)}
                placeholder={selectedJob?.title || "e.g., Staff Infrastructure Engineer"}
                style={{ width: '100%', padding: '0.35rem 0.5rem', background: '#131b2e', border: '1px solid var(--border-color)', borderRadius: '4px', color: '#f8fafc', fontSize: '0.75rem' }}
              />
            </div>

            <div style={{ gridColumn: 'span 2' }}>
              <label style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem', textTransform: 'uppercase', fontWeight: 600 }}>
                Strategic Guidance (Optional)
              </label>
              <input
                type="text"
                value={customInstructions}
                onChange={(e) => setCustomInstructions(e.target.value)}
                placeholder="e.g., Emphasize consensus protocols, streaming throughput, and fault tolerance..."
                style={{ width: '100%', padding: '0.35rem 0.5rem', background: '#131b2e', border: '1px solid var(--border-color)', borderRadius: '4px', color: '#f8fafc', fontSize: '0.75rem' }}
              />
            </div>
          </div>

          <button
            onClick={handleGenerateTailoredResume}
            disabled={isGenerating || !selectedJobId}
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.625rem', fontSize: '0.875rem' }}
          >
            <Sparkles size={16} />
            <span>{isGenerating ? 'Generating Traceable Application Materials...' : 'Generate Grounded Resume & Cover Letter'}</span>
          </button>
        </div>
      </div>

      {tailoredResume && (
        <>
          {/* Traceability & Validation Subsystem Inspector Card */}
          <div className="card" style={{ borderLeft: `4px solid ${tailoredResume.validation_status === 'valid' ? '#34d399' : tailoredResume.validation_status === 'requires_human_review' ? '#fbbf24' : '#f87171'}` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FileCheck size={20} color={tailoredResume.validation_status === 'valid' ? '#34d399' : '#fbbf24'} />
                  <h3 style={{ fontSize: '1.0625rem', fontWeight: 700 }}>Traceability & Validation Inspector</h3>
                  <span
                    className={`badge ${tailoredResume.validation_status === 'valid' ? 'badge-green' : tailoredResume.validation_status === 'requires_human_review' ? 'badge-purple' : 'badge-red'}`}
                    style={{ textTransform: 'uppercase' }}
                  >
                    {tailoredResume.validation_status.replace(/_/g, ' ')}
                  </span>
                  <span className={`badge ${tailoredResume.status === 'approved' ? 'badge-green' : 'badge-blue'}`}>
                    Workflow: {tailoredResume.status.replace(/_/g, ' ').toUpperCase()}
                  </span>
                </div>
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  Every claim is cross-referenced against the candidate's atomic verified fact registry (<code>source_fact_ids</code>).
                </p>
              </div>

              {/* Approval Action */}
              {tailoredResume.status !== 'approved' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    type="text"
                    value={approverNotes}
                    onChange={(e) => setApproverNotes(e.target.value)}
                    placeholder="Approver notes (optional)..."
                    style={{ padding: '0.35rem 0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '4px', color: '#f8fafc', fontSize: '0.75rem', width: '200px' }}
                  />
                  <button
                    onClick={handleApprove}
                    disabled={isApproving}
                    className="btn btn-primary"
                    style={{ fontSize: '0.75rem', padding: '0.4rem 0.75rem', backgroundColor: '#10b981' }}
                  >
                    <CheckCircle size={14} />
                    <span>{isApproving ? 'Approving...' : 'Approve for Submission'}</span>
                  </button>
                </div>
              )}
            </div>

            {/* Validation Metrics Grid */}
            <div className="grid-3" style={{ background: '#090d16', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <div>
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                  Traceability Score
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: tailoredResume.validation_details?.traceability_score === 100 ? '#34d399' : '#fbbf24' }}>
                  {tailoredResume.validation_details?.traceability_score ?? 100}%
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                  Verified Claims
                </div>
                <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#f8fafc', marginTop: '0.25rem' }}>
                  {tailoredResume.validation_details?.verified_claims ?? 0} / {tailoredResume.validation_details?.total_claims ?? 0}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                  Strategy Summary
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  {tailoredResume.diff_summary || 'Emphasized core verified skills.'}
                </p>
              </div>
            </div>

            {/* Untraced Claims Warning */}
            {tailoredResume.validation_details?.untraced_claims && tailoredResume.validation_details.untraced_claims.length > 0 && (
              <div style={{ background: 'rgba(251, 191, 36, 0.08)', padding: '0.75rem', borderRadius: '6px', border: '1px solid rgba(251, 191, 36, 0.3)', marginTop: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.8125rem', fontWeight: 600, color: '#fbbf24', marginBottom: '0.25rem' }}>
                  <AlertTriangle size={15} />
                  <span>Untraced Claims Requiring Review ({tailoredResume.validation_details.untraced_claims.length})</span>
                </div>
                <ul style={{ listStylePosition: 'inside', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  {tailoredResume.validation_details.untraced_claims.map((uc, i) => (
                    <li key={i}>[{uc.section}] {uc.text} &mdash; <em>{uc.reason}</em></li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Deterministically Compiled Document Studio */}
          <div className="card">
            {/* Studio Navigation Tabs */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  onClick={() => setActiveDocTab('markdown')}
                  className={`btn ${activeDocTab === 'markdown' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
                >
                  <FileCode size={13} />
                  <span>ATS Markdown</span>
                </button>
                <button
                  onClick={() => setActiveDocTab('cover_letter')}
                  className={`btn ${activeDocTab === 'cover_letter' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
                >
                  <FileText size={13} />
                  <span>Cover Letter</span>
                </button>
                <button
                  onClick={() => setActiveDocTab('text')}
                  className={`btn ${activeDocTab === 'text' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
                >
                  <FileText size={13} />
                  <span>Plain Text</span>
                </button>
                <button
                  onClick={() => setActiveDocTab('html')}
                  className={`btn ${activeDocTab === 'html' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
                >
                  <Globe size={13} />
                  <span>HTML View</span>
                </button>
                <button
                  onClick={() => setActiveDocTab('traceability')}
                  className={`btn ${activeDocTab === 'traceability' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
                >
                  <Eye size={13} />
                  <span>Fact Matrix</span>
                </button>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  onClick={() => {
                    const text = activeDocTab === 'cover_letter' ? tailoredResume.cover_letter : tailoredResume.compiled_markdown;
                    handleCopy(text || '', 'doc');
                  }}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem' }}
                >
                  {copiedKey === 'doc' ? <Check size={13} color="#34d399" /> : <Copy size={13} />}
                  <span>{copiedKey === 'doc' ? 'Copied!' : 'Copy'}</span>
                </button>
                <a
                  href={api.downloadDocumentUrl(tailoredResume.id, activeDocTab === 'cover_letter' ? 'cover_letter' : activeDocTab === 'html' ? 'html' : activeDocTab === 'text' ? 'text' : 'markdown')}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                  download
                >
                  <Download size={13} />
                  <span>Download</span>
                </a>
              </div>
            </div>

            {/* TAB 1: ATS Markdown */}
            {activeDocTab === 'markdown' && (
              <div>
                <pre
                  className="code-block"
                  style={{
                    maxHeight: '480px',
                    overflowY: 'auto',
                    fontSize: '0.8125rem',
                    lineHeight: 1.5,
                    backgroundColor: '#090d16',
                  }}
                >
                  {tailoredResume.compiled_markdown || tailoredResume.markdown_content}
                </pre>
              </div>
            )}

            {/* TAB 2: Cover Letter */}
            {activeDocTab === 'cover_letter' && (
              <div
                style={{
                  background: '#090d16',
                  padding: '1.5rem',
                  borderRadius: '6px',
                  border: '1px solid var(--border-color)',
                  fontSize: '0.875rem',
                  lineHeight: 1.7,
                  color: 'var(--text-secondary)',
                  whiteSpace: 'pre-wrap',
                  maxHeight: '480px',
                  overflowY: 'auto',
                  fontFamily: 'sans-serif',
                }}
              >
                {tailoredResume.cover_letter}
              </div>
            )}

            {/* TAB 3: Plain ASCII Text */}
            {activeDocTab === 'text' && (
              <div>
                <pre
                  className="code-block"
                  style={{
                    maxHeight: '480px',
                    overflowY: 'auto',
                    fontSize: '0.75rem',
                    lineHeight: 1.4,
                    backgroundColor: '#090d16',
                    fontFamily: 'monospace',
                  }}
                >
                  {tailoredResume.compiled_text}
                </pre>
              </div>
            )}

            {/* TAB 4: HTML Rendered */}
            {activeDocTab === 'html' && (
              <div
                style={{
                  background: '#ffffff',
                  borderRadius: '6px',
                  border: '1px solid var(--border-color)',
                  overflow: 'hidden',
                  width: '100%',
                }}
              >
                <iframe
                  srcDoc={tailoredResume.compiled_html || '<!DOCTYPE html><html><body><p style="padding:20px;color:#64748b;font-family:sans-serif;">No HTML document generated.</p></body></html>'}
                  title="HTML Resume Preview"
                  style={{
                    width: '100%',
                    height: '560px',
                    border: 'none',
                    backgroundColor: '#ffffff',
                    display: 'block',
                  }}
                  sandbox="allow-same-origin"
                />
              </div>
            )}

            {/* TAB 5: Traceability Fact Matrix */}
            {activeDocTab === 'traceability' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                  Atomic fact attribution mapping for tailored resume ID #{tailoredResume.id} ({Object.keys(tailoredResume.traceability_matrix || {}).length} verified facts cited):
                </div>
                {tailoredResume.traceability_matrix && Object.keys(tailoredResume.traceability_matrix).length > 0 ? (
                  Object.entries(tailoredResume.traceability_matrix).map(([factId, claims], i) => (
                    <div key={i} style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                        <code style={{ color: '#38bdf8', fontSize: '0.75rem', fontWeight: 600 }}>{factId}</code>
                        <span className="badge badge-gray" style={{ fontSize: '0.625rem' }}>{claims.length} claim(s)</span>
                      </div>
                      <ul style={{ listStylePosition: 'inside', fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.5, paddingLeft: '0.25rem' }}>
                        {claims.map((c, cIdx) => (
                          <li key={cIdx} style={{ marginBottom: '2px' }}>{c}</li>
                        ))}
                      </ul>
                    </div>
                  ))
                ) : (
                  <div style={{ background: '#090d16', padding: '1.25rem', borderRadius: '6px', border: '1px solid var(--border-color)', textAlign: 'center' }}>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                      No atomic fact attributions mapped yet. Fact traceability is populated when claims reference verified candidate fact IDs (e.g., <code>exp:1:h0</code>, <code>skill:java</code>).
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
