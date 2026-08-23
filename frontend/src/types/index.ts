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

export interface Job {
  id: number;
  external_id?: string | null;
  title: string;
  company: string;
  location?: string | null;
  remote_type?: string | null;
  job_type?: string | null;
  url?: string | null;
  source: string;
  salary_min?: string | number | null;
  salary_max?: string | number | null;
  currency: string;
  status: string;
  posted_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobListResponse {
  items: Job[];
  total: number;
  page: number;
  page_size: number;
}

// --- Phase 2 Candidate Profile Types ---

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
