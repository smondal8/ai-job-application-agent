import {
  HealthResponse,
  ReadinessResponse,
  SystemConfigResponse,
  PipelineStageInfo,
  Job,
  JobListResponse,
  Company,
  CompanyListResponse,
  JobIngestionBatch,
  JobIngestionBatchListResponse,
  SearchCriteria,
  AdapterInfo,
  DiscoveryRun,
  DiscoveryRunListResponse,
  SearchProfile,
  SearchProfileListResponse,
  LLMStatusResponse,
  JobAnalysis,
  JobAnalysisListResponse,
  TailoredResume,
  TailoredResumeListResponse,
  ResumeTailoringRequest,
  TailoredResumeApprovalRequest,
  ApplicationListResponse,
  ApplicationCreateRequest,
  ApplicationUpdateRequest,
  ApplicationDossier,
  ApplicationStats,
  ApplicationReview,
  APIErrorResponse,
  CandidateProfile,
  WorkExperience,
  Education,
  CandidateSkill,
  Project,
  RawResumeImport,
  VerifiedGroundTruthContextResponse,
} from '../types';

const API_BASE = '/api/v1';

export class ApiError extends Error {
  response: APIErrorResponse;
  status: number;

  constructor(status: number, response: APIErrorResponse) {
    super(response.error.message);
    this.name = 'ApiError';
    this.status = status;
    this.response = response;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorJson: APIErrorResponse;
    try {
      errorJson = await res.json();
    } catch {
      errorJson = {
        error: {
          code: `HTTP_${res.status}`,
          message: res.statusText || 'Unknown server error',
          timestamp: new Date().toISOString(),
        },
      };
    }
    throw new ApiError(res.status, errorJson);
  }
  if (res.status === 204) {
    return {} as T;
  }
  return res.json();
}

export interface JobFilterParams {
  search?: string;
  company?: string;
  location?: string;
  remote_type?: string;
  seniority_level?: string;
  status?: string;
  min_salary?: number;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export const api = {
  // --- Diagnostics & Config ---
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch('/health');
    return handleResponse<HealthResponse>(res);
  },

  async getReadiness(): Promise<ReadinessResponse> {
    const res = await fetch('/health/ready');
    return handleResponse<ReadinessResponse>(res);
  },

  async getConfig(): Promise<SystemConfigResponse> {
    const res = await fetch(`${API_BASE}/config`);
    return handleResponse<SystemConfigResponse>(res);
  },

  async getPipelineStages(): Promise<PipelineStageInfo[]> {
    const res = await fetch(`${API_BASE}/pipeline`);
    return handleResponse<PipelineStageInfo[]>(res);
  },

  async testError(errorType: string): Promise<any> {
    const res = await fetch(`${API_BASE}/test-error?error_type=${errorType}`);
    return handleResponse<any>(res);
  },

  // --- Phase 7: Central Application Dashboard & Review ---
  async getApplications(params: {
    status?: string;
    company?: string;
    portal_type?: string;
    job_id?: number;
    search?: string;
    page?: number;
    page_size?: number;
  } = {}): Promise<ApplicationListResponse> {
    const query = new URLSearchParams();
    if (params.status && params.status !== 'all') query.append('status', params.status);
    if (params.company && params.company !== 'all') query.append('company', params.company);
    if (params.portal_type && params.portal_type !== 'all') query.append('portal_type', params.portal_type);
    if (params.job_id) query.append('job_id', params.job_id.toString());
    if (params.search) query.append('search', params.search);
    if (params.page) query.append('page', params.page.toString());
    if (params.page_size) query.append('page_size', params.page_size.toString());

    const res = await fetch(`${API_BASE}/applications?${query.toString()}`);
    return handleResponse<ApplicationListResponse>(res);
  },

  async getApplication(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/applications/${id}`);
    return handleResponse<any>(res);
  },

  async getApplicationDossier(id: number): Promise<ApplicationDossier> {
    const res = await fetch(`${API_BASE}/applications/${id}/dossier`);
    return handleResponse<ApplicationDossier>(res);
  },

  async createApplication(payload: ApplicationCreateRequest): Promise<any> {
    const res = await fetch(`${API_BASE}/applications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async updateApplication(id: number, payload: ApplicationUpdateRequest): Promise<any> {
    const res = await fetch(`${API_BASE}/applications/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async linkResumeToApplication(id: number, tailoredResumeId: number): Promise<any> {
    const res = await fetch(`${API_BASE}/applications/${id}/link-resume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tailored_resume_id: tailoredResumeId }),
    });
    return handleResponse<any>(res);
  },

  async addApplicationReview(id: number, payload: { reviewer_notes?: string; decision?: string; manual_edits?: any }): Promise<ApplicationReview> {
    const res = await fetch(`${API_BASE}/applications/${id}/reviews`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<ApplicationReview>(res);
  },

  async getApplicationStats(): Promise<ApplicationStats> {
    const res = await fetch(`${API_BASE}/applications/stats/summary`);
    return handleResponse<ApplicationStats>(res);
  },

  // --- Phase 8: Human Approval Security Gate & Authorization ---
  async approveApplication(
    id: number,
    payload?: { approver_notes?: string; approver_id?: string }
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/applications/${id}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {}),
    });
    return handleResponse<any>(res);
  },

  async verifyApplicationApproval(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/applications/${id}/verify-approval`);
    return handleResponse<any>(res);
  },

  async revokeApplicationApproval(id: number, reason: string = 'Revoked by user'): Promise<any> {
    const res = await fetch(`${API_BASE}/applications/${id}/revoke-approval?reason=${encodeURIComponent(reason)}`, {
      method: 'POST',
    });
    return handleResponse<any>(res);
  },

  async rejectApplication(id: number, reason?: string): Promise<any> {
    const url = reason
      ? `${API_BASE}/applications/${id}/reject?reason=${encodeURIComponent(reason)}`
      : `${API_BASE}/applications/${id}/reject`;
    const res = await fetch(url, {
      method: 'POST',
    });
    return handleResponse<any>(res);
  },

  async authorizePreparation(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/applications/${id}/authorize-preparation`, {
      method: 'POST',
    });
    return handleResponse<any>(res);
  },

  // --- Phase 9: Playwright Browser Application Preparation ---
  async prepareApplication(
    id: number,
    payload: { custom_portal_url?: string; headless?: boolean } = {}
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/applications/${id}/prepare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async getPreparationRuns(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/applications/${id}/preparation-runs`);
    return handleResponse<any>(res);
  },

  async getLatestPreparationRun(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/applications/${id}/preparation-runs/latest`);
    return handleResponse<any>(res);
  },

  async continueAfterVerification(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/applications/${id}/continue-after-verification`, {
      method: 'POST',
    });
    return handleResponse<any>(res);
  },

  async openOrFocusBrowserSession(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/applications/${id}/browser-session/open`, {
      method: 'POST',
    });
    return handleResponse<any>(res);
  },

  async focusBrowserSession(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/applications/${id}/browser-session/focus`, {
      method: 'POST',
    });
    return handleResponse<any>(res);
  },

  async getBrowserSessionStatus(id: number): Promise<any> {
    const res = await fetch(`${API_BASE}/applications/${id}/browser-session/status`);
    return handleResponse<any>(res);
  },

  async deleteApplication(id: number): Promise<void> {
    const res = await fetch(`${API_BASE}/applications/${id}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(res);
  },

  // --- Phase 6: Grounded Resume Tailoring & Document Compilation ---
  async tailorResume(jobId: number, payload?: ResumeTailoringRequest): Promise<TailoredResume> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/tailor-resume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {}),
    });
    return handleResponse<TailoredResume>(res);
  },

  async getJobTailoredResume(jobId: number): Promise<TailoredResume> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/tailored-resume`);
    return handleResponse<TailoredResume>(res);
  },

  async getTailoredResumes(params: {
    page?: number;
    page_size?: number;
    status?: string;
    validation_status?: string;
  } = {}): Promise<TailoredResumeListResponse> {
    const query = new URLSearchParams();
    if (params.page) query.append('page', params.page.toString());
    if (params.page_size) query.append('page_size', params.page_size.toString());
    if (params.status && params.status !== 'all') query.append('status', params.status);
    if (params.validation_status && params.validation_status !== 'all') query.append('validation_status', params.validation_status);

    const res = await fetch(`${API_BASE}/tailored-resumes?${query.toString()}`);
    return handleResponse<TailoredResumeListResponse>(res);
  },

  async getTailoredResumeById(id: number): Promise<TailoredResume> {
    const res = await fetch(`${API_BASE}/tailored-resumes/${id}`);
    return handleResponse<TailoredResume>(res);
  },

  async approveTailoredResume(id: number, payload?: TailoredResumeApprovalRequest): Promise<TailoredResume> {
    const res = await fetch(`${API_BASE}/tailored-resumes/${id}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {}),
    });
    return handleResponse<TailoredResume>(res);
  },

  downloadDocumentUrl(id: number, format: 'markdown' | 'text' | 'html' | 'cover_letter' = 'markdown'): string {
    return `${API_BASE}/tailored-resumes/${id}/download?format=${format}`;
  },

  // --- Phase 5: Local LLM JD Analysis & Candidate Matching ---
  async getLLMStatus(): Promise<LLMStatusResponse> {
    const res = await fetch(`${API_BASE}/llm/status`);
    return handleResponse<LLMStatusResponse>(res);
  },

  async analyzeJob(jobId: number, payload?: { candidate_profile_id?: number; custom_instructions?: string }): Promise<JobAnalysis> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {}),
    });
    return handleResponse<JobAnalysis>(res);
  },

  async getJobAnalysis(jobId: number): Promise<JobAnalysis> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/analysis`);
    return handleResponse<JobAnalysis>(res);
  },

  async getJobAnalyses(params: {
    page?: number;
    page_size?: number;
    fit_level?: string;
    recommendation?: string;
  } = {}): Promise<JobAnalysisListResponse> {
    const query = new URLSearchParams();
    if (params.page) query.append('page', params.page.toString());
    if (params.page_size) query.append('page_size', params.page_size.toString());
    if (params.fit_level && params.fit_level !== 'all') query.append('fit_level', params.fit_level);
    if (params.recommendation && params.recommendation !== 'all') query.append('recommendation', params.recommendation);

    const res = await fetch(`${API_BASE}/analyses?${query.toString()}`);
    return handleResponse<JobAnalysisListResponse>(res);
  },

  async getAnalysisById(id: number): Promise<JobAnalysis> {
    const res = await fetch(`${API_BASE}/analyses/${id}`);
    return handleResponse<JobAnalysis>(res);
  },

  // --- Phase 4: Job Discovery Framework ---
  async getDiscoveryAdapters(): Promise<AdapterInfo[]> {
    const res = await fetch(`${API_BASE}/discovery/adapters`);
    return handleResponse<AdapterInfo[]>(res);
  },

  async runDiscovery(payload: {
    criteria?: SearchCriteria;
    search_profile_id?: number;
    source?: string;
  }): Promise<DiscoveryRun> {
    const res = await fetch(`${API_BASE}/discovery/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<DiscoveryRun>(res);
  },

  async getDiscoveryRuns(page: number = 1, pageSize: number = 20): Promise<DiscoveryRunListResponse> {
    const res = await fetch(`${API_BASE}/discovery/runs?page=${page}&page_size=${pageSize}`);
    return handleResponse<DiscoveryRunListResponse>(res);
  },

  async getDiscoveryRun(runId: string): Promise<DiscoveryRun> {
    const res = await fetch(`${API_BASE}/discovery/runs/${runId}`);
    return handleResponse<DiscoveryRun>(res);
  },

  async getSearchProfiles(): Promise<SearchProfileListResponse> {
    const res = await fetch(`${API_BASE}/discovery/search-profiles`);
    return handleResponse<SearchProfileListResponse>(res);
  },

  async createSearchProfile(data: {
    name: string;
    description?: string;
    criteria: SearchCriteria;
    is_active?: boolean;
    auto_run_interval_hours?: number;
  }): Promise<SearchProfile> {
    const res = await fetch(`${API_BASE}/discovery/search-profiles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<SearchProfile>(res);
  },

  async deleteSearchProfile(profileId: number): Promise<void> {
    const res = await fetch(`${API_BASE}/discovery/search-profiles/${profileId}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(res);
  },

  // --- Phase 3: Job Database & Ingestion ---
  async getJobs(params: JobFilterParams = {}): Promise<JobListResponse> {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.company) query.append('company', params.company);
    if (params.location) query.append('location', params.location);
    if (params.remote_type && params.remote_type !== 'all') query.append('remote_type', params.remote_type);
    if (params.seniority_level && params.seniority_level !== 'all') query.append('seniority_level', params.seniority_level);
    if (params.status && params.status !== 'all') query.append('status', params.status);
    if (params.min_salary) query.append('min_salary', params.min_salary.toString());
    if (params.is_active !== undefined) query.append('is_active', params.is_active.toString());
    query.append('page', (params.page || 1).toString());
    query.append('page_size', (params.page_size || 20).toString());

    const res = await fetch(`${API_BASE}/jobs?${query.toString()}`);
    return handleResponse<JobListResponse>(res);
  },

  async getJob(id: number): Promise<Job> {
    const res = await fetch(`${API_BASE}/jobs/${id}`);
    return handleResponse<Job>(res);
  },

  async updateJob(id: number, payload: Partial<Job>): Promise<Job> {
    const res = await fetch(`${API_BASE}/jobs/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<Job>(res);
  },

  async archiveJob(id: number): Promise<Job> {
    const res = await fetch(`${API_BASE}/jobs/${id}/archive`, {
      method: 'POST',
    });
    return handleResponse<Job>(res);
  },

  async rejectJob(id: number): Promise<Job> {
    const res = await fetch(`${API_BASE}/jobs/${id}/reject`, {
      method: 'POST',
    });
    return handleResponse<Job>(res);
  },

  async restoreJob(id: number): Promise<Job> {
    const res = await fetch(`${API_BASE}/jobs/${id}/restore`, {
      method: 'POST',
    });
    return handleResponse<Job>(res);
  },

  async ingestJobsJson(jsonPayload: string, source: string = 'json_import'): Promise<JobIngestionBatch> {
    const res = await fetch(`${API_BASE}/jobs/ingest/json`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ json_payload: jsonPayload, source }),
    });
    return handleResponse<JobIngestionBatch>(res);
  },

  async ingestJobsCsv(csvText: string, source: string = 'csv_import'): Promise<JobIngestionBatch> {
    const res = await fetch(`${API_BASE}/jobs/ingest/csv`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ csv_text: csvText, source }),
    });
    return handleResponse<JobIngestionBatch>(res);
  },

  async uploadJobsFile(file: File): Promise<JobIngestionBatch> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/jobs/ingest/file`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<JobIngestionBatch>(res);
  },

  async seedSampleFixtures(): Promise<JobIngestionBatch[]> {
    const res = await fetch(`${API_BASE}/jobs/ingest/seed-fixtures`, {
      method: 'POST',
    });
    return handleResponse<JobIngestionBatch[]>(res);
  },

  async getIngestionBatches(page: number = 1, pageSize: number = 20): Promise<JobIngestionBatchListResponse> {
    const res = await fetch(`${API_BASE}/jobs/ingest/batches?page=${page}&page_size=${pageSize}`);
    return handleResponse<JobIngestionBatchListResponse>(res);
  },

  async getCompanies(search?: string, page: number = 1, pageSize: number = 50): Promise<CompanyListResponse> {
    const url = search
      ? `${API_BASE}/companies?search=${encodeURIComponent(search)}&page=${page}&page_size=${pageSize}`
      : `${API_BASE}/companies?page=${page}&page_size=${pageSize}`;
    const res = await fetch(url);
    return handleResponse<CompanyListResponse>(res);
  },

  async getCompany(id: number): Promise<Company> {
    const res = await fetch(`${API_BASE}/companies/${id}`);
    return handleResponse<Company>(res);
  },

  // --- Phase 2: Candidate Profile & Ground Truth ---
  async getPrimaryProfile(): Promise<CandidateProfile> {
    const res = await fetch(`${API_BASE}/profile`);
    return handleResponse<CandidateProfile>(res);
  },

  async createProfile(data: Partial<CandidateProfile>): Promise<CandidateProfile> {
    const res = await fetch(`${API_BASE}/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<CandidateProfile>(res);
  },

  async updateProfile(profileId: number, data: Partial<CandidateProfile>): Promise<CandidateProfile> {
    const res = await fetch(`${API_BASE}/profile/${profileId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<CandidateProfile>(res);
  },

  async verifyProfile(profileId: number, verifyAllChildren: boolean = true): Promise<CandidateProfile> {
    const res = await fetch(`${API_BASE}/profile/${profileId}/verify?verify_all_children=${verifyAllChildren}`, {
      method: 'POST',
    });
    return handleResponse<CandidateProfile>(res);
  },

  async getVerifiedGroundTruthContext(profileId: number): Promise<VerifiedGroundTruthContextResponse> {
    const res = await fetch(`${API_BASE}/profile/${profileId}/verified-context`);
    return handleResponse<VerifiedGroundTruthContextResponse>(res);
  },

  // Work Experiences
  async addExperience(profileId: number, data: any): Promise<WorkExperience> {
    const res = await fetch(`${API_BASE}/profile/${profileId}/experiences`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<WorkExperience>(res);
  },

  async updateExperience(expId: number, data: any): Promise<WorkExperience> {
    const res = await fetch(`${API_BASE}/profile/experiences/${expId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<WorkExperience>(res);
  },

  async deleteExperience(expId: number): Promise<void> {
    const res = await fetch(`${API_BASE}/profile/experiences/${expId}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(res);
  },

  async toggleExperienceVerification(expId: number, verified: boolean): Promise<WorkExperience> {
    const res = await fetch(`${API_BASE}/profile/experiences/${expId}/verify?verified=${verified}`, {
      method: 'POST',
    });
    return handleResponse<WorkExperience>(res);
  },

  // Educations
  async addEducation(profileId: number, data: any): Promise<Education> {
    const res = await fetch(`${API_BASE}/profile/${profileId}/educations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<Education>(res);
  },

  async deleteEducation(eduId: number): Promise<void> {
    const res = await fetch(`${API_BASE}/profile/educations/${eduId}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(res);
  },

  async toggleEducationVerification(eduId: number, verified: boolean): Promise<Education> {
    const res = await fetch(`${API_BASE}/profile/educations/${eduId}/verify?verified=${verified}`, {
      method: 'POST',
    });
    return handleResponse<Education>(res);
  },

  // Skills
  async addSkill(profileId: number, data: any): Promise<CandidateSkill> {
    const res = await fetch(`${API_BASE}/profile/${profileId}/skills`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<CandidateSkill>(res);
  },

  async addSkillsBulk(profileId: number, skills: any[]): Promise<CandidateSkill[]> {
    const res = await fetch(`${API_BASE}/profile/${profileId}/skills/bulk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skills }),
    });
    return handleResponse<CandidateSkill[]>(res);
  },

  async deleteSkill(skillId: number): Promise<void> {
    const res = await fetch(`${API_BASE}/profile/skills/${skillId}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(res);
  },

  async toggleSkillVerification(skillId: number, verified: boolean): Promise<CandidateSkill> {
    const res = await fetch(`${API_BASE}/profile/skills/${skillId}/verify?verified=${verified}`, {
      method: 'POST',
    });
    return handleResponse<CandidateSkill>(res);
  },

  // Projects
  async addProject(profileId: number, data: any): Promise<Project> {
    const res = await fetch(`${API_BASE}/profile/${profileId}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<Project>(res);
  },

  async deleteProject(projId: number): Promise<void> {
    const res = await fetch(`${API_BASE}/profile/projects/${projId}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(res);
  },

  async toggleProjectVerification(projId: number, verified: boolean): Promise<Project> {
    const res = await fetch(`${API_BASE}/profile/projects/${projId}/verify?verified=${verified}`, {
      method: 'POST',
    });
    return handleResponse<Project>(res);
  },

  // Raw Resume Ingestion
  async importRawResumeText(rawText: string, label?: string, profileId?: number): Promise<RawResumeImport> {
    const url = profileId ? `${API_BASE}/resumes/imports/text?profile_id=${profileId}` : `${API_BASE}/resumes/imports/text`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_text: rawText, label }),
    });
    return handleResponse<RawResumeImport>(res);
  },

  async uploadRawResumeFile(file: File, profileId?: number): Promise<RawResumeImport> {
    const formData = new FormData();
    formData.append('file', file);
    if (profileId) {
      formData.append('profile_id', profileId.toString());
    }
    const res = await fetch(`${API_BASE}/resumes/imports/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<RawResumeImport>(res);
  },

  async applyImportToProfile(importId: number, profileId?: number): Promise<CandidateProfile> {
    const url = profileId
      ? `${API_BASE}/resumes/imports/${importId}/apply-to-profile?profile_id=${profileId}`
      : `${API_BASE}/resumes/imports/${importId}/apply-to-profile`;
    const res = await fetch(url, {
      method: 'POST',
    });
    return handleResponse<CandidateProfile>(res);
  },

  // --- Phase 11: Hardening, Observability, Resilience & Disaster Recovery ---
  async getSystemMetrics(): Promise<import('../types').SystemMetricsResponse> {
    const res = await fetch(`${API_BASE}/system/metrics`);
    return handleResponse<import('../types').SystemMetricsResponse>(res);
  },

  async recoverStaleTasks(maxAgeMinutes: number = 15): Promise<import('../types').CrashRecoveryResponse> {
    const res = await fetch(`${API_BASE}/system/recover-stale?max_age_minutes=${maxAgeMinutes}`, {
      method: 'POST',
    });
    return handleResponse<import('../types').CrashRecoveryResponse>(res);
  },

  async listBackups(): Promise<import('../types').BackupMetadata[]> {
    const res = await fetch(`${API_BASE}/system/backups`);
    return handleResponse<import('../types').BackupMetadata[]>(res);
  },

  async createBackup(includeArtifacts: boolean = true): Promise<import('../types').BackupMetadata> {
    const res = await fetch(`${API_BASE}/system/backups?include_artifacts=${includeArtifacts}`, {
      method: 'POST',
    });
    return handleResponse<import('../types').BackupMetadata>(res);
  },

  async verifyBackup(backupId: string): Promise<import('../types').BackupVerificationResponse> {
    const res = await fetch(`${API_BASE}/system/backups/${backupId}/verify`, {
      method: 'POST',
    });
    return handleResponse<import('../types').BackupVerificationResponse>(res);
  },

  async restoreBackup(backupId: string): Promise<import('../types').BackupRestoreResponse> {
    const res = await fetch(`${API_BASE}/system/backups/${backupId}/restore`, {
      method: 'POST',
    });
    return handleResponse<import('../types').BackupRestoreResponse>(res);
  },

  async redactSensitiveData(payload: any): Promise<any> {
    const res = await fetch(`${API_BASE}/system/redact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },
};
