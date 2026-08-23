from typing import List
from pydantic import BaseModel, Field


class PipelineStageInfo(BaseModel):
    """Information regarding a functional pipeline stage."""
    stage_id: str = Field(..., examples=["job_discovery"])
    name: str = Field(..., examples=["Phase 2: Job Discovery & Scraping"])
    status: str = Field(..., examples=["planned"])  # ready, active, planned, disabled
    description: str = Field(..., examples=["Job board adapters, scrapers, search query filters"])
    active: bool = Field(..., examples=[False])


class SystemConfigResponse(BaseModel):
    """Sanitized system configuration response."""
    app_name: str = Field(..., examples=["AI Job Application Agent"])
    app_version: str = Field(..., examples=["0.1.0"])
    environment: str = Field(..., examples=["development"])
    debug: bool = Field(..., examples=[True])
    api_v1_prefix: str = Field(..., examples=["/api/v1"])
    database_type: str = Field(..., examples=["sqlite"])
    storage_dir: str = Field(..., examples=["./data/storage"])
    log_level: str = Field(..., examples=["INFO"])
    log_format: str = Field(..., examples=["console"])
    pipeline_stages: List[PipelineStageInfo]
