from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ResumeTailoringRequest(BaseModel):
    """Request payload to tailor application materials for a target job."""

    candidate_profile_id: Optional[int] = Field(None, description="Optional specific candidate profile ID")
    tone: str = Field("professional", description="Target tone: professional, confident, technical, or impact_driven")
    target_role_title: Optional[str] = Field(None, description="Optional override title for the target position")
    custom_instructions: Optional[str] = Field(None, description="Optional special tailoring emphasis instructions")
    auto_regenerate_on_untraced: bool = Field(True, description="Automatically retry LLM generation once if untraced claims are detected")


class TailoredResumeApprovalRequest(BaseModel):
    """Request payload for human approval of tailored application materials."""

    approver_notes: Optional[str] = Field(None, description="Optional human reviewer notes on approval")


class TailoredResumeResponse(BaseModel):
    """Grounded tailored resume and application materials with fact traceability."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    candidate_profile_id: Optional[int] = None
    job_analysis_id: Optional[int] = None
    base_resume_id: Optional[int] = None
    
    # Model & Prompt Versioning
    prompt_version: str
    model_used: Optional[str] = None
    generation_metadata: Optional[Dict[str, Any]] = None

    # Structured Tailored Content
    tailored_summary: Optional[str] = None
    tailored_experience: List[Dict[str, Any]] = Field(default_factory=list)
    highlighted_skills: List[str] = Field(default_factory=list)
    cover_letter: Optional[str] = None
    cover_letter_paragraphs: List[Dict[str, Any]] = Field(default_factory=list)
    diff_summary: Optional[str] = None

    # Deterministically Compiled Formats
    compiled_markdown: Optional[str] = None
    compiled_text: Optional[str] = None
    compiled_html: Optional[str] = None
    markdown_content: Optional[str] = None  # Compatibility alias
    file_path: Optional[str] = None

    # Traceability & Validation Subsystem
    traceability_matrix: Optional[Dict[str, Any]] = None
    validation_status: str  # valid, requires_human_review, rejected
    validation_details: Optional[Dict[str, Any]] = None
    human_approved_at: Optional[datetime] = None
    human_approver_notes: Optional[str] = None

    # Status
    status: str  # draft, ready_for_review, approved, rejected
    created_at: datetime
    updated_at: datetime


class TailoredResumeListResponse(BaseModel):
    items: List[TailoredResumeResponse]
    total: int
    page: int = 1
    page_size: int = 20
