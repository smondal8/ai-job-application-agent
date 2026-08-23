import {
  HealthResponse,
  ReadinessResponse,
  SystemConfigResponse,
  PipelineStageInfo,
  JobListResponse,
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

  async getJobs(page: number = 1, pageSize: number = 10): Promise<JobListResponse> {
    const res = await fetch(`${API_BASE}/jobs?page=${page}&page_size=${pageSize}`);
    return handleResponse<JobListResponse>(res);
  },

  async testError(errorType: string): Promise<any> {
    const res = await fetch(`${API_BASE}/test-error?error_type=${errorType}`);
    return handleResponse<any>(res);
  },

  // --- Phase 2: Candidate Profile & Ground Truth ---
  async getPrimaryProfile(): Promise<CandidateProfile> {
    const res = await fetch(`${API_BASE}/profile`);
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
};
