from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class LLMStatusResponse(BaseModel):
    """Local LLM provider connectivity and status info."""

    provider: str = Field(..., examples=["ollama"])
    status: str = Field(..., examples=["connected", "disconnected", "degraded"])
    base_url: str = Field(..., examples=["http://127.0.0.1:11434"])
    active_model: str = Field(..., examples=["qwen3:8b"])
    is_active_model_available: bool = Field(...)
    available_models: List[str] = Field(default_factory=list)
    latency_ms: float = Field(...)
    error: Optional[str] = None


class JobAnalysisRequest(BaseModel):
    """Request payload to trigger LLM analysis on a job description."""

    candidate_profile_id: Optional[int] = Field(None, description="Optional specific candidate profile ID (defaults to primary verified profile)")
    custom_instructions: Optional[str] = Field(None, description="Optional extra evaluation instructions")


class JobAnalysisResponse(BaseModel):
    """Structured JD analysis and candidate alignment report."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    candidate_profile_id: Optional[int] = None
    fit_score: Optional[float] = None  # 0.0 - 100.0
    fit_level: Optional[str] = None  # high, medium, low
    summary: Optional[str] = None
    role_summary: Optional[str] = None
    key_responsibilities: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    required_qualifications: List[str] = Field(default_factory=list)
    preferred_qualifications: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    model_used: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
