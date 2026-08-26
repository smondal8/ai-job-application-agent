import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFoundError, BadRequestError, ForbiddenError, AppException
from app.core.logging import get_logger
from app.models.application import Application
from app.models.approval import ApplicationApproval
from app.models.preparation import BrowserPreparationRun
from app.models.audit import AuditLog
from app.services.approval import approval_service
from app.services.approval.state_machine import ApplicationStatus, transition_application
from app.services.preparation.adapter_base import PreparationContext, PreparationResult
from app.services.preparation.adapter_registry import preparation_adapter_registry
from app.services.preparation.safety_guard import PlaywrightSafetyGuard
from app.services.preparation.browser_session_manager import browser_session_manager

logger = get_logger("app.services.preparation.engine")


class BrowserPreparationEngine:
    """Core Playwright browser application preparation engine (Phase 9)."""

    def __init__(self):
        self.settings = get_settings()

    async def prepare_application_async(
        self,
        db: Session,
        application_id: int,
        headless: bool = True,
        custom_portal_url: Optional[str] = None,
    ) -> BrowserPreparationRun:
        """Asynchronously executes Playwright browser application staging."""
        # 1. NON-NEGOTIABLE SERVER-SIDE AUTHORIZATION GATE CHECK
        logger.info(f"Checking server-side approval authorization for application #{application_id}...")
        auth_res = approval_service.authorize_for_preparation(db=db, application_id=application_id)
        approval_token = auth_res["approval_token"]

        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise NotFoundError(f"Application #{application_id} not found.")

        job = application.job
        if not job:
            raise NotFoundError(f"Job not found for application #{application_id}.")

        candidate = application.candidate_profile
        if not candidate:
            raise BadRequestError("Candidate profile not linked to application.")

        tailored_resume = application.tailored_resume
        approval = (
            db.query(ApplicationApproval)
            .filter(ApplicationApproval.application_id == application_id, ApplicationApproval.is_valid == True)
            .order_by(ApplicationApproval.created_at.desc())
            .first()
        )

        # 2. Resolve target URL
        portal_url = custom_portal_url or application.portal_url or job.url
        if not portal_url:
            raise BadRequestError("No target portal URL configured for this job application.")

        # 3. Create approved resume upload file if available
        temp_resume_file: Optional[Path] = None
        if tailored_resume:
            if tailored_resume.file_path and Path(tailored_resume.file_path).exists():
                temp_resume_file = Path(tailored_resume.file_path)
            else:
                resume_content = (
                    tailored_resume.compiled_markdown
                    or tailored_resume.compiled_text
                    or tailored_resume.cover_letter
                    or f"# {candidate.full_name}\n\nCandidate Resume"
                )
                resumes_dir = Path(self.settings.STORAGE_DIR) / "staged_resumes"
                resumes_dir.mkdir(parents=True, exist_ok=True)
                temp_resume_file = resumes_dir / f"approved_resume_app_{application_id}.txt"
                temp_resume_file.write_text(resume_content, encoding="utf-8")

        screenshot_dir = Path(self.settings.STORAGE_DIR) / "screenshots" / f"app_{application_id}"
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        context = PreparationContext(
            application_id=application.id,
            job=job,
            candidate=candidate,
            tailored_resume=tailored_resume,
            answers_payload=application.answers_payload or {},
            approval_token=approval_token,
            portal_url=portal_url,
            screenshot_dir=screenshot_dir,
            resume_file_path=temp_resume_file,
        )

        adapter = preparation_adapter_registry.get_adapter(application.portal_type, portal_url)
        logger.info(f"Using preparation adapter '{adapter.portal_name}' for portal URL: {portal_url}")

        # 4. Launch Playwright session
        from playwright.async_api import async_playwright

        logger.info(
            f"[PID {os.getpid()}] Starting browser preparation for App #{application.id} (Job #{job.id}). "
            f"Manager ID: {id(browser_session_manager)}, Headless: {headless}, Portal: {portal_url}"
        )

        p = await async_playwright().start()
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        browser_context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        )
        page = await browser_context.new_page()

        logger.info(
            f"[PID {os.getpid()}] Playwright initialized: Browser ID {id(browser)}, Context ID {id(browser_context)}, Page ID {id(page)}"
        )

        prep_result: Optional[PreparationResult] = None
        try:
            prep_result = await adapter.prepare(page, context)
        except Exception as e:
            logger.error(f"[PID {os.getpid()}] Unexpected error during browser staging: {e}")
            try:
                await browser_context.close()
                await browser.close()
                await p.stop()
            except Exception:
                pass
            raise e

        # 5. Non-Negotiable Safety Verification
        if prep_result.final_submit_clicked:
            try:
                await browser_context.close()
                await browser.close()
                await p.stop()
            except Exception:
                pass
            raise AppException("CRITICAL SAFETY VIOLATION: Submit button was clicked during preparation!")

        # 6. Check Challenge / Human Handoff vs Normal Completion Lifecycle
        is_challenge = prep_result.captcha_detected or prep_result.status in ("blocked_by_captcha", "blocked_by_auth")

        if is_challenge:
            # KEEP BROWSER SESSION ALIVE FOR HUMAN HANDOFF
            logger.info(
                f"[PID {os.getpid()}] Challenge detected for App #{application.id} (Status: {prep_result.status}). "
                f"Registering ActiveBrowserSession (Manager ID: {id(browser_session_manager)}) and keeping Playwright alive."
            )
            await browser_session_manager.register_session(
                application_id=application.id,
                job_id=job.id,
                portal_url=portal_url,
                playwright_obj=p,
                browser=browser,
                browser_context=browser_context,
                page=page,
                is_headless=headless,
            )
        else:
            # Normal completion -> Clean up session
            logger.info(
                f"[PID {os.getpid()}] Staging completed successfully for App #{application.id}. Closing Playwright session."
            )
            try:
                await browser_context.close()
                await browser.close()
                await p.stop()
            except Exception as e:
                logger.warning(f"Error during normal browser cleanup: {e}")
            await browser_session_manager.close_session(application.id)

        # 6. Persist Preparation Run Audit Record
        run_record = BrowserPreparationRun(
            application_id=application.id,
            job_id=job.id,
            approval_id=approval.id if approval else None,
            approval_token=approval_token,
            portal_type=adapter.portal_name,
            portal_url=portal_url,
            status=prep_result.status,
            fields_filled=prep_result.fields_filled,
            unresolved_fields=prep_result.unresolved_fields,
            resume_uploaded=prep_result.resume_uploaded,
            resume_file_path=prep_result.resume_file_path,
            screenshot_path=prep_result.screenshot_path,
            final_submit_clicked=False,
            guard_triggered=prep_result.guard_triggered,
            captcha_detected=prep_result.captcha_detected,
            auth_required=prep_result.auth_required,
            error_message=prep_result.error_message,
            duration_ms=prep_result.duration_ms,
        )
        db.add(run_record)

        # Handle CAPTCHA / Browser Challenge Safe State Transition
        is_challenge = prep_result.captcha_detected or prep_result.status in ("blocked_by_captcha", "blocked_by_auth")
        if is_challenge:
            challenge_reason = "CAPTCHA / Browser Challenge" if (prep_result.captcha_detected or prep_result.status == "blocked_by_captcha") else "Authentication Required"
            transition_application(application, ApplicationStatus.ACTION_REQUIRED, reason=challenge_reason)
            application.error_message = prep_result.error_message or "Browser verification required: Portal challenge detected."
            action_name = "APPLICATION_CAPTCHA_DETECTED" if (prep_result.captcha_detected or prep_result.status == "blocked_by_captcha") else "APPLICATION_CHALLENGE_DETECTED"
            msg = f"Browser verification required: CAPTCHA / bot challenge detected for application #{application.id}. Automation paused safely for human intervention."
            challenge_type = "CAPTCHA_REQUIRED" if (prep_result.captcha_detected or prep_result.status == "blocked_by_captcha") else "AUTH_REQUIRED"
        else:
            if application.status != ApplicationStatus.STAGED_FOR_PREPARATION.value:
                transition_application(application, ApplicationStatus.STAGED_FOR_PREPARATION)
            action_name = "APPLICATION_BROWSER_STAGED"
            msg = f"Browser application staged for App #{application.id} via adapter '{adapter.portal_name}'. Status: {prep_result.status}. Fields filled: {len(prep_result.fields_filled)}. Submit guard active."
            challenge_type = None

        db.commit()
        db.refresh(run_record)

        # 7. Audit Log
        audit = AuditLog(
            application_id=application.id,
            stage="browser_automation_staging",
            action=action_name,
            message=msg,
            payload={
                "run_id": run_record.id,
                "portal_type": adapter.portal_name,
                "status": prep_result.status,
                "challenge_type": challenge_type,
                "detected_at": datetime.now(timezone.utc).isoformat() if is_challenge else None,
                "fields_filled_count": len(prep_result.fields_filled),
                "unresolved_count": len(prep_result.unresolved_fields),
                "guard_triggered": prep_result.guard_triggered,
                "captcha_detected": prep_result.captcha_detected,
                "screenshot_path": prep_result.screenshot_path,
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(run_record)

        return run_record

    def prepare_application(
        self,
        db: Session,
        application_id: int,
        headless: bool = True,
        custom_portal_url: Optional[str] = None,
    ) -> BrowserPreparationRun:
        """Synchronous wrapper for browser application preparation."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In async contexts, run in a separate thread/loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(
                        asyncio.run,
                        self.prepare_application_async(
                            db=db,
                            application_id=application_id,
                            headless=headless,
                            custom_portal_url=custom_portal_url,
                        ),
                    ).result()
            else:
                return loop.run_until_complete(
                    self.prepare_application_async(
                        db=db,
                        application_id=application_id,
                        headless=headless,
                        custom_portal_url=custom_portal_url,
                    )
                )
        except RuntimeError:
            return asyncio.run(
                self.prepare_application_async(
                    db=db,
                    application_id=application_id,
                    headless=headless,
                    custom_portal_url=custom_portal_url,
                )
            )


browser_preparation_engine = BrowserPreparationEngine()
