import React, { useState, useEffect, useCallback } from 'react';
import {
  Cpu,
  Brain,
  Sparkles,
  CheckCircle,
  AlertCircle,
  Copy,
  Check,
  FileText,
  FileCode,
  Layers,
  RefreshCw,
  Search,
  Sliders,
  Award,
} from 'lucide-react';
import { api } from '../services/api';
import { Job, JobAnalysis, TailoredResume, LLMStatusResponse } from '../types';

export const AnalysisAndTailoringView: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [analysis, setAnalysis] = useState<JobAnalysis | null>(null);
  const [tailoredResume, setTailoredResume] = useState<TailoredResume | null>(null);
  const [llmStatus, setLlmStatus] = useState<LLMStatusResponse | null>(null);

  // Loading States
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [isTailoring, setIsTailoring] = useState<boolean>(false);

  // Tailoring Options
  const [tone, setTone] = useState<string>('professional');
  const [customInstructions, setCustomInstructions] = useState<string>('');
  const [activeOutputTab, setActiveOutputTab] = useState<'resume' | 'cover_letter' | 'experience'>('resume');

  // Copy Feedback
  const [copiedSection, setCopiedSection] = useState<string | null>(null);

  const fetchLLMAndJobs = useCallback(async () => {
    try {
      const [statusData, jobsData] = await Promise.all([
        api.getLLMStatus(),
        api.getJobs({ page: 1, page_size: 50 }),
      ]);
      setLlmStatus(statusData);
      setJobs(jobsData.items);

      if (jobsData.items.length > 0 && !selectedJobId) {
        setSelectedJobId(jobsData.items[0].id);
        setSelectedJob(jobsData.items[0]);
      }
    } catch (err) {
      console.error('Failed to load LLM status or jobs:', err);
    }
  }, [selectedJobId]);

  const fetchJobArtifacts = useCallback(async (jobId: number) => {
    try {
      const [analysisData, tailorData] = await Promise.allSettled([
        api.getJobAnalysis(jobId),
        api.getJobTailoredResume(jobId),
      ]);

      if (analysisData.status === 'fulfilled') {
        setAnalysis(analysisData.value);
      } else {
        setAnalysis(null);
      }

      if (tailorData.status === 'fulfilled') {
        setTailoredResume(tailorData.value);
      } else {
        setTailoredResume(null);
      }
    } catch (err) {
      console.error('Error fetching job analysis/tailoring artifacts:', err);
    }
  }, []);

  useEffect(() => {
    fetchLLMAndJobs();
  }, [fetchLLMAndJobs]);

  useEffect(() => {
    if (selectedJobId) {
      const target = jobs.find((j) => j.id === selectedJobId) || null;
      setSelectedJob(target);
      fetchJobArtifacts(selectedJobId);
    }
  }, [selectedJobId, jobs, fetchJobArtifacts]);

  const handleSelectJob = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = parseInt(e.target.value, 10);
    setSelectedJobId(id);
  };

  const handleRunAnalysis = async () => {
    if (!selectedJobId) return;
    setIsAnalyzing(true);
    try {
      const res = await api.analyzeJob(selectedJobId, {
        custom_instructions: customInstructions || undefined,
      });
      setAnalysis(res);
    } catch (err: any) {
      alert(`JD Analysis failed: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleRunTailoring = async () => {
    if (!selectedJobId) return;
    setIsTailoring(true);
    try {
      const res = await api.tailorResume(selectedJobId, {
        tone,
        custom_instructions: customInstructions || undefined,
      });
      setTailoredResume(res);
      // Refresh analysis too in case it was triggered during tailoring
      fetchJobArtifacts(selectedJobId);
    } catch (err: any) {
      alert(`Resume Tailoring failed: ${err.message}`);
    } finally {
      setIsTailoring(false);
    }
  };

  const handleCopyText = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSection(label);
    setTimeout(() => setCopiedSection(null), 2500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner: Local LLM Engine Status */}
      <div
        className="card"
        style={{
          borderLeft: '4px solid #c084fc',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Cpu size={24} color="#c084fc" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>
              Local LLM Analysis & Resume Tailoring Studio
            </h2>
            <span className="badge badge-purple">Phase 5 Active</span>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Privacy-preserving local inference on Apple Silicon GPU via Ollama. 100% grounded in verified candidate facts without hallucination.
          </p>
        </div>

        {/* LLM Health Status Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              padding: '0.4rem 0.75rem',
              borderRadius: '6px',
              backgroundColor: '#090d16',
              border: `1px solid ${llmStatus?.status === 'connected' ? '#34d399' : '#f87171'}`,
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.75rem',
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: llmStatus?.status === 'connected' ? '#34d399' : '#f87171',
              }}
            />
            <span>
              Provider: <strong>{llmStatus?.provider || 'ollama'}</strong> ({llmStatus?.active_model || 'qwen3:8b'})
            </span>
            {llmStatus?.latency_ms !== undefined && (
              <span style={{ color: 'var(--text-muted)' }}>· {llmStatus.latency_ms} ms</span>
            )}
          </div>

          <button onClick={fetchLLMAndJobs} className="btn btn-secondary" style={{ fontSize: '0.8125rem' }}>
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Target Job Selector */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: '280px' }}>
            <Search size={16} color="var(--text-muted)" />
            <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Select Job to Analyze & Tailor:
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
      </div>

      {/* Main Two-Column Workbench */}
      <div className="grid-2">
        {/* COLUMN 1: JD Analysis & Fit Scoring */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Brain size={18} color="#38bdf8" />
                <h3 style={{ fontSize: '1.0625rem', fontWeight: 700 }}>1. AI Job Description Analysis</h3>
              </div>
              <button
                onClick={handleRunAnalysis}
                disabled={isAnalyzing || !selectedJobId}
                className="btn btn-primary"
                style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
              >
                <Sparkles size={13} />
                <span>{isAnalyzing ? 'Analyzing via Ollama...' : 'Analyze JD (qwen3:8b)'}</span>
              </button>
            </div>

            {analysis ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {/* Fit Score Radial / Pill */}
                <div
                  style={{
                    background: '#090d16',
                    padding: '1rem',
                    borderRadius: '8px',
                    border: '1px solid var(--border-color)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                      Candidate Match Score
                    </div>
                    <div style={{ fontSize: '1.75rem', fontWeight: 800, color: analysis.fit_score && analysis.fit_score >= 75 ? '#34d399' : analysis.fit_score && analysis.fit_score >= 50 ? '#fbbf24' : '#f87171' }}>
                      {analysis.fit_score !== null && analysis.fit_score !== undefined ? `${analysis.fit_score.toFixed(1)}%` : 'N/A'}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span
                      className={`badge ${analysis.fit_level === 'high' ? 'badge-green' : analysis.fit_level === 'medium' ? 'badge-blue' : 'badge-red'}`}
                      style={{ fontSize: '0.8125rem', textTransform: 'uppercase', padding: '0.3rem 0.6rem' }}
                    >
                      {analysis.fit_level || 'Evaluated'} Match
                    </span>
                    <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                      Model: <code>{analysis.model_used || 'qwen3:8b'}</code>
                    </div>
                  </div>
                </div>

                {/* Match Summary */}
                {analysis.summary && (
                  <div>
                    <h5 style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                      Fit Assessment
                    </h5>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      {analysis.summary}
                    </p>
                  </div>
                )}

                {/* Skill Matrix */}
                <div>
                  <h5 style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                    Skill Alignment Matrix
                  </h5>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {/* Matched Verified Skills */}
                    <div style={{ background: 'rgba(52, 211, 153, 0.08)', padding: '0.625rem', borderRadius: '6px', border: '1px solid rgba(52, 211, 153, 0.2)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.75rem', fontWeight: 600, color: '#34d399', marginBottom: '0.375rem' }}>
                        <CheckCircle size={13} />
                        <span>Matched Verified Skills ({analysis.matched_skills?.length || 0})</span>
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                        {analysis.matched_skills?.map((s, idx) => (
                          <span key={idx} style={{ fontSize: '0.6875rem', padding: '0.125rem 0.375rem', background: '#090d16', borderRadius: '4px', color: '#34d399', border: '1px solid rgba(52, 211, 153, 0.3)' }}>
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Missing Skills */}
                    {analysis.missing_skills && analysis.missing_skills.length > 0 && (
                      <div style={{ background: 'rgba(251, 191, 36, 0.08)', padding: '0.625rem', borderRadius: '6px', border: '1px solid rgba(251, 191, 36, 0.2)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.75rem', fontWeight: 600, color: '#fbbf24', marginBottom: '0.375rem' }}>
                          <AlertCircle size={13} />
                          <span>Skill Gap / Unverified ({analysis.missing_skills.length})</span>
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                          {analysis.missing_skills.map((s, idx) => (
                            <span key={idx} style={{ fontSize: '0.6875rem', padding: '0.125rem 0.375rem', background: '#090d16', borderRadius: '4px', color: '#fbbf24', border: '1px solid rgba(251, 191, 36, 0.3)' }}>
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Key Responsibilities */}
                {analysis.key_responsibilities && analysis.key_responsibilities.length > 0 && (
                  <div>
                    <h5 style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                      Key Responsibilities
                    </h5>
                    <ul style={{ listStylePosition: 'inside', fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                      {analysis.key_responsibilities.slice(0, 4).map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ padding: '3rem 1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                <Brain size={36} color="var(--border-color)" style={{ margin: '0 auto 0.75rem' }} />
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                  Click <strong>Analyze JD</strong> to run local LLM match evaluation against the candidate's verified profile facts.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* COLUMN 2: Resume & Cover Letter Tailoring Studio */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FileText size={18} color="#34d399" />
                <h3 style={{ fontSize: '1.0625rem', fontWeight: 700 }}>2. Resume & Cover Letter Tailoring</h3>
              </div>

              {/* Anti-Hallucination Badge */}
              <span
                style={{
                  fontSize: '0.6875rem',
                  padding: '0.2rem 0.5rem',
                  background: 'rgba(52, 211, 153, 0.15)',
                  color: '#34d399',
                  borderRadius: '4px',
                  border: '1px solid #34d399',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                }}
              >
                <Award size={12} />
                <span>100% Grounded</span>
              </span>
            </div>

            <div style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)', marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                  <Sliders size={13} color="var(--text-muted)" />
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Tone:</span>
                  <select
                    value={tone}
                    onChange={(e) => setTone(e.target.value)}
                    style={{ padding: '0.25rem 0.5rem', background: '#131b2e', border: '1px solid var(--border-color)', borderRadius: '4px', color: '#f8fafc', fontSize: '0.75rem' }}
                  >
                    <option value="professional">Professional</option>
                    <option value="confident">Confident / High Impact</option>
                    <option value="technical">Deep Technical</option>
                  </select>
                </div>

                <button
                  onClick={handleRunTailoring}
                  disabled={isTailoring || !selectedJobId}
                  className="btn btn-primary"
                  style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem', marginLeft: 'auto' }}
                >
                  <Sparkles size={13} />
                  <span>{isTailoring ? 'Generating Materials...' : 'Tailor Resume & Letter'}</span>
                </button>
              </div>

              <input
                type="text"
                value={customInstructions}
                onChange={(e) => setCustomInstructions(e.target.value)}
                placeholder="Optional special tailoring instructions (e.g. emphasize distributed consensus & high availability)..."
                style={{
                  width: '100%',
                  padding: '0.35rem 0.5rem',
                  background: '#131b2e',
                  border: '1px solid var(--border-color)',
                  borderRadius: '4px',
                  color: '#f8fafc',
                  fontSize: '0.75rem',
                }}
              />
            </div>

            {tailoredResume ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {/* Output Sub-Tabs */}
                <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                  <button
                    onClick={() => setActiveOutputTab('resume')}
                    className={`btn ${activeOutputTab === 'resume' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.75rem', padding: '0.25rem 0.625rem' }}
                  >
                    <FileCode size={12} />
                    <span>Markdown Resume</span>
                  </button>
                  <button
                    onClick={() => setActiveOutputTab('cover_letter')}
                    className={`btn ${activeOutputTab === 'cover_letter' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.75rem', padding: '0.25rem 0.625rem' }}
                  >
                    <FileText size={12} />
                    <span>Cover Letter</span>
                  </button>
                  <button
                    onClick={() => setActiveOutputTab('experience')}
                    className={`btn ${activeOutputTab === 'experience' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.75rem', padding: '0.25rem 0.625rem' }}
                  >
                    <Layers size={12} />
                    <span>Experience Highlights</span>
                  </button>
                </div>

                {/* Sub-Tab 1: Markdown Resume Preview */}
                {activeOutputTab === 'resume' && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Status: <span className="badge badge-green">{tailoredResume.status}</span>
                      </span>
                      <button
                        onClick={() => handleCopyText(tailoredResume.markdown_content || '', 'resume')}
                        className="btn btn-secondary"
                        style={{ fontSize: '0.6875rem', padding: '0.2rem 0.5rem' }}
                      >
                        {copiedSection === 'resume' ? <Check size={12} color="#34d399" /> : <Copy size={12} />}
                        <span>{copiedSection === 'resume' ? 'Copied!' : 'Copy Markdown'}</span>
                      </button>
                    </div>

                    <pre
                      className="code-block"
                      style={{
                        maxHeight: '380px',
                        overflowY: 'auto',
                        fontSize: '0.75rem',
                        lineHeight: 1.5,
                        backgroundColor: '#090d16',
                      }}
                    >
                      {tailoredResume.markdown_content}
                    </pre>
                  </div>
                )}

                {/* Sub-Tab 2: Cover Letter */}
                {activeOutputTab === 'cover_letter' && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Personalized Cover Letter
                      </span>
                      <button
                        onClick={() => handleCopyText(tailoredResume.cover_letter || '', 'cover_letter')}
                        className="btn btn-secondary"
                        style={{ fontSize: '0.6875rem', padding: '0.2rem 0.5rem' }}
                      >
                        {copiedSection === 'cover_letter' ? <Check size={12} color="#34d399" /> : <Copy size={12} />}
                        <span>{copiedSection === 'cover_letter' ? 'Copied!' : 'Copy Letter'}</span>
                      </button>
                    </div>

                    <div
                      style={{
                        background: '#090d16',
                        padding: '1rem',
                        borderRadius: '6px',
                        border: '1px solid var(--border-color)',
                        fontSize: '0.8125rem',
                        lineHeight: 1.6,
                        color: 'var(--text-secondary)',
                        whiteSpace: 'pre-wrap',
                        maxHeight: '380px',
                        overflowY: 'auto',
                      }}
                    >
                      {tailoredResume.cover_letter}
                    </div>
                  </div>
                )}

                {/* Sub-Tab 3: Experience Highlights */}
                {activeOutputTab === 'experience' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {tailoredResume.tailored_experience?.map((exp, idx) => (
                      <div key={idx} style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                        <div style={{ fontWeight: 600, fontSize: '0.8125rem', color: '#38bdf8' }}>
                          {exp.position} — {exp.company}
                        </div>
                        <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginBottom: '0.375rem' }}>
                          {exp.start_date} – {exp.is_current ? 'Present' : exp.end_date || 'N/A'}
                        </div>
                        <ul style={{ listStylePosition: 'inside', fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                          {exp.tailored_highlights?.map((h, hIdx) => (
                            <li key={hIdx}>{h}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div style={{ padding: '3rem 1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                <FileText size={36} color="var(--border-color)" style={{ margin: '0 auto 0.75rem' }} />
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                  Click <strong>Tailor Resume & Letter</strong> to synthesize custom application documents grounded strictly in verified candidate facts.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
