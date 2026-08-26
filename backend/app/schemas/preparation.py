from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class PreparationRunRequest(BaseModel):
    """Request payload to initiate browser application preparation."""

    custom_portal_url: Optional[str] = Field(default=None, description="Optional override URL for testing or fixture execution")
    headless: bool = Field(default=True, description="Run Playwright in headless mode")


class PreparationRunResponse(BaseModel):
    """Audit and result summary of a Playwright browser preparation execution."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    job_id: int
    approval_id: Optional[int] = None
    approval_token: str
    portal_type: str
    portal_url: Optional[str] = None
    status: str
    fields_filled: List[Dict[str, Any]] = Field(default_factory=list)
    unresolved_fields: List[Dict[str, Any]] = Field(default_factory=list)
    resume_uploaded: bool
    resume_file_path: Optional[str] = None
    screenshot_path: Optional[str] = None
    final_submit_clicked: bool
    guard_triggered: bool
    captcha_detected: bool
    auth_required: bool
    error_message: Optional[str] = None
    duration_ms: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class PreparationRunListResponse(BaseModel):
    """List response of browser preparation runs for an application."""

    items: List[PreparationRunResponse]
    total: int


class BrowserSessionResponse(BaseModel):
    """Status and metadata for an active or opened Playwright browser session."""

    session_active: bool = Field(description="Whether a live browser session is active")
    application_id: int
    job_id: Optional[int] = None
    portal_url: Optional[str] = None
    is_headless: Optional[bool] = None
    focused: Optional[bool] = None
    page_alive: Optional[bool] = Field(default=None, description="Whether the Playwright page is currently open and responsive")
    browser_connected: Optional[bool] = Field(default=None, description="Whether the Chromium browser process is connected")
    page_url: Optional[str] = Field(default=None, description="Current live URL of the browser page")
    message: str = Field(description="Status message or user instruction")

