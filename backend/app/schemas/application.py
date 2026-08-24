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


# --- Phase 8 Human Approval & Security Schemas ---

class ApplicationApprovalRequest(BaseModel):
    """Request payload to grant human approval bound to material input hashes."""
    approver_notes: Optional[str] = Field(None, description="Reviewer justification or sign-off notes")
    approver_id: str = Field("human_reviewer", description="Identifier of the approving reviewer")


class ApplicationApprovalResponse(BaseModel):
    """Cryptographic approval certificate record."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    status: str
    job_id: int
    approved_job_hash: str
    candidate_profile_id: Optional[int] = None
    approved_candidate_hash: str
    tailored_resume_id: Optional[int] = None
    approved_resume_hash: str
    approved_answers_hash: str
    approval_token: str
    approver_id: str
    approver_notes: Optional[str] = None
    is_valid: bool
    invalidation_reason: Optional[str] = None
    invalidated_at: Optional[datetime] = None
    approved_at: datetime
    created_at: datetime
    updated_at: datetime


class ApprovalVerificationResponse(BaseModel):
    """Integrity verification response checking active approval against live input hashes."""
    is_valid: bool
    is_approved: bool
    application_id: int
    current_status: str
    reason: Optional[str] = None
    approval_token: Optional[str] = None
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
    hashes: Optional[Dict[str, str]] = None
    mismatches: List[str] = Field(default_factory=list)


class PreparationAuthorizationResponse(BaseModel):
    """Server-side security authorization certificate required before starting browser preparation."""
    authorization_granted: bool
    application_id: int
    approval_token: str
    status: str
    authorized_at: str
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
    snapshot_hashes: Optional[Dict[str, str]] = None


class ApplicationResponse(ApplicationBase):
    """Standard application response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    approval_token: Optional[str] = None
    approved_at: Optional[datetime] = None
    invalidation_reason: Optional[str] = None
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
    approval_token: Optional[str] = None
    approved_at: Optional[str] = None
    invalidation_reason: Optional[str] = None
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
    """Complete application dossier aggregating Job, Tailored Resume, Analysis, Candidate, Approvals, and Reviews."""
    application: Dict[str, Any]
    job: Dict[str, Any]
    tailored_resume: Optional[Dict[str, Any]] = None
    available_resumes: List[Dict[str, Any]] = Field(default_factory=list)
    analysis: Optional[Dict[str, Any]] = None
    candidate: Optional[Dict[str, Any]] = None
    approval: Optional[Dict[str, Any]] = None
    reviews: List[Dict[str, Any]] = Field(default_factory=list)


class ApplicationStatsResponse(BaseModel):
    """Application overview metrics and status distribution."""
    total_applications: int
    status_counts: Dict[str, int]
    portal_counts: Dict[str, int]
