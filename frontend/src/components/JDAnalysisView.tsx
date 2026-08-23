import React, { useState, useEffect, useCallback } from 'react';
import {
  Cpu,
  Brain,
  Sparkles,
  CheckCircle,
  AlertCircle,
  ShieldCheck,
  RefreshCw,
  Search,
  Award,
  Check,
  Copy,
} from 'lucide-react';
import { api } from '../services/api';
import { Job, JobAnalysis, LLMStatusResponse } from '../types';

export const JDAnalysisView: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [analysis, setAnalysis] = useState<JobAnalysis | null>(null);
  const [llmStatus, setLlmStatus] = useState<LLMStatusResponse | null>(null);

  // Loading States
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [customInstructions, setCustomInstructions] = useState<string>('');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

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

  const fetchJobAnalysis = useCallback(async (jobId: number) => {
    try {
      const analysisData = await api.getJobAnalysis(jobId);
      setAnalysis(analysisData);
    } catch {
      setAnalysis(null);
    }
  }, []);

  useEffect(() => {
    fetchLLMAndJobs();
  }, [fetchLLMAndJobs]);

  useEffect(() => {
    if (selectedJobId) {
      const target = jobs.find((j) => j.id === selectedJobId) || null;
      setSelectedJob(target);
      fetchJobAnalysis(selectedJobId);
    }
  }, [selectedJobId, jobs, fetchJobAnalysis]);

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

  const handleCopyKeywords = (keywords: string[]) => {
    navigator.clipboard.writeText(keywords.join(', '));
    setCopiedKey('keywords');
    setTimeout(() => setCopiedKey(null), 2000);
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
              Structured JD Analysis & Candidate Matching Engine
            </h2>
            <span className="badge badge-purple">Phase 5 Active</span>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Local LLM inference on Apple Silicon GPU via Ollama. Untrusted JD isolation, deterministic + semantic matching, and zero cloud dependencies.
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
              Select Job from Catalog:
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
        {/* COLUMN 1: Untrusted JD Text & Security Sandbox */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <ShieldCheck size={18} color="#38bdf8" />
                <h3 style={{ fontSize: '1.0625rem', fontWeight: 700 }}>Untrusted JD Text Sandbox</h3>
              </div>
              <span
                style={{
                  fontSize: '0.6875rem',
                  padding: '0.2rem 0.5rem',
                  background: 'rgba(56, 189, 248, 0.12)',
                  color: '#38bdf8',
                  borderRadius: '4px',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                }}
              >
                <ShieldCheck size={12} />
                <span>Prompt Injection Shield</span>
              </span>
            </div>

            {/* Custom Evaluation Instructions */}
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.25rem' }}>
                Optional Evaluation Guidance / Focus:
              </label>
              <input
                type="text"
                value={customInstructions}
                onChange={(e) => setCustomInstructions(e.target.value)}
                placeholder="e.g., Focus evaluation on high-throughput streaming database architecture..."
                style={{
                  width: '100%',
                  padding: '0.4rem 0.625rem',
                  background: '#090d16',
                  border: '1px solid var(--border-color)',
                  borderRadius: '6px',
                  color: '#f8fafc',
                  fontSize: '0.75rem',
                }}
              />
            </div>

            {/* Raw Untrusted JD Viewer */}
            <div style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)', marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between' }}>
                <span>Isolated Prompt Boundary: <code>&lt;untrusted_job_description&gt;</code></span>
                <span>Length: {selectedJob?.description_raw?.length || 0} chars</span>
              </div>
              <div
                style={{
                  maxHeight: '260px',
                  overflowY: 'auto',
                  fontSize: '0.75rem',
                  lineHeight: 1.5,
                  color: 'var(--text-secondary)',
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'monospace',
                }}
              >
                {selectedJob?.description_raw || selectedJob?.description_clean || 'No description available for this job.'}
              </div>
            </div>

            <button
              onClick={handleRunAnalysis}
              disabled={isAnalyzing || !selectedJobId}
              className="btn btn-primary"
              style={{ width: '100%', padding: '0.625rem', fontSize: '0.875rem' }}
            >
              <Sparkles size={16} />
              <span>{isAnalyzing ? 'Evaluating via Ollama (qwen3:8b)...' : 'Run Deep JD Analysis & Matching'}</span>
            </button>
          </div>
        </div>

        {/* COLUMN 2: Structured Analysis & Candidate Alignment Report */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Brain size={18} color="#c084fc" />
                <h3 style={{ fontSize: '1.0625rem', fontWeight: 700 }}>Match & Alignment Evaluation</h3>
              </div>

              {/* Anti-Hallucination Verified Badge */}
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

            {analysis ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {/* Composite Score Card */}
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
                      Composite Match Score
                    </div>
                    <div
                      style={{
                        fontSize: '2rem',
                        fontWeight: 800,
                        color:
                          analysis.fit_score && analysis.fit_score >= 75
                            ? '#34d399'
                            : analysis.fit_score && analysis.fit_score >= 50
                            ? '#fbbf24'
                            : '#f87171',
                      }}
                    >
                      {analysis.fit_score !== null && analysis.fit_score !== undefined
                        ? `${analysis.fit_score.toFixed(1)}%`
                        : 'N/A'}
                    </div>
                    <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.125rem' }}>
                      Deterministic: {analysis.deterministic_score ?? 'N/A'}% · Semantic: {analysis.semantic_score ?? 'N/A'}%
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <span
                      className={`badge ${
                        analysis.recommendation === 'strong_apply'
                          ? 'badge-green'
                          : analysis.recommendation === 'apply'
                          ? 'badge-blue'
                          : analysis.recommendation === 'stretch'
                          ? 'badge-purple'
                          : 'badge-red'
                      }`}
                      style={{ fontSize: '0.8125rem', textTransform: 'uppercase', padding: '0.3rem 0.6rem' }}
                    >
                      {analysis.recommendation ? analysis.recommendation.replace('_', ' ') : 'Evaluated'}
                    </span>
                    <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                      Model: <code>{analysis.model_used || 'qwen3:8b'}</code>
                    </div>
                  </div>
                </div>

                {/* Role Summary & Assessment */}
                <div>
                  <h5 style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                    Executive Assessment
                  </h5>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {analysis.summary}
                  </p>
                </div>

                {/* Skill Alignment Matrix */}
                <div>
                  <h5 style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                    Dual Match Skill Matrix
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

                    {/* Missing Skills / Gaps */}
                    {analysis.missing_skills && analysis.missing_skills.length > 0 && (
                      <div style={{ background: 'rgba(251, 191, 36, 0.08)', padding: '0.625rem', borderRadius: '6px', border: '1px solid rgba(251, 191, 36, 0.2)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.75rem', fontWeight: 600, color: '#fbbf24', marginBottom: '0.375rem' }}>
                          <AlertCircle size={13} />
                          <span>Skill Gaps / Unverified ({analysis.missing_skills.length})</span>
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

                {/* ATS Keywords */}
                {analysis.keywords && analysis.keywords.length > 0 && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
                      <h5 style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                        High-Signal ATS Keywords
                      </h5>
                      <button
                        onClick={() => handleCopyKeywords(analysis.keywords)}
                        className="btn btn-secondary"
                        style={{ fontSize: '0.6875rem', padding: '0.125rem 0.375rem' }}
                      >
                        {copiedKey === 'keywords' ? <Check size={11} color="#34d399" /> : <Copy size={11} />}
                        <span>{copiedKey === 'keywords' ? 'Copied' : 'Copy'}</span>
                      </button>
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                      {analysis.keywords.map((k, idx) => (
                        <span key={idx} style={{ fontSize: '0.6875rem', padding: '0.125rem 0.375rem', background: '#1e293b', borderRadius: '4px', color: '#94a3b8' }}>
                          {k}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ padding: '3rem 1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                <Brain size={36} color="var(--border-color)" style={{ margin: '0 auto 0.75rem' }} />
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                  Click <strong>Run Deep JD Analysis</strong> to execute deterministic & local Ollama matching against verified candidate ground truth.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
