from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.models.job import Job
from app.models.candidate import CandidateProfile
from app.models.resume import TailoredResume


@dataclass
class PreparationContext:
    """Immutable data context passed to the browser application preparation adapter."""

    application_id: int
    job: Job
    candidate: CandidateProfile
    tailored_resume: Optional[TailoredResume]
    answers_payload: Dict[str, Any]
    approval_token: str
    portal_url: str
    screenshot_dir: Path
    resume_file_path: Optional[Path] = None


@dataclass
class PreparationResult:
    """Output summary of browser staging actions, field discovery, and safety checkpoints."""

    application_id: int
    approval_token: str
    portal_type: str
    status: str  # staged, paused_for_human_input, blocked_by_captcha, blocked_by_auth, failed
    fields_filled: List[Dict[str, Any]] = field(default_factory=list)
    unresolved_fields: List[Dict[str, Any]] = field(default_factory=list)
    resume_uploaded: bool = False
    resume_file_path: Optional[str] = None
    screenshot_path: Optional[str] = None
    final_submit_clicked: bool = False  # MUST ALWAYS REMAIN FALSE
    guard_triggered: bool = False
    captcha_detected: bool = False
    auth_required: bool = False
    error_message: Optional[str] = None
    duration_ms: float = 0.0


class BasePortalPreparationAdapter(ABC):
    """Abstract Base Class for Portal-specific Playwright browser preparation adapters."""

    @property
    @abstractmethod
    def portal_name(self) -> str:
        """Name of the portal (e.g., generic, greenhouse, lever, ashby)."""
        pass

    @abstractmethod
    def can_handle(self, portal_type: str, url: str) -> bool:
        """Determines if this adapter can handle the given portal type or URL."""
        pass

    @abstractmethod
    async def prepare(self, page: Any, context: PreparationContext) -> PreparationResult:
        """Pre-fills fields, uploads resume, maps answers, captures screenshots, and stops at submit button."""
        pass
