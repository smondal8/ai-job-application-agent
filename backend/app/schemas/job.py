from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class JobBase(BaseModel):
    """Base fields shared across Job schemas."""
    title: str = Field(..., min_length=1, max_length=255, examples=["Senior Software Engineer"])
    company: str = Field(..., min_length=1, max_length=255, examples=["Anthropic"])
    location: Optional[str] = Field(None, max_length=255, examples=["San Francisco, CA"])
    remote_type: Optional[str] = Field("unspecified", max_length=50, examples=["hybrid"])
    job_type: Optional[str] = Field("full-time", max_length=50, examples=["full-time"])
    url: Optional[str] = Field(None, max_length=1024, examples=["https://jobs.lever.co/example/123"])
    source: str = Field("manual", max_length=100, examples=["manual"])
    description_raw: Optional[str] = Field(None, examples=["Job description text..."])
    description_clean: Optional[str] = Field(None)
    salary_min: Optional[Decimal] = Field(None, ge=0)
    salary_max: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field("USD", max_length=10)
    status: str = Field("discovered", max_length=50)
    posted_at: Optional[datetime] = None


class JobCreate(JobBase):
    """Schema for registering or importing a job manually."""
    external_id: Optional[str] = Field(None, max_length=255)


class JobUpdate(BaseModel):
    """Schema for partial update of a job listing."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    company: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = None
    remote_type: Optional[str] = None
    job_type: Optional[str] = None
    url: Optional[str] = None
    description_raw: Optional[str] = None
    description_clean: Optional[str] = None
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    currency: Optional[str] = None
    status: Optional[str] = None


class JobResponse(JobBase):
    """Schema for job details response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class JobListResponse(BaseModel):
    """List response for jobs."""
    items: List[JobResponse]
    total: int
    page: int
    page_size: int
