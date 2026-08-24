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

logger = get_logger("app.services.preparation.adapters.workday")


class WorkdayPreparationAdapter(BasePortalPreparationAdapter):
    """Specialized preparation adapter for Workday (myworkdayjobs.com) application workflows."""

    WORKDAY_AUTH_SELECTORS = [
        "div[data-automation-id='signInPage']",
        "input[data-automation-id='password']",
        "button[data-automation-id='signInSubmitButton']",
        "button[data-automation-id='createAccountSubmitButton']",
        "div[data-automation-id='createAccountPage']",
    ]

    @property
    def portal_name(self) -> str:
        return "workday"

    def can_handle(self, portal_type: str, url: str) -> bool:
        if portal_type and portal_type.lower() == "workday":
            return True
        if url and ("myworkdayjobs.com" in url.lower() or "workday.com" in url.lower()):
            return True
        return False

    async def prepare(self, page: Any, context: PreparationContext) -> PreparationResult:
        start_time = time.time()
        fields_filled: List[Dict[str, Any]] = []
        unresolved_fields: List[Dict[str, Any]] = []
        resume_uploaded = False

        logger.info(f"[WorkdayAdapter] Opening portal URL for app #{context.application_id}: {context.portal_url}")
        await page.goto(context.portal_url, wait_until="load", timeout=30000)

        # 1. Global Safety Checks (CAPTCHA / Bot detection / Universal Auth wall)
        safety_blocked = await self.check_global_safety_guards(page, context, start_time)
        if safety_blocked:
            return safety_blocked

        # 2. Workday-Specific Candidate Login / Account Creation Detection
        for auth_sel in self.WORKDAY_AUTH_SELECTORS:
            if await page.locator(auth_sel).count() > 0:
                logger.warning(f"[WorkdayAdapter] Workday candidate login or account creation required ({auth_sel}). Pausing for user.")
                screenshot_path = await self.capture_screenshot(page, context, "auth_required")
                return PreparationResult(
                    application_id=context.application_id,
                    approval_token=context.approval_token,
                    portal_type=self.portal_name,
                    status="blocked_by_auth",
                    auth_required=True,
                    screenshot_path=screenshot_path,
                    error_message="Workday candidate account login or creation required. Execution safely paused for user sign-in.",
                    duration_ms=(time.time() - start_time) * 1000,
                )

        candidate = context.candidate

        # 3. Populate Workday Form Fields (via data-automation-id & semantic attributes)
        # First Name
        fn_loc = page.locator("input[data-automation-id='legalNameSection_firstName'], input[data-automation-id*='firstName'], input[name*='firstName']")
        if await fn_loc.count() > 0:
            first_name = candidate.full_name.split()[0] if candidate.full_name else ""
            await fn_loc.first.fill(first_name)
            fields_filled.append({"field": "first_name", "value": first_name, "selector": "data-automation-id=firstName"})

        # Last Name
        ln_loc = page.locator("input[data-automation-id='legalNameSection_lastName'], input[data-automation-id*='lastName'], input[name*='lastName']")
        if await ln_loc.count() > 0:
            last_name = " ".join(candidate.full_name.split()[1:]) if candidate.full_name and len(candidate.full_name.split()) > 1 else ""
            await ln_loc.first.fill(last_name)
            fields_filled.append({"field": "last_name", "value": last_name, "selector": "data-automation-id=lastName"})

        # Email
        email_loc = page.locator("input[data-automation-id='email'], input[data-automation-id*='email'], input[type='email']")
        if await email_loc.count() > 0:
            await email_loc.first.fill(candidate.email)
            fields_filled.append({"field": "email", "value": candidate.email, "selector": "data-automation-id=email"})

        # Phone
        if candidate.phone:
            phone_loc = page.locator("input[data-automation-id='phone-number'], input[data-automation-id*='phone'], input[type='tel']")
            if await phone_loc.count() > 0:
                await phone_loc.first.fill(candidate.phone)
                fields_filled.append({"field": "phone", "value": candidate.phone, "selector": "data-automation-id=phone"})

        # City / Location
        if candidate.location:
            loc_input = page.locator("input[data-automation-id='addressSection_city'], input[data-automation-id*='city'], input[data-automation-id*='location']")
            if await loc_input.count() > 0:
                await loc_input.first.fill(candidate.location)
                fields_filled.append({"field": "location", "value": candidate.location, "selector": "data-automation-id=city"})

        # 4. Upload Resume
        if context.resume_file_path and Path(context.resume_file_path).exists():
            file_loc = page.locator("input[type='file'][data-automation-id*='file'], input[type='file']")
            if await file_loc.count() > 0:
                await file_loc.first.set_input_files(str(context.resume_file_path))
                resume_uploaded = True
                fields_filled.append({"field": "resume_file", "value": str(context.resume_file_path), "selector": "input[type=file]"})

        # 5. Populate Screening Answers
        answers = context.answers_payload or {}
        for key, val in answers.items():
            if isinstance(val, bool):
                bool_str = "yes" if val else "no"
                radio_loc = page.locator(f"input[type='radio'][data-automation-id*='{key}'], input[type='radio'][id*='{key}_{bool_str}']")
                if await radio_loc.count() > 0:
                    await radio_loc.first.check()
                    fields_filled.append({"field": key, "value": val, "selector": f"radio[{key}]"})
                    continue

            custom_input = page.locator(f"input[data-automation-id*='{key}'], input[name*='{key}']")
            if await custom_input.count() > 0:
                await custom_input.first.fill(str(val))
                fields_filled.append({"field": key, "value": str(val), "selector": f"input[{key}]"})

        # 6. Discover Unresolved Required Fields
        req_inputs = page.locator("input[required], select[required], textarea[required]")
        req_count = await req_inputs.count()
        for i in range(req_count):
            inp = req_inputs.nth(i)
            inp_type = await inp.get_attribute("type") or ""
            if inp_type in ["file", "submit", "button", "hidden"]:
                continue
            inp_val = await inp.input_value() if await inp.evaluate("el => 'value' in el") else ""
            if not inp_val or inp_val.strip() == "":
                name = await inp.get_attribute("data-automation-id") or await inp.get_attribute("name") or f"unresolved_field_{i}"
                unresolved_fields.append({
                    "field": name,
                    "type": inp_type,
                    "reason": "Required Workday field not matched in profile or answers payload",
                })

        # 7. Non-Negotiable Submit Guard Check
        guard_triggered = await self.verify_submit_guard(page)

        # 8. Capture Screenshot Artifact
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
