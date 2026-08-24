export interface DatabaseHealth {
  status: string;
  connected: boolean;
  latency_ms: number;
  dialect: string;
  database_target?: string | null;
  error?: string | null;
}

export interface StorageHealth {
  status: string;
  storage_dir: string;
  writable: boolean;
  error?: string | null;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  uptime_seconds: number;
  environment: string;
  database: DatabaseHealth;
  storage: StorageHealth;
}

export interface ReadinessResponse {
  ready: boolean;
  status: string;
  timestamp: string;
  checks: {
    database: boolean;
    storage: boolean;
    [key: string]: boolean;
  };
}

export interface PipelineStageInfo {
  stage_id: string;
  name: string;
  status: 'ready' | 'active' | 'planned' | 'disabled';
  description: string;
  active: boolean;
}

export interface SystemConfigResponse {
  app_name: string;
  app_version: string;
  environment: string;
  debug: boolean;
  api_v1_prefix: string;
  database_type: string;
  storage_dir: string;
  log_level: string;
  log_format: string;
  llm_provider?: string;
  llm_model?: string;
  llm_base_url?: string;
  pipeline_stages: PipelineStageInfo[];
}

export interface APIErrorDetail {
  location?: string;
  message?: string;
  type?: string;
  [key: string]: any;
}

export interface APIErrorResponse {
  error: {
    code: string;
    message: string;
    details?: APIErrorDetail[] | Record<string, any> | string | null;
    request_id?: string;
    timestamp: string;
  };
}

// --- Phase 8: Human Approval Security & State Machine Types ---

export interface ApplicationApproval {
  id: number;
  application_id: number;
  status: string;
  job_id: number;
  approved_job_hash: string;
  candidate_profile_id?: number | null;
  approved_candidate_hash: string;
  tailored_resume_id?: number | null;
  approved_resume_hash: string;
  approved_answers_hash: string;
  approval_token: string;
  approver_id: string;
  approver_notes?: string | null;
  is_valid: boolean;
  invalidation_reason?: string | null;
  invalidated_at?: string | null;
  approved_at: string;
  created_at: string;
  updated_at: string;
}

export interface ApprovalVerificationResponse {
  is_valid: boolean;
  is_approved: boolean;
  application_id: number;
  current_status: string;
  reason?: string | null;
  approval_token?: string | null;
  approved_at?: string | null;
  approved_by?: string | null;
  hashes?: {
    job_hash: string;
    candidate_hash: string;
    resume_hash: string;
    answers_hash: string;
  } | null;
  mismatches: string[];
}

export interface PreparationAuthorizationResponse {
  authorization_granted: boolean;
  application_id: number;
  approval_token: string;
  status: string;
  authorized_at: string;
  approved_at?: string | null;
  approved_by?: string | null;
  snapshot_hashes?: Record<string, string> | null;
}

// --- Phase 7: Central Application Dashboard & Review Types ---

export interface ApplicationReview {
  id: number;
  decision: string; // pending, approved, rejected, changes_requested
  reviewer_notes?: string | null;
  manual_edits?: Record<string, any> | null;
  reviewed_at?: string | null;
  created_at?: string | null;
}

export interface ApplicationItem {
  id: number;
  job_id: number;
  tailored_resume_id?: number | null;
  candidate_profile_id?: number | null;
  status: string;
  approval_token?: string | null;
  approved_at?: string | null;
  invalidation_reason?: string | null;
  portal_type: string;
  portal_url?: string | null;
  cover_letter?: string | null;
  answers_payload?: Record<string, any>;
  submission_notes?: string | null;
  reviewer_notes?: string | null;
  error_message?: string | null;
  applied_at?: string | null;
  submitted_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  // Enriched
  job_title: string;
  job_company: string;
  job_location?: string | null;
  job_remote_type?: string | null;
  fit_score?: number | null;
  fit_level?: string | null;
  recommendation?: string | null;
  resume_validation_status?: string | null;
}

export interface ApplicationListResponse {
  items: ApplicationItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApplicationCreateRequest {
  job_id: number;
  tailored_resume_id?: number | null;
  candidate_profile_id?: number | null;
  status?: string | null;
  portal_type?: string;
  portal_url?: string | null;
  cover_letter?: string | null;
  answers_payload?: Record<string, any>;
  submission_notes?: string | null;
}

export interface ApplicationUpdateRequest {
  tailored_resume_id?: number | null;
  candidate_profile_id?: number | null;
  status?: string | null;
  portal_type?: string | null;
  portal_url?: string | null;
  cover_letter?: string | null;
  answers_payload?: Record<string, any> | null;
  submission_notes?: string | null;
  reviewer_notes?: string | null;
}

export interface ApplicationDossier {
  application: {
    id: number;
    job_id: number;
    tailored_resume_id?: number | null;
    candidate_profile_id?: number | null;
    status: string;
    approval_token?: string | null;
    approved_at?: string | null;
    invalidation_reason?: string | null;
    portal_type: string;
    portal_url?: string | null;
    cover_letter?: string | null;
    answers_payload: Record<string, any>;
    submission_notes?: string | null;
    reviewer_notes?: string | null;
    error_message?: string | null;
    applied_at?: string | null;
    submitted_at?: string | null;
    created_at?: string | null;
    updated_at?: string | null;
  };
  job: Job;
  tailored_resume?: TailoredResume | null;
  available_resumes: Array<{
    id: number;
    prompt_version: string;
    validation_status: string;
    model_used?: string | null;
    status: string;
    updated_at?: string | null;
  }>;
  analysis?: JobAnalysis | null;
  candidate?: {
    id: number;
    full_name: string;
    email: string;
    phone?: string | null;
    location?: string | null;
    headline?: string | null;
    is_verified: boolean;
  } | null;
  approval?: ApplicationApproval | null;
  reviews: ApplicationReview[];
}

export interface ApplicationStats {
  total_applications: number;
  status_counts: {
    draft: number;
    ready_for_review: number;
    in_review: number;
    approved_pending_submission: number;
    submitted: number;
    rejected: number;
    archived: number;
  };
  portal_counts: Record<string, number>;
}

// --- Phase 6: Grounded Resume Tailoring & Document Compilation Types ---

export interface UntracedClaim {
  section: string;
  text: string;
  invalid_fact_ids: string[];
  reason: string;
}

export interface ValidationDetails {
  is_valid: boolean;
  traceability_score: number;
  total_claims: number;
  verified_claims: number;
  untraced_claims: UntracedClaim[];
  warnings: string[];
}

export interface ResumeTailoringRequest {
  candidate_profile_id?: number | null;
  tone?: string;
  target_role_title?: string | null;
  custom_instructions?: string | null;
  auto_regenerate_on_untraced?: boolean;
}

export interface TailoredResumeApprovalRequest {
  approver_notes?: string | null;
}

export interface TailoredResume {
  id: number;
  job_id: number;
  candidate_profile_id?: number | null;
  job_analysis_id?: number | null;
  base_resume_id?: number | null;
  prompt_version: string;
  model_used?: string | null;
  generation_metadata?: Record<string, any> | null;
  tailored_summary?: string | null;
  tailored_experience: Array<{
    company: string;
    position: string;
    start_date?: string;
    end_date?: string | null;
    is_current?: boolean;
    tailored_highlights: Array<{
      text: string;
      source_fact_ids: string[];
    }>;
  }>;
  highlighted_skills: string[];
  cover_letter?: string | null;
  cover_letter_paragraphs?: Array<{
    paragraph_type: string;
    text: string;
    source_fact_ids: string[];
  }>;
  diff_summary?: string | null;
  compiled_markdown?: string | null;
  compiled_text?: string | null;
  compiled_html?: string | null;
  markdown_content?: string | null;
  file_path?: string | null;
  traceability_matrix?: Record<string, string[]> | null;
  validation_status: 'valid' | 'requires_human_review' | 'rejected';
  validation_details?: ValidationDetails | null;
  human_approved_at?: string | null;
  human_approver_notes?: string | null;
  status: 'draft' | 'ready_for_review' | 'approved' | 'rejected';
  created_at: string;
  updated_at: string;
}

export interface TailoredResumeListResponse {
  items: TailoredResume[];
  total: number;
  page: number;
  page_size: number;
}

// --- Phase 5: Local LLM JD Analysis & Candidate Matching Types ---

export interface LLMStatusResponse {
  provider: string;
  status: 'connected' | 'disconnected' | 'degraded';
  base_url: string;
  active_model: string;
  is_active_model_available: boolean;
  available_models: string[];
  latency_ms: number;
  error?: string | null;
}

export interface JobAnalysis {
  id: number;
  job_id: number;
  candidate_profile_id?: number | null;
  fit_score?: number | null;
  deterministic_score?: number | null;
  semantic_score?: number | null;
  fit_level?: 'high' | 'medium' | 'low' | null;
  recommendation?: 'strong_apply' | 'apply' | 'stretch' | 'skip' | null;
  summary?: string | null;
  role_summary?: string | null;
  key_responsibilities: string[];
  matched_skills: string[];
  missing_skills: string[];
  required_qualifications: string[];
  preferred_qualifications: string[];
  keywords: string[];
  red_flags: string[];
  model_used?: string | null;
  analysis_metadata?: Record<string, any> | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface JobAnalysisListResponse {
  items: JobAnalysis[];
  total: number;
  page: number;
  page_size: number;
}

// --- Phase 4: Job Discovery & Adapter Types ---

export interface SearchCriteria {
  keywords: string[];
  locations: string[];
  remote_only: boolean;
  target_companies: string[];
  seniority_levels: string[];
  min_salary?: number | null;
  sources: string[];
  max_results_per_source: number;
}

export interface AdapterInfo {
  source_name: string;
  display_name: string;
  description: string;
  is_reliable: boolean;
  requires_auth: boolean;
  supports_search_criteria: boolean;
  rate_limit_per_minute: number;
  fallback_mode?: string | null;
  status: string;
}

export interface DiscoveryRun {
  id: number;
  run_id: string;
  source: string;
  criteria: Record<string, any>;
  total_discovered: number;
  inserted_count: number;
  duplicate_count: number;
  error_count: number;
  status: string;
  duration_ms?: number | null;
  adapter_logs?: Array<Record<string, any>>;
  created_at: string;
  updated_at: string;
}

export interface DiscoveryRunListResponse {
  items: DiscoveryRun[];
  total: number;
  page: number;
  page_size: number;
}

export interface SearchProfile {
  id: number;
  name: string;
  description?: string | null;
  criteria: SearchCriteria;
  is_active: boolean;
  auto_run_interval_hours?: number | null;
  created_at: string;
  updated_at: string;
}

export interface SearchProfileListResponse {
  items: SearchProfile[];
  total: number;
}

// --- Phase 3: Job Database & Ingestion Types ---

export interface Job {
  id: number;
  external_id?: string | null;
  company_id?: number | null;
  batch_id?: string | null;
  title: string;
  company: string;
  location?: string | null;
  department?: string | null;
  dedup_hash?: string | null;
  normalized_company?: string | null;
  normalized_title?: string | null;
  normalized_location?: string | null;
  remote_type?: string | null;
  workplace_type?: string | null;
  job_type?: string | null;
  employment_type?: string | null;
  seniority_level?: string | null;
  experience_years_min?: number | null;
  experience_years_max?: number | null;
  url?: string | null;
  source: string;
  description_raw?: string | null;
  description_clean?: string | null;
  salary_min?: string | number | null;
  salary_max?: string | number | null;
  currency: string;
  skills_raw?: string[];
  benefits?: string[];
  metadata_extra?: Record<string, any>;
  status: string;
  is_active: boolean;
  posted_at?: string | null;
  last_seen_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobListResponse {
  items: Job[];
  total: number;
  page: number;
  page_size: number;
}

export interface Company {
  id: number;
  name: string;
  normalized_name: string;
  domain?: string | null;
  industry?: string | null;
  company_size?: string | null;
  careers_url?: string | null;
  location_headquarters?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CompanyListResponse {
  items: Company[];
  total: number;
}

export interface JobIngestionBatch {
  id?: number;
  batch_id: string;
  source: string;
  filename?: string | null;
  file_hash?: string | null;
  total_records: number;
  inserted_count: number;
  updated_count: number;
  duplicate_count: number;
  error_count: number;
  status: string;
  error_log?: Array<Record<string, any>>;
  created_at?: string;
}

export interface JobIngestionBatchListResponse {
  items: JobIngestionBatch[];
  total: number;
}

// --- Phase 2: Candidate Profile Types ---

export interface WorkExperience {
  id: number;
  profile_id: number;
  company: string;
  position: string;
  location?: string | null;
  start_date: string;
  end_date?: string | null;
  is_current: boolean;
  description?: string | null;
  highlights: string[];
  skills_used: string[];
  is_verified: boolean;
  order_index: number;
  created_at: string;
  updated_at: string;
}

export interface Education {
  id: number;
  profile_id: number;
  institution: string;
  degree: string;
  field_of_study?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  gpa?: string | null;
  highlights: string[];
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface CandidateSkill {
  id: number;
  profile_id: number;
  name: string;
  category: string;
  proficiency: string;
  years_of_experience?: number | null;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: number;
  profile_id: number;
  name: string;
  description?: string | null;
  url?: string | null;
  highlights: string[];
  technologies: string[];
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface CandidateProfile {
  id: number;
  full_name: string;
  email: string;
  phone?: string | null;
  location?: string | null;
  headline?: string | null;
  summary?: string | null;
  website?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  portfolio_url?: string | null;
  is_verified: boolean;
  verified_at?: string | null;
  experiences: WorkExperience[];
  educations: Education[];
  skills: CandidateSkill[];
  projects: Project[];
  created_at: string;
  updated_at: string;
}

export interface RawResumeImport {
  id: number;
  profile_id?: number | null;
  filename: string;
  file_path: string;
  file_hash: string;
  file_size_bytes: number;
  mime_type: string;
  status: string;
  parsed_data?: Record<string, any> | null;
  created_at: string;
}

export interface VerifiedGroundTruthContextResponse {
  profile_id: number;
  profile_verified: boolean;
  verified_at?: string | null;
  candidate: Record<string, any>;
  experiences: Record<string, any>[];
  educations: Record<string, any>[];
  skills: Record<string, any>[];
  projects: Record<string, any>[];
  stats: {
    verified_experiences_count: number;
    verified_educations_count: number;
    verified_skills_count: number;
    verified_projects_count: number;
    total_verified_facts: number;
  };
  formatted_llm_prompt_context: string;
}
