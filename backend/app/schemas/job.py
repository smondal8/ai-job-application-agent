from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class JobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, examples=["Senior Backend Engineer"])
    company: str = Field(..., min_length=1, max_length=255, examples=["Stripe"])
    location: Optional[str] = Field(None, max_length=255, examples=["San Francisco, CA"])
    department: Optional[str] = Field(None, max_length=100, examples=["Core Infrastructure"])
    remote_type: Optional[str] = Field("unspecified", max_length=50, examples=["remote", "hybrid", "on_site"])
    workplace_type: Optional[str] = Field("unspecified", max_length=50)
    job_type: Optional[str] = Field("full-time", max_length=50, examples=["full-time", "contract"])
    employment_type: Optional[str] = Field("full_time", max_length=50)
    seniority_level: Optional[str] = Field(None, max_length=50, examples=["senior", "staff", "lead"])
    experience_years_min: Optional[int] = Field(None, ge=0)
    experience_years_max: Optional[int] = Field(None, ge=0)
    url: Optional[str] = Field(None, max_length=1024, examples=["https://stripe.com/jobs/123"])
    source: str = Field("manual", max_length=100, examples=["json_import", "csv_import", "manual"])
    description_raw: Optional[str] = None
    description_clean: Optional[str] = None
    salary_min: Optional[Decimal] = Field(None, ge=0)
    salary_max: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field("USD", max_length=10)
    skills_raw: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    metadata_extra: Dict[str, Any] = Field(default_factory=dict)
    status: str = Field("discovered", max_length=50)
    is_active: bool = Field(True)


class JobCreate(JobBase):
    external_id: Optional[str] = None
    company_id: Optional[int] = None
    posted_at: Optional[datetime] = None


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None
    remote_type: Optional[str] = None
    workplace_type: Optional[str] = None
    job_type: Optional[str] = None
    employment_type: Optional[str] = None
    seniority_level: Optional[str] = None
    experience_years_min: Optional[int] = None
    experience_years_max: Optional[int] = None
    url: Optional[str] = None
    source: Optional[str] = None
    description_raw: Optional[str] = None
    description_clean: Optional[str] = None
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    currency: Optional[str] = None
    skills_raw: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    posted_at: Optional[datetime] = None


class JobResponse(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: Optional[str] = None
    company_id: Optional[int] = None
    batch_id: Optional[str] = None
    dedup_hash: Optional[str] = None
    normalized_company: Optional[str] = None
    normalized_title: Optional[str] = None
    normalized_location: Optional[str] = None
    posted_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int
    page: int
    page_size: int
