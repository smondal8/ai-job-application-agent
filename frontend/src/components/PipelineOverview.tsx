import React, { useState } from 'react';
import {
  Layers,
  UserCheck,
  Briefcase,
  Compass,
  Brain,
  FileText,
  Globe,
  Code,
} from 'lucide-react';
import { PipelineStageInfo } from '../types';

interface PipelineOverviewProps {
  stages?: PipelineStageInfo[];
}

export const PipelineOverview: React.FC<PipelineOverviewProps> = () => {
  const [selectedStage, setSelectedStage] = useState<string>('jd_analysis_matching');

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
      phase: 'Phase 2 (Complete)',
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
    job_database: {
      title: 'Normalized Job DB & Ingestion',
      phase: 'Phase 3 (Complete)',
      icon: <Briefcase size={24} color="#38bdf8" />,
      status: 'active',
      description:
        'Normalized job listings catalog and ingestion pipeline supporting JSON and CSV feeds. Features company registry normalization and deterministic conservative deduplication preserving distinct roles and locations.',
      inputs: ['JSON Feeds', 'CSV Fixtures', 'File Uploads', 'Manual Postings'],
      outputs: ['Normalized Job Catalog', 'Registered Companies', 'Batch Ingestion Ledger'],
      tables: ['jobs', 'companies', 'job_ingestion_batches', 'audit_logs'],
      contract: `// Phase 3 Ingestion Batch Response
interface JobIngestionBatchResponse {
  batch_id: string;
  source: string;
  total_records: number;
  inserted_count: number;
  updated_count: number;
  duplicate_count: number;
  error_count: number;
  status: 'completed' | 'failed';
}`,
    },
    job_discovery: {
      title: 'Job Discovery & Orchestration',
      phase: 'Phase 4 (Complete)',
      icon: <Compass size={24} color="#38bdf8" />,
      status: 'active',
      description:
        'Source-agnostic adapter framework with rate limiting, retries, and orchestration across Greenhouse, Lever, and remote feeds, with safe manual fallbacks for bot-protected platforms.',
      inputs: ['Search Criteria (Keywords, Target Companies, Locations)', 'Saved Search Profiles'],
      outputs: ['Discovered Job Records', 'Discovery Run Audit Logs', 'Direct Ingestion into DB'],
      tables: ['job_discovery_runs', 'job_search_profiles', 'jobs', 'audit_logs'],
      contract: `// Phase 4 Discovery Run Response
interface DiscoveryRunResponse {
  run_id: string;
  source: string;
  criteria: SearchCriteria;
  total_discovered: number;
  inserted_count: number;
  duplicate_count: number;
  status: 'completed' | 'partial' | 'failed';
  adapter_logs: Array<{ adapter: string; status: string; discovered_count: number }>;
}`,
    },
    jd_analysis_matching: {
      title: 'Structured JD Analysis & Candidate Matching',
      phase: 'Phase 5 (Active)',
      icon: <Brain size={24} color="#c084fc" />,
      status: 'active',
      description:
        'Prompt-injection safe structured output pipeline using local Ollama (qwen3:8b) on Apple Silicon GPU. Combines deterministic keyword matching and deep semantic evaluation for objective fit scoring (0-100%).',
      inputs: ['Untrusted Job Description (Isolated in sandbox)', 'Authoritative Verified Candidate Facts'],
      outputs: ['JobAnalysis (Composite Fit Score, Matched/Missing Skills Matrix, Recommendations)'],
      tables: ['job_analyses', 'audit_logs'],
      contract: `// Phase 5 JD Analysis & Matching Contract
interface JobAnalysisResponse {
  job_id: number;
  candidate_profile_id: number;
  fit_score: number; // 0.0 - 100.0 (Composite)
  deterministic_score: number;
  semantic_score: number;
  fit_level: 'high' | 'medium' | 'low';
  recommendation: 'strong_apply' | 'apply' | 'stretch' | 'skip';
  summary: string;
  role_summary: string;
  key_responsibilities: string[];
  matched_skills: string[];
  missing_skills: string[];
  keywords: string[];
  model_used: string;
}`,
    },
    resume_tailoring: {
      title: 'Resume & Cover Letter Tailoring Studio',
      phase: 'Phase 6 (Active)',
      icon: <FileText size={24} color="#34d399" />,
      status: 'active',
      description:
        'Grounded resume tailoring and personalized cover letter generation with atomic fact attribution (source_fact_ids), claim validation, and deterministic document compilation (Markdown/ASCII/HTML).',
      inputs: ['JobAnalysis Artifact', 'Atomic Verified Candidate Facts (source_fact_ids)', 'Writing Tone & Strategic Guidance'],
      outputs: ['ATS Markdown Resume', 'Plain ASCII Text', 'Styled HTML Document', 'Personalized Cover Letter', 'Traceability Matrix'],
      tables: ['tailored_resumes', 'job_analyses', 'audit_logs'],
      contract: `// Phase 6 Grounded Tailoring Contract
interface TailoredResumeResponse {
  job_id: number;
  prompt_version: 'v1.0.0';
  tailored_summary: string;
  tailored_experience: Array<{
    company: string;
    position: string;
    tailored_highlights: Array<{ text: string; source_fact_ids: string[] }>;
  }>;
  highlighted_skills: string[];
  cover_letter: string;
  compiled_markdown: string;
  compiled_text: string;
  compiled_html: string;
  validation_status: 'valid' | 'requires_human_review' | 'rejected';
  traceability_matrix: Record<string, string[]>;
}`,
    },
    application_dashboard: {
      title: 'Central Application Dashboard & Review Workflow',
      phase: 'Phase 7 (Active)',
      icon: <Briefcase size={24} color="#38bdf8" />,
      status: 'active',
      description:
        'Unified application management, multi-entity dossier read/review workflows, and job & tailored resume version linking with full traceability.',
      inputs: ['Job Listings', 'Tailored Resumes (Phase 6)', 'Screening Answers', 'Review Notes'],
      outputs: ['Application Dossier', 'Review Ledger Entries', 'Audit Trails'],
      tables: ['applications', 'application_reviews', 'jobs', 'tailored_resumes', 'audit_logs'],
      contract: `// Phase 7 Application Dossier Contract
interface ApplicationDossierResponse {
  application: ApplicationResponse;
  job: JobResponse;
  tailored_resume: TailoredResumeResponse;
  available_resumes: Array<{ id: number; prompt_version: string; validation_status: string }>;
  analysis: JobAnalysisResponse;
  candidate: CandidateProfileResponse;
  reviews: ApplicationReviewResponse[];
}`,
    },
    approval_and_submission: {
      title: 'Human Approval Security Boundary & State Machine',
      phase: 'Phase 8 (Active)',
      icon: <Globe size={24} color="#34d399" />,
      status: 'active',
      description:
        'Cryptographic human approval gate bound to immutable hashes of JD, candidate profile facts, tailored resume, and screening answers. Automatic invalidation on material changes.',
      inputs: ['Reviewed Application Dossier', 'Live Hashes (Job, Profile, Resume, Answers)', 'Human Reviewer Authorization'],
      outputs: ['ApplicationApproval Certificate', 'Approval Token', 'Preparation Authorization Certificate', 'AuditLog record'],
      tables: ['applications', 'application_approvals', 'application_reviews', 'audit_logs'],
      contract: `// Phase 8 Human Approval Security Contract
interface ApprovalVerificationResponse {
  is_valid: boolean;
  is_approved: boolean;
  application_id: number;
  current_status: string;
  approval_token?: string | null;
  hashes?: {
    job_hash: string;
    candidate_hash: string;
    resume_hash: string;
    answers_hash: string;
  };
  mismatches: string[];
}`,
    },
    browser_automation_staging: {
      title: 'Playwright Browser Application-Preparation Engine',
      phase: 'Phase 9 (Active)',
      icon: <Globe size={24} color="#38bdf8" />,
      status: 'active',
      description:
        'Playwright browser application preparation engine, server-side authorization check, automated form pre-filling, screenshot capture, and non-negotiable submit guards.',
      inputs: ['Authorized Application Preparation Token', 'Verified Candidate Facts', 'Approved Tailored Resume', 'Screening Answers'],
      outputs: ['Pre-filled Application Form', 'Execution Audit Run', 'Full-Page Screenshot Artifact', 'Unresolved Fields Log'],
      tables: ['applications', 'browser_preparation_runs', 'audit_logs'],
      contract: `// Phase 9 Browser Preparation Contract
interface PreparationRunResponse {
  id: number;
  application_id: number;
  approval_token: string;
  portal_type: 'greenhouse' | 'lever' | 'ashby' | 'workday' | 'generic';
  status: 'staged' | 'paused_for_human_input' | 'blocked_by_captcha' | 'blocked_by_auth' | 'failed';
  fields_filled: Array<{ field: string; value: string }>;
  unresolved_fields: Array<{ field: string; reason: string }>;
  resume_uploaded: boolean;
  screenshot_path: string;
  final_submit_clicked: false; // NON-NEGOTIABLE
  guard_triggered: boolean;
}`,
    },
    portal_adapters_staging: {
      title: 'Portal-Specific Adapters & Robust Staging',
      phase: 'Phase 10 (Active)',
      icon: <Layers size={24} color="#34d399" />,
      status: 'active',
      description:
        'Isolated portal-specific Playwright adapters (Greenhouse, Lever, Ashby, Workday, Generic), layout change resilience, screening answer mapping, global safety guard enforcement, and automated human handoff.',
      inputs: ['Approved Application Dossier', 'Target ATS Portal (Greenhouse / Lever / Ashby / Workday)'],
      outputs: ['High-Reliability Pre-Filled Form', 'Screening Answers Mapped', 'Layout Verification', 'Safety Screenshot'],
      tables: ['applications', 'browser_preparation_runs', 'audit_logs'],
      contract: `// Phase 10 Portal Adapters Contract
interface PortalAdapterExecutionContract {
  portal_adapter: 'greenhouse' | 'lever' | 'ashby' | 'workday' | 'generic';
  layout_valid: boolean;
  fields_mapped_count: number;
  unresolved_questions: Array<{ field: string; reason: string }>;
  captcha_paused: boolean;
  auth_wall_paused: boolean;
  submit_avoided: true; // INVARIANT
}`,
    },
  };

  const currentDetail = stageDetails[selectedStage] || stageDetails['jd_analysis_matching'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          End-to-End Pipeline Architecture
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Sequential, human-in-the-loop autonomous pipeline architecture. Phase 5 delivers prompt-isolated structured JD analysis and dual deterministic/semantic candidate matching.
        </p>
      </div>

      {/* Visual Pipeline Flowchart */}
      <div
        className="card"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
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
                border: `1px solid ${isSelected ? '#c084fc' : isActive ? '#10b981' : 'var(--border-color)'}`,
                backgroundColor: isSelected ? 'rgba(192, 132, 252, 0.1)' : isActive ? 'rgba(16, 185, 129, 0.12)' : '#131b2e',
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
      <div className="card" style={{ borderTop: `3px solid ${currentDetail.status === 'active' ? '#c084fc' : '#64748b'}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {currentDetail.icon}
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{currentDetail.title}</h3>
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem' }}>
                <span className="badge badge-purple">{currentDetail.phase}</span>
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
