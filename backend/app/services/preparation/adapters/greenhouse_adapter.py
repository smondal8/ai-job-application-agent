import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.preparation.adapter_base import (
    BasePortalPreparationAdapter,
    PreparationContext,
    PreparationResult,
)

logger = get_logger("app.services.preparation.adapters.greenhouse")


class GreenhousePreparationAdapter(BasePortalPreparationAdapter):
    """Specialized, high-reliability preparation adapter for Greenhouse (boards.greenhouse.io) job application forms."""

    @property
    def portal_name(self) -> str:
        return "greenhouse"

    def can_handle(self, portal_type: str, url: str) -> bool:
        if portal_type and portal_type.lower() == "greenhouse":
            return True
        if url and ("greenhouse.io" in url.lower() or "boards.greenhouse" in url.lower() or "grnh.se" in url.lower()):
            return True
        return False

    async def prepare(self, page: Any, context: PreparationContext) -> PreparationResult:
        start_time = time.time()
        fields_filled: List[Dict[str, Any]] = []
        unresolved_fields: List[Dict[str, Any]] = []
        resume_uploaded = False

        logger.info(f"[GreenhouseAdapter] Opening portal URL for app #{context.application_id}: {context.portal_url}")
        await page.goto(context.portal_url, wait_until="load", timeout=30000)

        # 1. Global Safety Checks (CAPTCHA / Bot detection / Auth wall)
        safety_blocked = await self.check_global_safety_guards(page, context, start_time)
        if safety_blocked:
            return safety_blocked

        # 2. Greenhouse Layout Integrity Verification
        has_app_container = (
            await page.locator("#application_form, #apply_form, form[action*='applications'], form#application").count() > 0
            or await page.locator("#first_name, input[name='first_name'], input[id*='first_name']").count() > 0
        )
        if not has_app_container:
            logger.warning(f"[GreenhouseAdapter] Standard Greenhouse form container not found on {context.portal_url}. Layout may have changed.")
            screenshot_path = await self.capture_screenshot(page, context, "layout_changed")
            return PreparationResult(
                application_id=context.application_id,
                approval_token=context.approval_token,
                portal_type=self.portal_name,
                status="paused_for_human_input",
                fields_filled=fields_filled,
                unresolved_fields=[{"field": "layout", "reason": "Standard Greenhouse form layout not detected or dynamically altered"}],
                screenshot_path=screenshot_path,
                error_message="Greenhouse portal layout differs from standard structure. Execution paused safely for human review.",
                duration_ms=(time.time() - start_time) * 1000,
            )

        candidate = context.candidate

        # 3. Populate Standard Personal Details
        # First Name
        fn_loc = page.locator("#first_name, input[name='first_name'], input[id*='first_name']")
        if await fn_loc.count() > 0:
            first_name = candidate.full_name.split()[0] if candidate.full_name else ""
            await fn_loc.first.fill(first_name)
            fields_filled.append({"field": "first_name", "value": first_name, "selector": "#first_name"})

        # Last Name
        ln_loc = page.locator("#last_name, input[name='last_name'], input[id*='last_name']")
        if await ln_loc.count() > 0:
            last_name = " ".join(candidate.full_name.split()[1:]) if candidate.full_name and len(candidate.full_name.split()) > 1 else ""
            await ln_loc.first.fill(last_name)
            fields_filled.append({"field": "last_name", "value": last_name, "selector": "#last_name"})

        # Email
        email_loc = page.locator("#email, input[name='email'], input[id*='email']")
        if await email_loc.count() > 0:
            await email_loc.first.fill(candidate.email)
            fields_filled.append({"field": "email", "value": candidate.email, "selector": "#email"})

        # Phone
        if candidate.phone:
            phone_loc = page.locator("#phone, input[name='phone'], input[id*='phone']")
            if await phone_loc.count() > 0:
                await phone_loc.first.fill(candidate.phone)
                fields_filled.append({"field": "phone", "value": candidate.phone, "selector": "#phone"})

        # Location
        if candidate.location:
            loc_input = page.locator("#job_application_location, #location, input[name='location'], input[id*='location']")
            if await loc_input.count() > 0:
                await loc_input.first.fill(candidate.location)
                fields_filled.append({"field": "location", "value": candidate.location, "selector": "#location"})

        # LinkedIn Profile
        if candidate.linkedin_url:
            li_loc = page.locator("#linkedin, input[id*='linkedin'], input[name*='linkedin'], input[autocomplete*='linkedin']")
            if await li_loc.count() > 0:
                await li_loc.first.fill(candidate.linkedin_url)
                fields_filled.append({"field": "linkedin_url", "value": candidate.linkedin_url, "selector": "#linkedin"})

        # Website / GitHub / Portfolio
        gh_or_portfolio = candidate.github_url or candidate.portfolio_url or candidate.website
        if gh_or_portfolio:
            gh_loc = page.locator("#github, #website, input[id*='github'], input[id*='website'], input[name*='website']")
            if await gh_loc.count() > 0:
                await gh_loc.first.fill(gh_or_portfolio)
                fields_filled.append({"field": "portfolio_url", "value": gh_or_portfolio, "selector": "#website"})

        # 4. Upload Approved Tailored Resume File
        if context.resume_file_path and Path(context.resume_file_path).exists():
            file_loc = page.locator("input[type='file']#resume, input[type='file'][name*='resume'], input[type='file']")
            if await file_loc.count() > 0:
                await file_loc.first.set_input_files(str(context.resume_file_path))
                resume_uploaded = True
                fields_filled.append({"field": "resume_file", "value": str(context.resume_file_path), "selector": "input[type=file]#resume"})

        # 5. Populate Cover Letter
        cover_text = context.tailored_resume.cover_letter if context.tailored_resume and context.tailored_resume.cover_letter else None
        if cover_text:
            cl_loc = page.locator("textarea#cover_letter_text, textarea[name='cover_letter_text'], textarea[id*='cover_letter']")
            if await cl_loc.count() > 0:
                await cl_loc.first.fill(cover_text)
                fields_filled.append({"field": "cover_letter", "value": f"Cover Letter ({len(cover_text)} characters)", "selector": "#cover_letter_text"})

        # 6. Map Custom Screening Questions
        answers = context.answers_payload or {}
        for key, val in answers.items():
            # Check for radio buttons (e.g. work_auth, sponsorship)
            if isinstance(val, bool):
                bool_str = "yes" if val else "no"
                radio_loc = page.locator(
                    f"input[type='radio'][id*='{key}_{bool_str}'], input[type='radio'][name*='{key}'][value*='{bool_str}']"
                )
                if await radio_loc.count() > 0:
                    await radio_loc.first.check()
                    fields_filled.append({"field": key, "value": val, "selector": f"radio[{key}={bool_str}]"})
                    continue

            # Check for text/select inputs
            custom_input = page.locator(f"input[name*='{key}'], input[id*='{key}'], textarea[name*='{key}']")
            if await custom_input.count() > 0:
                await custom_input.first.fill(str(val))
                fields_filled.append({"field": key, "value": str(val), "selector": f"input[{key}]"})

        # 7. Identify Unresolved Required Questions
        req_inputs = page.locator("form input[required], form select[required], form textarea[required]")
        req_count = await req_inputs.count()
        for i in range(req_count):
            inp = req_inputs.nth(i)
            inp_type = await inp.get_attribute("type") or ""
            if inp_type in ["file", "submit", "button", "hidden"]:
                continue
            inp_val = await inp.input_value() if await inp.evaluate("el => 'value' in el") else ""
            if not inp_val or inp_val.strip() == "":
                name = await inp.get_attribute("name") or await inp.get_attribute("id") or f"unresolved_question_{i}"
                unresolved_fields.append({
                    "field": name,
                    "type": inp_type,
                    "reason": "Required field not matched in profile or answers payload",
                })

        # 8. Non-Negotiable Submit Guard Check
        guard_triggered = await self.verify_submit_guard(page)

        # 9. Screenshot Audit Artifact
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
