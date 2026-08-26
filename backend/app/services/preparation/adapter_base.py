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

    async def has_accessible_form_fields(self, page: Any) -> bool:
        """Checks if interactive application form inputs are present in the DOM."""
        try:
            count = await page.locator(
                "input[name*='name'], input[id*='name'], input[placeholder*='Name'], "
                "input[type='file'], #first_name, #last_name, form[action*='apply'], "
                "#application_form, #lever-form, .ashby-application-form, textarea"
            ).count()
            return count > 0
        except Exception:
            return False

    async def check_blocking_pre_challenges(
        self,
        page: Any,
        context: PreparationContext,
        start_time: float,
    ) -> Optional[PreparationResult]:
        """Checks if a full-page blocking authentication wall or blocking interstitial exists before any form is accessible."""
        # 1. Non-negotiable Check: Authentication wall / login required
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

        # 2. Non-negotiable Check: Full-page CAPTCHA / bot challenge when NO application form inputs exist
        has_form = await self.has_accessible_form_fields(page)
        if await PlaywrightSafetyGuard.detect_captcha(page) and not has_form:
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

        return None

    async def safe_fill_locator(self, loc: Any, value: str, timeout_ms: int = 2500) -> bool:
        """Attempts to fill an input locator safely without hanging or throwing if hidden/disabled."""
        try:
            count = await loc.count()
            for i in range(count):
                el = loc.nth(i)
                try:
                    if await el.is_visible():
                        await el.fill(value, timeout=timeout_ms)
                        return True
                except Exception:
                    continue
            # If not interactable via standard fill, attempt evaluate value set
            if count > 0:
                try:
                    await loc.first.evaluate(
                        "(el, val) => { if ('value' in el) { el.value = val; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); } }",
                        value,
                    )
                    return True
                except Exception:
                    pass
        except Exception:
            pass
        return False

    async def safe_check_locator(self, loc: Any, timeout_ms: int = 2500) -> bool:
        """Attempts to check a radio/checkbox locator safely without hanging."""
        try:
            count = await loc.count()
            for i in range(count):
                el = loc.nth(i)
                try:
                    if await el.is_visible():
                        await el.check(timeout=timeout_ms)
                        return True
                except Exception:
                    continue
            if count > 0:
                try:
                    await loc.first.evaluate("(el) => { el.checked = true; el.dispatchEvent(new Event('change', { bubbles: true })); }")
                    return True
                except Exception:
                    pass
        except Exception:
            pass
        return False

    async def safe_upload_locator(self, loc: Any, file_path: str, timeout_ms: int = 3000) -> bool:
        """Attempts to upload file to file input locator safely."""
        try:
            count = await loc.count()
            for i in range(count):
                el = loc.nth(i)
                try:
                    await el.set_input_files(file_path, timeout=timeout_ms)
                    return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    async def fill_common_form_fields(
        self,
        page: Any,
        context: PreparationContext,
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], bool]:
        """
        Populates all available reliable fields from Master Profile and answers payload.
        Uses privacy-preserving logging (field categories only, never logging sensitive values).
        Returns: (fields_filled, unresolved_fields, resume_uploaded)
        """
        fields_filled: List[Dict[str, Any]] = []
        unresolved_fields: List[Dict[str, Any]] = []
        resume_uploaded = False

        candidate = context.candidate
        if not candidate:
            return fields_filled, unresolved_fields, resume_uploaded

        # 1. First & Last Name or Full Name
        fn_loc = page.locator(
            "#first_name, input[name='first_name'], input[name='firstName'], input[id*='first_name'], "
            "input[id*='firstName'], input[placeholder*='First Name'], input[aria-label*='First Name'], "
            "input[data-automation-id='legalNameSection_firstName'], input[data-automation-id*='firstName']"
        )
        first_name = candidate.full_name.split()[0] if candidate.full_name else ""
        if first_name and await self.safe_fill_locator(fn_loc, first_name):
            fields_filled.append({"field": "first_name", "value": first_name, "selector": "first_name"})
            logger.info(f"application_id={context.application_id} field=first_name source=master_profile action=filled")

        ln_loc = page.locator(
            "#last_name, input[name='last_name'], input[name='lastName'], input[id*='last_name'], "
            "input[id*='lastName'], input[placeholder*='Last Name'], input[aria-label*='Last Name'], "
            "input[data-automation-id='legalNameSection_lastName'], input[data-automation-id*='lastName']"
        )
        last_name = " ".join(candidate.full_name.split()[1:]) if candidate.full_name and len(candidate.full_name.split()) > 1 else ""
        if last_name and await self.safe_fill_locator(ln_loc, last_name):
            fields_filled.append({"field": "last_name", "value": last_name, "selector": "last_name"})
            logger.info(f"application_id={context.application_id} field=last_name source=master_profile action=filled")

        # If neither first/last name field was filled, look for Full Name input
        if not any(f["field"] in ["first_name", "last_name"] for f in fields_filled) and candidate.full_name:
            name_loc = page.locator(
                "input[name='name'], input[id='name'], input[name='_system_field_name'], "
                "input[name*='full_name'], input[name*='fullName'], input[placeholder*='Full Name'], "
                "input[placeholder*='Your Name'], input[aria-label*='Full Name'], input[placeholder='Name']"
            )
            if await self.safe_fill_locator(name_loc, candidate.full_name):
                fields_filled.append({"field": "name", "value": candidate.full_name, "selector": "full_name"})
                logger.info(f"application_id={context.application_id} field=name source=master_profile action=filled")

        # 2. Email Address
        if candidate.email:
            email_loc = page.locator(
                "input[type='email'], #email, input[name='email'], input[name='_system_field_email'], "
                "input[id*='email'], input[data-automation-id='email'], input[placeholder*='Email'], input[aria-label*='Email']"
            )
            if await self.safe_fill_locator(email_loc, candidate.email):
                fields_filled.append({"field": "email", "value": candidate.email, "selector": "email"})
                logger.info(f"application_id={context.application_id} field=email source=master_profile action=filled")

        # 3. Phone Number
        if candidate.phone:
            phone_loc = page.locator(
                "input[type='tel'], #phone, input[name='phone'], input[name='phoneNumber'], "
                "input[name='_system_field_phoneNumber'], input[id*='phone'], input[data-automation-id='phone-number'], "
                "input[placeholder*='Phone'], input[aria-label*='Phone']"
            )
            if await self.safe_fill_locator(phone_loc, candidate.phone):
                fields_filled.append({"field": "phone", "value": candidate.phone, "selector": "phone"})
                logger.info(f"application_id={context.application_id} field=phone source=master_profile action=filled")

        # 4. Location / City
        if candidate.location:
            loc_input = page.locator(
                "#job_application_location, #location, input[name='location'], input[id*='location'], "
                "input[name='city'], input[id*='city'], input[data-automation-id='addressSection_city'], "
                "input[data-automation-id*='city'], input[placeholder*='Location'], input[placeholder*='City']"
            )
            if await self.safe_fill_locator(loc_input, candidate.location):
                fields_filled.append({"field": "location", "value": candidate.location, "selector": "location"})
                logger.info(f"application_id={context.application_id} field=location source=master_profile action=filled")

        # 5. Current / Most Recent Company
        curr_company = ""
        if candidate.experiences and len(candidate.experiences) > 0:
            curr_company = candidate.experiences[0].company or ""
        if curr_company:
            org_loc = page.locator(
                "input[name='org'], input[placeholder*='Current company'], input[id*='org'], "
                "input[name*='company'], input[id*='company'], input[data-automation-id*='company'], "
                "input[placeholder*='Company']"
            )
            if await self.safe_fill_locator(org_loc, curr_company):
                fields_filled.append({"field": "org", "value": curr_company, "selector": "company"})
                logger.info(f"application_id={context.application_id} field=company source=master_profile action=filled")

        # 6. Current Title / Headline
        curr_title = candidate.headline or (candidate.experiences[0].position if candidate.experiences and len(candidate.experiences) > 0 else "")
        if curr_title:
            title_loc = page.locator(
                "input[name*='title'], input[id*='title'], input[name*='headline'], "
                "input[id*='headline'], input[placeholder*='Title'], input[placeholder*='Headline']"
            )
            if await self.safe_fill_locator(title_loc, curr_title):
                fields_filled.append({"field": "title", "value": curr_title, "selector": "title"})
                logger.info(f"application_id={context.application_id} field=title source=master_profile action=filled")

        # 7. LinkedIn Profile URL
        if candidate.linkedin_url:
            li_loc = page.locator(
                "#linkedin, input[name='urls[LinkedIn]'], input[name*='linkedin'], input[id*='linkedin'], "
                "input[placeholder*='LinkedIn'], input[autocomplete*='linkedin']"
            )
            if await self.safe_fill_locator(li_loc, candidate.linkedin_url):
                fields_filled.append({"field": "linkedin_url", "value": candidate.linkedin_url, "selector": "linkedin"})
                logger.info(f"application_id={context.application_id} field=linkedin_url source=master_profile action=filled")

        # 8. GitHub Profile URL
        if candidate.github_url:
            gh_loc = page.locator(
                "#github, input[name='urls[GitHub]'], input[name*='github'], input[id*='github'], "
                "input[placeholder*='GitHub']"
            )
            if await self.safe_fill_locator(gh_loc, candidate.github_url):
                fields_filled.append({"field": "github_url", "value": candidate.github_url, "selector": "github"})
                logger.info(f"application_id={context.application_id} field=github_url source=master_profile action=filled")

        # 9. Portfolio / Website URL
        port_url = candidate.portfolio_url or candidate.website
        if port_url:
            port_loc = page.locator(
                "#website, input[name='urls[Portfolio]'], input[name='urls[Other]'], input[name*='portfolio'], "
                "input[id*='portfolio'], input[name*='website'], input[id*='website'], "
                "input[placeholder*='Portfolio'], input[placeholder*='Website']"
            )
            if await self.safe_fill_locator(port_loc, port_url):
                fields_filled.append({"field": "portfolio_url", "value": port_url, "selector": "portfolio_url"})
                logger.info(f"application_id={context.application_id} field=portfolio_url source=master_profile action=filled")

        # 10. Approved Tailored Resume Upload
        if context.resume_file_path and Path(context.resume_file_path).exists():
            file_loc = page.locator("input[type='file']")
            if await self.safe_upload_locator(file_loc, str(context.resume_file_path)):
                resume_uploaded = True
                fields_filled.append({"field": "resume_file", "value": str(context.resume_file_path), "selector": "input[type=file]"})
                logger.info(f"application_id={context.application_id} field=resume_file source=approved_tailored_resume action=uploaded")

        # 11. Cover Letter / Additional Comments
        cover_text = context.tailored_resume.cover_letter if context.tailored_resume and context.tailored_resume.cover_letter else None
        if cover_text:
            cl_loc = page.locator(
                "textarea#cover_letter_text, textarea[name='cover_letter_text'], textarea[id*='cover_letter'], "
                "textarea[name*='cover'], textarea[name='comments'], textarea[id*='comments'], "
                "textarea[placeholder*='Cover Letter'], textarea[placeholder*='Additional information']"
            )
            if await self.safe_fill_locator(cl_loc, cover_text):
                fields_filled.append({"field": "cover_letter", "value": f"Cover letter ({len(cover_text)} chars)", "selector": "cover_letter"})
                logger.info(f"application_id={context.application_id} field=cover_letter source=tailored_materials action=filled")

        # 12. Screening Answers Mapping from answers_payload
        answers = context.answers_payload or {}
        for key, val in answers.items():
            if isinstance(val, bool):
                bool_str = "yes" if val else "no"
                radio_loc = page.locator(
                    f"input[type='radio'][id*='{key}_{bool_str}'], input[type='radio'][value*='{bool_str}'], "
                    f"input[type='radio'][name*='{key}'][value*='{bool_str}']"
                )
                if await self.safe_check_locator(radio_loc):
                    fields_filled.append({"field": key, "value": val, "selector": f"radio[{key}={bool_str}]"})
                    logger.info(f"application_id={context.application_id} field={key} source=answers_payload action=checked")
                    continue

            custom_input = page.locator(f"input[name*='{key}'], input[id*='{key}'], textarea[name*='{key}'], textarea[id*='{key}']")
            if await custom_input.count() > 0:
                input_type = await custom_input.first.get_attribute("type") or "text"
                if input_type in ["text", "number", "tel"]:
                    if await self.safe_fill_locator(custom_input, str(val)):
                        fields_filled.append({"field": key, "value": str(val), "selector": f"input[{key}]"})
                        logger.info(f"application_id={context.application_id} field={key} source=answers_payload action=filled")
                elif input_type == "checkbox":
                    if bool(val):
                        if await self.safe_check_locator(custom_input):
                            fields_filled.append({"field": key, "value": True, "selector": f"checkbox[{key}]"})
                            logger.info(f"application_id={context.application_id} field={key} source=answers_payload action=checked")

        # 13. Identify Unresolved Required Fields
        req_inputs = page.locator("form input[required], form select[required], form textarea[required], input[required], select[required], textarea[required]")
        req_count = await req_inputs.count()
        for i in range(req_count):
            try:
                inp = req_inputs.nth(i)
                if not await inp.is_visible():
                    continue
                inp_type = await inp.get_attribute("type") or ""
                if inp_type in ["file", "submit", "button", "hidden"]:
                    continue
                inp_val = await inp.input_value(timeout=1000) if await inp.evaluate("el => 'value' in el") else ""
                if not inp_val or inp_val.strip() == "":
                    name = await inp.get_attribute("name") or await inp.get_attribute("id") or f"unresolved_field_{i}"
                    unresolved_fields.append({
                        "field": name,
                        "type": inp_type,
                        "reason": "Required field not matched in profile or answers payload",
                    })
            except Exception:
                continue

        return fields_filled, unresolved_fields, resume_uploaded

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
