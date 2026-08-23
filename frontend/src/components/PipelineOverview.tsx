import React, { useState } from 'react';
import {
  Layers,
  UserCheck,
  FileSearch,
  FileText,
  CheckCircle,
  Globe,
  Code,
} from 'lucide-react';
import { PipelineStageInfo } from '../types';

interface PipelineOverviewProps {
  stages?: PipelineStageInfo[];
}

export const PipelineOverview: React.FC<PipelineOverviewProps> = () => {
  const [selectedStage, setSelectedStage] = useState<string>('candidate_profile');

  const stageDetails: Record<
    string,
    {
      title: string;
      phase: string;
      icon: React.ReactNode;
      status: 'active' | 'planned';
      description: string;
      inputs: string[];
      outputs: string[];
      tables: string[];
      contract: string;
    }
  > = {
    core_foundation: {
      title: 'Foundation & Core Infrastructure',
      phase: 'Phase 1 (Complete)',
      icon: <Layers size={24} color="#38bdf8" />,
      status: 'active',
      description:
        'FastAPI 3.12+ backend with SQLite WAL persistence, Alembic migrations, unified error contract, structured logging, health/readiness endpoints, and React+TS operational control plane.',
      inputs: ['Environment (.env)', 'System Signals', 'CLI invocation'],
      outputs: ['REST API (/api/v1)', 'Health Diagnostics', 'Database Schema v1'],
      tables: ['jobs', 'job_analyses', 'resumes', 'tailored_resumes', 'applications', 'application_reviews', 'audit_logs'],
      contract: `// Phase 1 API Envelope
interface APIResponse<T> {
  success: boolean;
  data: T;
  request_id?: string;
  timestamp: string;
}`,
    },
    candidate_profile: {
      title: 'Candidate Profile & Master Resume',
      phase: 'Phase 2 (Active)',
      icon: <UserCheck size={24} color="#34d399" />,
      status: 'active',
      description:
        'Authoritative candidate profile and master resume ground truth subsystem. Features untrusted raw resume parsing, human verification gate, and strict LLM context retrieval service boundary.',
      inputs: ['Raw Resume (PDF/TXT/MD/JSON)', 'User Manual Edits', 'Verification Actions'],
      outputs: ['Verified Ground Truth Context for Downstream LLMs', 'CandidateProfile Schema v2'],
      tables: ['candidate_profiles', 'work_experiences', 'educations', 'candidate_skills', 'projects', 'raw_resume_imports', 'audit_logs'],
      contract: `// Authoritative LLM Context Boundary
interface VerifiedGroundTruthContext {
  profile_id: number;
  profile_verified: boolean;
  candidate: { full_name: string; email: string; ... };
  experiences: VerifiedWorkExperience[];
  educations: VerifiedEducation[];
  skills: VerifiedCandidateSkill[];
  projects: VerifiedProject[];
  formatted_llm_prompt_context: string;
}`,
    },
    jd_analysis: {
      title: 'JD Analysis & Match Scoring',
      phase: 'Phase 3 (Planned)',
      icon: <FileSearch size={24} color="#ec4899" />,
      status: 'planned',
      description:
        'Analyzes job descriptions using NLP/LLM against verified candidate ground truth to extract technical competencies, required qualifications, soft skills, and match scoring.',
      inputs: ['Job Description (description_raw)', 'Verified Candidate Profile'],
      outputs: ['Fit Score (0-100)', 'Matched Skills', 'Missing Skills', 'JobAnalysis entity'],
      tables: ['job_analyses', 'jobs'],
      contract: `interface JDAnalysisContract {
  job_id: number;
  fit_score: number; // 0.0 - 100.0
  fit_level: 'high' | 'medium' | 'low';
  matched_skills: string[];
  missing_skills: string[];
}`,
    },
    resume_tailoring: {
      title: 'Resume Tailoring & Generation',
      phase: 'Phase 4 (Planned)',
      icon: <FileText size={24} color="#f59e0b" />,
      status: 'planned',
      description:
        'Dynamically tailors master resume bullet points and summary to match job requirements without hallucination, generating tailored markdown, cover letters, and PDFs.',
      inputs: ['Verified Ground Truth Resume', 'Job Analysis (JobAnalysis)'],
      outputs: ['TailoredResume record', 'Custom Cover Letter', 'Generated PDF path'],
      tables: ['resumes', 'tailored_resumes'],
      contract: `interface ResumeTailoringContract {
  job_id: number;
  base_resume_id: number;
  tailored_summary: string;
  highlighted_skills: string[];
}`,
    },
    human_approval: {
      title: 'Human-in-the-Loop Review & Approval',
      phase: 'Phase 5 (Planned)',
      icon: <CheckCircle size={24} color="#a855f7" />,
      status: 'planned',
      description:
        'Interactive approval queue where user inspects tailored resume, match score, form answers, and makes manual edits before granting submission permission.',
      inputs: ['Application Draft', 'Tailored Resume', 'Form Field Answers'],
      outputs: ['ApplicationReview record', 'Approved Application state (APPROVED)'],
      tables: ['applications', 'application_reviews', 'audit_logs'],
      contract: `interface ApprovalContract {
  application_id: number;
  decision: 'approved' | 'rejected' | 'changes_requested';
}`,
    },
    browser_preparation: {
      title: 'Browser Automation & Portal Submission',
      phase: 'Phase 6 (Planned)',
      icon: <Globe size={24} color="#3b82f6" />,
      status: 'planned',
      description:
        'Assisted or automated portal navigation (Greenhouse, Lever, Workday, etc.), form auto-filling, file attachment, with final human confirmation gate before submission.',
      inputs: ['Approved Application', 'Tailored PDF', 'Candidate Metadata'],
      outputs: ['Application Status: submitted', 'Confirmation Receipt', 'AuditLog record'],
      tables: ['applications', 'audit_logs'],
      contract: `interface BrowserSubmissionContract {
  application_id: number;
  portal_type: 'greenhouse' | 'lever' | 'workday' | 'generic';
  status: 'submitted' | 'failed';
}`,
    },
  };

  const currentDetail = stageDetails[selectedStage] || stageDetails['candidate_profile'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          End-to-End Pipeline Architecture
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          The AI Job Application Agent executes as a sequential, human-in-the-loop autonomous pipeline.
          Phase 2 establishes the verified candidate profile and master resume subsystem.
        </p>
      </div>

      {/* Visual Pipeline Flowchart */}
      <div
        className="card"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '0.75rem',
          padding: '1.5rem 1rem',
          backgroundColor: '#0b1120',
        }}
      >
        {Object.entries(stageDetails).map(([key, stage], index) => {
          const isSelected = selectedStage === key;
          const isActive = stage.status === 'active';

          return (
            <div
              key={key}
              onClick={() => setSelectedStage(key)}
              style={{
                cursor: 'pointer',
                borderRadius: '8px',
                padding: '1rem',
                border: `1px solid ${isSelected ? '#38bdf8' : isActive ? '#10b981' : 'var(--border-color)'}`,
                backgroundColor: isSelected ? 'rgba(56, 189, 248, 0.1)' : isActive ? 'rgba(16, 185, 129, 0.12)' : '#131b2e',
                transition: 'all 0.2s',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                  STEP 0{index + 1}
                </span>
                {isActive ? (
                  <span className="badge badge-green" style={{ fontSize: '0.625rem', padding: '0.125rem 0.375rem' }}>
                    Active
                  </span>
                ) : (
                  <span className="badge badge-gray" style={{ fontSize: '0.625rem', padding: '0.125rem 0.375rem' }}>
                    Planned
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                {stage.icon}
                <div style={{ fontWeight: 600, fontSize: '0.8125rem', lineHeight: 1.3 }}>
                  {stage.title}
                </div>
              </div>

              <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                {stage.phase}
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Stage Deep-Dive Card */}
      <div className="card" style={{ borderTop: `3px solid ${currentDetail.status === 'active' ? '#34d399' : '#64748b'}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {currentDetail.icon}
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{currentDetail.title}</h3>
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem' }}>
                <span className="badge badge-blue">{currentDetail.phase}</span>
                <span className={`badge ${currentDetail.status === 'active' ? 'badge-green' : 'badge-gray'}`}>
                  Status: {currentDetail.status.toUpperCase()}
                </span>
              </div>
            </div>
          </div>
        </div>

        <p style={{ fontSize: '0.9375rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '1.5rem' }}>
          {currentDetail.description}
        </p>

        {/* Inputs & Outputs Grid */}
        <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
          <div style={{ background: '#090d16', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <h4 style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent-blue)', marginBottom: '0.5rem' }}>
              Input Requirements
            </h4>
            <ul style={{ listStylePosition: 'inside', fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              {currentDetail.inputs.map((inp, i) => (
                <li key={i} style={{ marginBottom: '0.25rem' }}>{inp}</li>
              ))}
            </ul>
          </div>

          <div style={{ background: '#090d16', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <h4 style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent-emerald)', marginBottom: '0.5rem' }}>
              Output Artifacts
            </h4>
            <ul style={{ listStylePosition: 'inside', fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              {currentDetail.outputs.map((out, i) => (
                <li key={i} style={{ marginBottom: '0.25rem' }}>{out}</li>
              ))}
            </ul>
          </div>

          <div style={{ background: '#090d16', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <h4 style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent-purple)', marginBottom: '0.5rem' }}>
              Database Tables
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
              {currentDetail.tables.map((tbl, i) => (
                <span key={i} style={{ fontSize: '0.75rem', padding: '0.125rem 0.5rem', background: '#1e293b', borderRadius: '4px', color: '#c084fc' }}>
                  {tbl}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
            <Code size={14} />
            <span>Target Contract / Data Transfer Interface</span>
          </div>
          <pre className="code-block">{currentDetail.contract}</pre>
        </div>
      </div>
    </div>
  );
};
