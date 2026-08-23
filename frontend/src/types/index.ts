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
