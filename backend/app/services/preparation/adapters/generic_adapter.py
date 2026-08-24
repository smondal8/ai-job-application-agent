import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.services.preparation.adapter_base import (
    BasePortalPreparationAdapter,
    PreparationContext,
    PreparationResult,
)
from app.services.preparation.safety_guard import PlaywrightSafetyGuard

logger = get_logger("app.services.preparation.generic_adapter")


class GenericPortalPreparationAdapter(BasePortalPreparationAdapter):
    """Generic portal preparation adapter using standard HTML5 form inspection."""

    @property
    def portal_name(self) -> str:
        return "generic"

    def can_handle(self, portal_type: str, url: str) -> bool:
        return portal_type == "generic" or not portal_type

    async def prepare(self, page: Any, context: PreparationContext) -> PreparationResult:
        start_time = time.time()
        fields_filled: List[Dict[str, Any]] = []
        unresolved_fields: List[Dict[str, Any]] = []
        resume_uploaded = False
        guard_triggered = False
        screenshot_path: Optional[str] = None

        logger.info(f"Opening portal URL for application #{context.application_id}: {context.portal_url}")
        await page.goto(context.portal_url, wait_until="load", timeout=30000)

        # 1. Non-negotiable Check: CAPTCHA / Bot challenge detection
        if await PlaywrightSafetyGuard.detect_captcha(page):
            screenshot_path = await self._capture_screenshot(page, context, "captcha_blocked")
            return PreparationResult(
                application_id=context.application_id,
                approval_token=context.approval_token,
                portal_type=self.portal_name,
                status="blocked_by_captcha",
                fields_filled=fields_filled,
                unresolved_fields=unresolved_fields,
                captcha_detected=True,
                screenshot_path=screenshot_path,
                error_message="CAPTCHA or bot protection challenge detected. Execution safely paused for human intervention.",
                duration_ms=(time.time() - start_time) * 1000,
            )

        # 2. Non-negotiable Check: Authentication wall detection
        if await PlaywrightSafetyGuard.detect_auth_wall(page):
            screenshot_path = await self._capture_screenshot(page, context, "auth_blocked")
            return PreparationResult(
                application_id=context.application_id,
                approval_token=context.approval_token,
                portal_type=self.portal_name,
                status="blocked_by_auth",
                fields_filled=fields_filled,
                unresolved_fields=unresolved_fields,
                auth_required=True,
                screenshot_path=screenshot_path,
                error_message="Authentication wall or login required. Execution safely paused for human intervention.",
                duration_ms=(time.time() - start_time) * 1000,
            )

        # 3. Fill Standard Candidate Profile Fields
        candidate = context.candidate

        # Full Name or First/Last Name
        if await page.locator("input[id*='first_name'], input[name*='first_name'], input[id='first_name']").count() > 0:
            first_name = candidate.full_name.split()[0] if candidate.full_name else ""
            last_name = " ".join(candidate.full_name.split()[1:]) if candidate.full_name and len(candidate.full_name.split()) > 1 else ""
            await page.fill("input[id*='first_name'], input[name*='first_name'], input[id='first_name']", first_name)
            fields_filled.append({"field": "first_name", "value": first_name, "selector": "first_name"})
            if await page.locator("input[id*='last_name'], input[name*='last_name'], input[id='last_name']").count() > 0:
                await page.fill("input[id*='last_name'], input[name*='last_name'], input[id='last_name']", last_name)
                fields_filled.append({"field": "last_name", "value": last_name, "selector": "last_name"})
        elif await page.locator("input[name*='name'], input[id*='name'], input[placeholder*='Name']").count() > 0:
            await page.fill("input[name*='name'], input[id*='name'], input[placeholder*='Name']", candidate.full_name)
            fields_filled.append({"field": "name", "value": candidate.full_name, "selector": "name"})

        # Email
        if await page.locator("input[type='email'], input[name*='email'], input[id*='email']").count() > 0:
            await page.fill("input[type='email'], input[name*='email'], input[id*='email']", candidate.email)
            fields_filled.append({"field": "email", "value": candidate.email, "selector": "email"})

        # Phone
        if candidate.phone and await page.locator("input[type='tel'], input[name*='phone'], input[id*='phone']").count() > 0:
            await page.fill("input[type='tel'], input[name*='phone'], input[id*='phone']", candidate.phone)
            fields_filled.append({"field": "phone", "value": candidate.phone, "selector": "phone"})

        # Location
        if candidate.location and await page.locator("input[name*='location'], input[id*='location'], input[name*='city']").count() > 0:
            await page.fill("input[name*='location'], input[id*='location'], input[name*='city']", candidate.location)
            fields_filled.append({"field": "location", "value": candidate.location, "selector": "location"})

        # LinkedIn URL
        if candidate.linkedin_url and await page.locator("input[name*='linkedin'], input[id*='linkedin'], input[placeholder*='LinkedIn']").count() > 0:
            await page.fill("input[name*='linkedin'], input[id*='linkedin'], input[placeholder*='LinkedIn']", candidate.linkedin_url)
            fields_filled.append({"field": "linkedin_url", "value": candidate.linkedin_url, "selector": "linkedin"})

        # GitHub URL
        if candidate.github_url and await page.locator("input[name*='github'], input[id*='github'], input[placeholder*='GitHub']").count() > 0:
            await page.fill("input[name*='github'], input[id*='github'], input[placeholder*='GitHub']", candidate.github_url)
            fields_filled.append({"field": "github_url", "value": candidate.github_url, "selector": "github"})

        # Portfolio / Website URL
        site_url = candidate.portfolio_url or candidate.website
        if site_url and await page.locator("input[name*='website'], input[id*='website'], input[name*='portfolio'], input[id*='portfolio']").count() > 0:
            await page.fill("input[name*='website'], input[id*='website'], input[name*='portfolio'], input[id*='portfolio']", site_url)
            fields_filled.append({"field": "portfolio_url", "value": site_url, "selector": "portfolio/website"})

        # 4. Upload Approved Resume Document
        if context.resume_file_path and Path(context.resume_file_path).exists():
            file_inputs = page.locator("input[type='file']")
            if await file_inputs.count() > 0:
                await file_inputs.first.set_input_files(str(context.resume_file_path))
                resume_uploaded = True
                fields_filled.append({"field": "resume_file", "value": str(context.resume_file_path), "selector": "input[type=file]"})

        # 5. Fill Cover Letter
        cover_letter_text = context.tailored_resume.cover_letter if context.tailored_resume and context.tailored_resume.cover_letter else None
        if cover_letter_text and await page.locator("textarea[name*='cover'], textarea[id*='cover'], textarea[name*='letter'], textarea[id*='letter']").count() > 0:
            await page.fill("textarea[name*='cover'], textarea[id*='cover'], textarea[name*='letter'], textarea[id*='letter']", cover_letter_text)
            fields_filled.append({"field": "cover_letter", "value": f"Cover letter ({len(cover_letter_text)} chars)", "selector": "textarea[cover]"})

        # 6. Map Screening Answers from answers_payload
        answers = context.answers_payload or {}
        for key, val in answers.items():
            # Check for matching inputs or textareas or selects
            key_clean = key.replace("_", "").lower()
            matching_inputs = page.locator(f"input[name*='{key}'], input[id*='{key}'], textarea[name*='{key}'], textarea[id*='{key}']")
            if await matching_inputs.count() > 0:
                input_type = await matching_inputs.first.get_attribute("type") or "text"
                if input_type in ["text", "number", "tel"]:
                    await matching_inputs.first.fill(str(val))
                    fields_filled.append({"field": key, "value": str(val), "selector": f"input[{key}]"})
                elif input_type == "checkbox":
                    if bool(val):
                        await matching_inputs.first.check()
                    else:
                        await matching_inputs.first.uncheck()
                    fields_filled.append({"field": key, "value": bool(val), "selector": f"checkbox[{key}]"})
            else:
                # Try finding radio by value or label
                if isinstance(val, bool):
                    bool_val_str = "yes" if val else "no"
                    radio = page.locator(f"input[type='radio'][value*='{bool_val_str}'], input[type='radio'][id*='{key}_{bool_val_str}']")
                    if await radio.count() > 0:
                        await radio.first.check()
                        fields_filled.append({"field": key, "value": val, "selector": f"radio[{key}={bool_val_str}]"})

        # 7. Discover Ambiguous / Unfilled Required Questions
        required_inputs = page.locator("input[required], textarea[required], select[required]")
        req_count = await required_inputs.count()
        for i in range(req_count):
            inp = required_inputs.nth(i)
            inp_val = await inp.input_value() if await inp.evaluate("el => 'value' in el") else ""
            inp_type = await inp.get_attribute("type") or ""
            if inp_type == "file":
                continue
            if not inp_val or inp_val.strip() == "":
                name = await inp.get_attribute("name") or await inp.get_attribute("id") or f"unnamed_field_{i}"
                unresolved_fields.append({
                    "field": name,
                    "type": inp_type,
                    "reason": "Required field not matched in profile or answers payload",
                })

        # 8. NON-NEGOTIABLE FINAL SUBMISSION GUARD: Ensure submit button is NOT clicked
        for submit_sel in PlaywrightSafetyGuard.SUBMIT_SELECTORS:
            if await page.locator(submit_sel).count() > 0:
                guard_triggered = True
                logger.info(f"Safety guard active: Detected submit element '{submit_sel}'. Halting at staged checkpoint.")
                break

        # Capture final staging screenshot
        screenshot_path = await self._capture_screenshot(page, context, "staged_form")

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

    async def _capture_screenshot(self, page: Any, context: PreparationContext, label: str) -> str:
        """Helper to capture screenshot and return relative/absolute path."""
        try:
            context.screenshot_dir.mkdir(parents=True, exist_ok=True)
            filename = f"app_{context.application_id}_{label}_{int(time.time())}.png"
            full_path = context.screenshot_dir / filename
            await page.screenshot(path=str(full_path), full_page=True)
            return str(full_path)
        except Exception as e:
            logger.warning(f"Failed to capture screenshot: {e}")
            return ""
