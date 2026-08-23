from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SearchCriteria(BaseModel):
    """Universal search criteria schema for source-agnostic job discovery."""

    keywords: List[str] = Field(default_factory=lambda: ["Software Engineer"])
    locations: List[str] = Field(default_factory=list)
    remote_only: bool = Field(default=False)
    target_companies: List[str] = Field(default_factory=list)
    seniority_levels: List[str] = Field(default_factory=list)
    min_salary: Optional[float] = Field(default=None)
    sources: List[str] = Field(default_factory=lambda: ["greenhouse", "lever", "remote_tech"])
    max_results_per_source: int = Field(default=25, ge=1, le=100)


class DiscoveryRunRequest(BaseModel):
    """Trigger an on-demand discovery run."""

    criteria: Optional[SearchCriteria] = None
    search_profile_id: Optional[int] = None
    source: Optional[str] = Field(default=None, description="Specific single source or null for all matching sources")


class AdapterInfoResponse(BaseModel):
    """Discovery Adapter metadata and capabilities."""

    source_name: str
    display_name: str
    description: str
    is_reliable: bool
    requires_auth: bool
    supports_search_criteria: bool
    rate_limit_per_minute: int
    fallback_mode: Optional[str] = None
    status: str = "active"


class DiscoveryRunResponse(BaseModel):
    """Summary and audit record of a discovery execution."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: str
    source: str
    criteria: Dict[str, Any]
    total_discovered: int
    inserted_count: int
    duplicate_count: int
    error_count: int
    status: str
    duration_ms: Optional[float] = None
    adapter_logs: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime


class DiscoveryRunListResponse(BaseModel):
    items: List[DiscoveryRunResponse]
    total: int
    page: int = 1
    page_size: int = 20


class SearchProfileCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    criteria: SearchCriteria
    is_active: bool = True
    auto_run_interval_hours: Optional[int] = None


class SearchProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    criteria: Dict[str, Any]
    is_active: bool
    auto_run_interval_hours: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class SearchProfileListResponse(BaseModel):
    items: List[SearchProfileResponse]
    total: int
