import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.preparation.adapter_base import (
    BasePortalPreparationAdapter,
    PreparationContext,
    PreparationResult,
)

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
        fields_filled: List[Dict[str, Any]] = []
        unresolved_fields: List[Dict[str, Any]] = []
        resume_uploaded = False

        logger.info(f"[LeverAdapter] Opening portal URL for app #{context.application_id}: {context.portal_url}")
        await page.goto(context.portal_url, wait_until="load", timeout=30000)

        # 1. Global Safety Checks (CAPTCHA / Bot detection / Auth wall)
        safety_blocked = await self.check_global_safety_guards(page, context, start_time)
        if safety_blocked:
            return safety_blocked

        # 2. Lever Layout Integrity Verification
        has_lever_form = (
            await page.locator("#lever-form, form[action*='lever'], .application-page, .application-form").count() > 0
            or await page.locator("input[name='name'], input[name='email']").count() > 0
        )
        if not has_lever_form:
            logger.warning(f"[LeverAdapter] Standard Lever form container not found on {context.portal_url}. Layout may have changed.")
            screenshot_path = await self.capture_screenshot(page, context, "layout_changed")
            return PreparationResult(
                application_id=context.application_id,
                approval_token=context.approval_token,
                portal_type=self.portal_name,
                status="paused_for_human_input",
                fields_filled=fields_filled,
                unresolved_fields=[{"field": "layout", "reason": "Standard Lever form layout not detected or dynamically altered"}],
                screenshot_path=screenshot_path,
                error_message="Lever portal layout differs from standard structure. Execution paused safely for human review.",
                duration_ms=(time.time() - start_time) * 1000,
            )

        candidate = context.candidate

        # 3. Populate Standard Personal Details
        # Full Name
        name_loc = page.locator("input[name='name'], input[placeholder*='Full Name'], input[id*='name']")
        if await name_loc.count() > 0:
            await name_loc.first.fill(candidate.full_name)
            fields_filled.append({"field": "name", "value": candidate.full_name, "selector": "input[name='name']"})

        # Email
        email_loc = page.locator("input[name='email'], input[placeholder*='Email'], input[type='email']")
        if await email_loc.count() > 0:
            await email_loc.first.fill(candidate.email)
            fields_filled.append({"field": "email", "value": candidate.email, "selector": "input[name='email']"})

        # Phone
        if candidate.phone:
            phone_loc = page.locator("input[name='phone'], input[placeholder*='Phone'], input[type='tel']")
            if await phone_loc.count() > 0:
                await phone_loc.first.fill(candidate.phone)
                fields_filled.append({"field": "phone", "value": candidate.phone, "selector": "input[name='phone']"})

        # Current Company / Org
        org_loc = page.locator("input[name='org'], input[placeholder*='Current company'], input[id*='org']")
        if await org_loc.count() > 0:
            curr_org = ""
            if candidate.experiences and len(candidate.experiences) > 0:
                curr_org = candidate.experiences[0].company
            if curr_org:
                await org_loc.first.fill(curr_org)
                fields_filled.append({"field": "org", "value": curr_org, "selector": "input[name='org']"})

        # Social & Profile URLs
        if candidate.linkedin_url:
            li_loc = page.locator("input[name='urls[LinkedIn]'], input[placeholder*='LinkedIn'], input[name*='linkedin']")
            if await li_loc.count() > 0:
                await li_loc.first.fill(candidate.linkedin_url)
                fields_filled.append({"field": "linkedin_url", "value": candidate.linkedin_url, "selector": "input[name='urls[LinkedIn]']"})

        if candidate.github_url:
            gh_loc = page.locator("input[name='urls[GitHub]'], input[placeholder*='GitHub'], input[name*='github']")
            if await gh_loc.count() > 0:
                await gh_loc.first.fill(candidate.github_url)
                fields_filled.append({"field": "github_url", "value": candidate.github_url, "selector": "input[name='urls[GitHub]']"})

        site_url = candidate.portfolio_url or candidate.website
        if site_url:
            port_loc = page.locator("input[name='urls[Portfolio]'], input[name='urls[Other]'], input[placeholder*='Portfolio']")
            if await port_loc.count() > 0:
                await port_loc.first.fill(site_url)
                fields_filled.append({"field": "portfolio_url", "value": site_url, "selector": "input[name='urls[Portfolio]']"})

        # 4. Upload Approved Tailored Resume File
        if context.resume_file_path and Path(context.resume_file_path).exists():
            file_loc = page.locator("input[name='resume'][type='file'], input[type='file']")
            if await file_loc.count() > 0:
                await file_loc.first.set_input_files(str(context.resume_file_path))
                resume_uploaded = True
                fields_filled.append({"field": "resume_file", "value": str(context.resume_file_path), "selector": "input[name='resume']"})

        # 5. Populate Additional Comments / Cover Letter
        cover_text = context.tailored_resume.cover_letter if context.tailored_resume and context.tailored_resume.cover_letter else None
        if cover_text:
            comm_loc = page.locator("textarea[name='comments'], textarea[placeholder*='Additional information'], textarea[id*='comments']")
            if await comm_loc.count() > 0:
                await comm_loc.first.fill(cover_text)
                fields_filled.append({"field": "comments", "value": f"Additional notes ({len(cover_text)} chars)", "selector": "textarea[name='comments']"})

        # 6. Map Custom Screening Answers
        answers = context.answers_payload or {}
        for key, val in answers.items():
            if isinstance(val, bool):
                bool_str = "yes" if val else "no"
                radio_loc = page.locator(
                    f"input[type='radio'][id*='{key}_{bool_str}'], input[type='radio'][value*='{bool_str}']"
                )
                if await radio_loc.count() > 0:
                    await radio_loc.first.check()
                    fields_filled.append({"field": key, "value": val, "selector": f"radio[{key}={bool_str}]"})
                    continue

            custom_input = page.locator(f"input[name*='{key}'], input[id*='{key}'], textarea[name*='{key}']")
            if await custom_input.count() > 0:
                await custom_input.first.fill(str(val))
                fields_filled.append({"field": key, "value": str(val), "selector": f"input[{key}]"})

        # 7. Discover Unresolved Required Fields
        req_inputs = page.locator("input[required], select[required], textarea[required]")
        req_count = await req_inputs.count()
        for i in range(req_count):
            inp = req_inputs.nth(i)
            inp_type = await inp.get_attribute("type") or ""
            if inp_type in ["file", "submit", "button", "hidden"]:
                continue
            inp_val = await inp.input_value() if await inp.evaluate("el => 'value' in el") else ""
            if not inp_val or inp_val.strip() == "":
                name = await inp.get_attribute("name") or await inp.get_attribute("id") or f"unresolved_field_{i}"
                unresolved_fields.append({
                    "field": name,
                    "type": inp_type,
                    "reason": "Required field not matched in candidate profile or screening answers",
                })

        # 8. Non-Negotiable Submit Guard Check
        guard_triggered = await self.verify_submit_guard(page)

        # 9. Capture Screenshot Artifact
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
