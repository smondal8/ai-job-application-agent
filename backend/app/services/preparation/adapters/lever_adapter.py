import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.preparation.adapter_base import (
    BasePortalPreparationAdapter,
    PreparationContext,
    PreparationResult,
)
from app.services.preparation.safety_guard import PlaywrightSafetyGuard

logger = get_logger("app.services.preparation.adapters.lever")


class LeverPreparationAdapter(BasePortalPreparationAdapter):
    """Specialized, high-reliability preparation adapter for Lever (jobs.lever.co) job application forms."""

    @property
    def portal_name(self) -> str:
        return "lever"

    def can_handle(self, portal_type: str, url: str) -> bool:
        if portal_type and portal_type.lower() == "lever":
            return True
        if url and ("lever.co" in url.lower() or "jobs.lever.co" in url.lower()):
            return True
        return False

    async def prepare(self, page: Any, context: PreparationContext) -> PreparationResult:
        start_time = time.time()

        logger.info(f"[LeverAdapter] Opening portal URL for app #{context.application_id}: {context.portal_url}")
        await page.goto(context.portal_url, wait_until="domcontentloaded", timeout=30000)

        # 1. Check for blocking full-page challenge / auth wall before form exists (Scenario B)
        blocking_challenge = await self.check_blocking_pre_challenges(page, context, start_time)
        if blocking_challenge:
            return blocking_challenge

        # 2. Lever Layout Integrity Verification
        has_lever_form = (
            await page.locator("#lever-form, form[action*='lever'], .application-page, .application-form, form").count() > 0
            or await page.locator("input[name='name'], input[name='email'], input[name='first_name']").count() > 0
        )
        if not has_lever_form:
            logger.warning(f"[LeverAdapter] Standard Lever form container not found on {context.portal_url}. Layout may have changed.")
            screenshot_path = await self.capture_screenshot(page, context, "layout_changed")
            return PreparationResult(
                application_id=context.application_id,
                approval_token=context.approval_token,
                portal_type=self.portal_name,
                status="paused_for_human_input",
                fields_filled=[],
                unresolved_fields=[{"field": "layout", "reason": "Standard Lever form layout not detected or dynamically altered"}],
                screenshot_path=screenshot_path,
                error_message="Lever portal layout differs from standard structure. Execution paused safely for human review.",
                duration_ms=(time.time() - start_time) * 1000,
            )

        # 3. Populate All Supported Master Profile & Screening Fields (Scenario A)
        fields_filled, unresolved_fields, resume_uploaded = await self.fill_common_form_fields(page, context)

        # 4. CAPTCHA / Bot Challenge Verification Check on Form
        if await PlaywrightSafetyGuard.detect_captcha(page):
            logger.info(f"[LeverAdapter] CAPTCHA detected on Lever form for App #{context.application_id}. Pausing after pre-populating fields.")
            screenshot_path = await self.capture_screenshot(page, context, "captcha_challenge_staged")
            return PreparationResult(
                application_id=context.application_id,
                approval_token=context.approval_token,
                portal_type=self.portal_name,
                status="blocked_by_captcha",
                fields_filled=fields_filled,
                unresolved_fields=unresolved_fields,
                resume_uploaded=resume_uploaded,
                resume_file_path=str(context.resume_file_path) if context.resume_file_path else None,
                screenshot_path=screenshot_path,
                final_submit_clicked=False,
                guard_triggered=await self.verify_submit_guard(page),
                captcha_detected=True,
                auth_required=False,
                error_message="CAPTCHA or bot protection challenge detected. Execution safely paused for human intervention.",
                duration_ms=(time.time() - start_time) * 1000,
            )

        # 5. Non-Negotiable Submit Guard Check
        guard_triggered = await self.verify_submit_guard(page)

        # 6. Capture Screenshot Artifact
        screenshot_path = await self.capture_screenshot(page, context, "staged")

        status = "paused_for_human_input" if len(unresolved_fields) > 0 else "staged"

        return PreparationResult(
            application_id=context.application_id,
            approval_token=context.approval_token,
            portal_type=self.portal_name,
            status=status,
            fields_filled=fields_filled,
            unresolved_fields=unresolved_fields,
            resume_uploaded=resume_uploaded,
            resume_file_path=str(context.resume_file_path) if context.resume_file_path else None,
            screenshot_path=screenshot_path,
            final_submit_clicked=False,  # ALWAYS FALSE
            guard_triggered=guard_triggered,
            captcha_detected=False,
            auth_required=False,
            duration_ms=(time.time() - start_time) * 1000,
        )
