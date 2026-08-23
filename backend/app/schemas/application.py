from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ApplicationBase(BaseModel):
    """Base fields for Application schema."""
    job_id: int
    tailored_resume_id: Optional[int] = None
    status: str = Field("draft", max_length=50)
    portal_type: str = Field("generic", max_length=100)
    portal_url: Optional[str] = None
    cover_letter: Optional[str] = None
    answers_payload: Optional[Dict[str, Any]] = Field(default_factory=dict)
    submission_notes: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationResponse(ApplicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    error_message: Optional[str] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ApplicationListResponse(BaseModel):
    items: List[ApplicationResponse]
    total: int
