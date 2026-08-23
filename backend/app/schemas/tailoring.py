from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ResumeTailoringRequest(BaseModel):
    """Request payload to generate tailored application materials."""

    candidate_profile_id: Optional[int] = Field(None, description="Candidate profile ID (defaults to primary verified profile)")
    tone: str = Field("professional", description="Tone for cover letter and summary (e.g. professional, confident, technical)")
    target_role_title: Optional[str] = Field(None, description="Optional custom target role title")
    custom_instructions: Optional[str] = Field(None, description="Special instructions for tailoring")


class TailoredResumeResponse(BaseModel):
    """Tailored resume and cover letter artifact."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    candidate_profile_id: Optional[int] = None
    base_resume_id: Optional[int] = None
    tailored_summary: Optional[str] = None
    tailored_experience: List[Dict[str, Any]] = Field(default_factory=list)
    highlighted_skills: List[str] = Field(default_factory=list)
    cover_letter: Optional[str] = None
    markdown_content: Optional[str] = None
    diff_summary: Optional[str] = None
    model_used: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class TailoredResumeListResponse(BaseModel):
    items: List[TailoredResumeResponse]
    total: int
    page: int = 1
    page_size: int = 20
