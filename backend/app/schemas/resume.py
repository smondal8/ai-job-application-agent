from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ResumeBase(BaseModel):
    """Base fields for master resume."""
    name: str = Field(..., min_length=1, max_length=255, examples=["Principal Engineer Resume"])
    version: str = Field("1.0", max_length=50)
    contact_info: Optional[Dict[str, Any]] = Field(default_factory=dict)
    summary: Optional[str] = None
    skills: Optional[List[str]] = Field(default_factory=list)
    experience: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    education: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    raw_content: Optional[str] = None
    is_default: bool = False


class ResumeCreate(ResumeBase):
    pass


class ResumeResponse(ResumeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ResumeListResponse(BaseModel):
    items: List[ResumeResponse]
    total: int
