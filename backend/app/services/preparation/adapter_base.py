import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.models.job import Job
from app.models.candidate import CandidateProfile
from app.models.resume import TailoredResume
from app.services.preparation.safety_guard import PlaywrightSafetyGuard

logger = get_logger("app.services.preparation.adapter_base")


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
    status: str  # staged, paused_for_human_input, blocked_by_captcha, blocked_by_auth, unsupported_layout, failed
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
        """Name of the portal (e.g., generic, greenhouse, lever, ashby, workday)."""
        pass

    @abstractmethod
    def can_handle(self, portal_type: str, url: str) -> bool:
        """Determines if this adapter can handle the given portal type or URL."""
        pass

    @abstractmethod
    async def prepare(self, page: Any, context: PreparationContext) -> PreparationResult:
        """Pre-fills fields, uploads resume, maps answers, captures screenshots, and stops at submit button."""
        pass

    async def check_global_safety_guards(self, page: Any, context: PreparationContext, start_time: float) -> Optional[PreparationResult]:
        """Runs universal safety checks (CAPTCHA / bot challenges, auth walls). Returns PreparationResult if blocked."""
        # 1. Non-negotiable Check: CAPTCHA / Bot challenge detection
        if await PlaywrightSafetyGuard.detect_captcha(page):
            screenshot_path = await self.capture_screenshot(page, context, "captcha_blocked")
            return PreparationResult(
                application_id=context.application_id,
                approval_token=context.approval_token,
                portal_type=self.portal_name,
                status="blocked_by_captcha",
                captcha_detected=True,
                screenshot_path=screenshot_path,
                error_message="CAPTCHA or bot protection challenge detected. Execution safely paused for human intervention.",
                duration_ms=(time.time() - start_time) * 1000,
            )

        # 2. Non-negotiable Check: Authentication wall detection
        if await PlaywrightSafetyGuard.detect_auth_wall(page):
            screenshot_path = await self.capture_screenshot(page, context, "auth_blocked")
            return PreparationResult(
                application_id=context.application_id,
                approval_token=context.approval_token,
                portal_type=self.portal_name,
                status="blocked_by_auth",
                auth_required=True,
                screenshot_path=screenshot_path,
                error_message="Authentication wall or login required. Execution safely paused for human intervention.",
                duration_ms=(time.time() - start_time) * 1000,
            )

        return None

    async def verify_submit_guard(self, page: Any) -> bool:
        """Verifies presence of submission triggers and logs safety guard status."""
        for submit_sel in PlaywrightSafetyGuard.SUBMIT_SELECTORS:
            try:
                if await page.locator(submit_sel).count() > 0:
                    logger.info(f"[{self.portal_name}] Submit guard active: Detected submit element '{submit_sel}'. Halting at staged checkpoint.")
                    return True
            except Exception:
                continue
        return False

    async def capture_screenshot(self, page: Any, context: PreparationContext, label: str) -> str:
        """Helper to capture full-page screenshot and return file path."""
        try:
            context.screenshot_dir.mkdir(parents=True, exist_ok=True)
            filename = f"app_{context.application_id}_{self.portal_name}_{label}_{int(time.time())}.png"
            full_path = context.screenshot_dir / filename
            await page.screenshot(path=str(full_path), full_page=True)
            return str(full_path)
        except Exception as e:
            logger.warning(f"Failed to capture screenshot: {e}")
            return ""
