import {
  HealthResponse,
  ReadinessResponse,
  SystemConfigResponse,
  PipelineStageInfo,
  JobListResponse,
  APIErrorResponse,
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
  return res.json();
}

export const api = {
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
};
