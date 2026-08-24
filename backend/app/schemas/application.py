from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ApplicationBase(BaseModel):
    """Base fields for Application schema."""
    job_id: int
    tailored_resume_id: Optional[int] = None
    candidate_profile_id: Optional[int] = None
    status: str = Field("draft", max_length=50)
    portal_type: str = Field("generic", max_length=100)
    portal_url: Optional[str] = None
    cover_letter: Optional[str] = None
    answers_payload: Optional[Dict[str, Any]] = Field(default_factory=dict)
    submission_notes: Optional[str] = None
    reviewer_notes: Optional[str] = None


class ApplicationCreate(BaseModel):
    """Request payload to create a new application linked to a job."""
    job_id: int
    tailored_resume_id: Optional[int] = None
    candidate_profile_id: Optional[int] = None
    status: Optional[str] = None
    portal_type: str = "generic"
    portal_url: Optional[str] = None
    cover_letter: Optional[str] = None
    answers_payload: Optional[Dict[str, Any]] = Field(default_factory=dict)
    submission_notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    """Request payload to update application fields or screening answers."""
    tailored_resume_id: Optional[int] = None
    candidate_profile_id: Optional[int] = None
    status: Optional[str] = None
    portal_type: Optional[str] = None
    portal_url: Optional[str] = None
    cover_letter: Optional[str] = None
    answers_payload: Optional[Dict[str, Any]] = None
    submission_notes: Optional[str] = None
    reviewer_notes: Optional[str] = None
    applied_at: Optional[datetime] = None


class ApplicationLinkResumeRequest(BaseModel):
    """Request payload to link or switch the tailored resume version for an application."""
    tailored_resume_id: int


class ApplicationReviewCreate(BaseModel):
    """Request payload to record a human review note for an application."""
    reviewer_notes: Optional[str] = None
    decision: str = Field("pending", description="pending, approved, rejected, changes_requested")
    manual_edits: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ApplicationResponse(ApplicationBase):
    """Standard application response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    error_message: Optional[str] = None
    applied_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ApplicationItemResponse(BaseModel):
    """Enriched application item for table listings and dashboard grids."""
    id: int
    job_id: int
    tailored_resume_id: Optional[int] = None
    candidate_profile_id: Optional[int] = None
    status: str
    portal_type: str
    portal_url: Optional[str] = None
    cover_letter: Optional[str] = None
    answers_payload: Optional[Dict[str, Any]] = Field(default_factory=dict)
    submission_notes: Optional[str] = None
    reviewer_notes: Optional[str] = None
    error_message: Optional[str] = None
    applied_at: Optional[str] = None
    submitted_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    # Enriched job and match info
    job_title: str
    job_company: str
    job_location: Optional[str] = None
    job_remote_type: Optional[str] = None
    fit_score: Optional[float] = None
    fit_level: Optional[str] = None
    recommendation: Optional[str] = None
    resume_validation_status: Optional[str] = None


class ApplicationListResponse(BaseModel):
    """Paginated application list response."""
    items: List[ApplicationItemResponse]
    total: int
    page: int = 1
    page_size: int = 20


class ApplicationReviewResponse(BaseModel):
    """Application review note entry."""
    id: int
    decision: str
    reviewer_notes: Optional[str] = None
    manual_edits: Optional[Dict[str, Any]] = None
    reviewed_at: Optional[str] = None
    created_at: Optional[str] = None


class ApplicationDossierResponse(BaseModel):
    """Complete application dossier aggregating Job, Tailored Resume, Analysis, and Reviews."""
    application: Dict[str, Any]
    job: Dict[str, Any]
    tailored_resume: Optional[Dict[str, Any]] = None
    available_resumes: List[Dict[str, Any]] = Field(default_factory=list)
    analysis: Optional[Dict[str, Any]] = None
    candidate: Optional[Dict[str, Any]] = None
    reviews: List[Dict[str, Any]] = Field(default_factory=list)


class ApplicationStatsResponse(BaseModel):
    """Application overview metrics and status distribution."""
    total_applications: int
    status_counts: Dict[str, int]
    portal_counts: Dict[str, int]
