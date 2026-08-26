import asyncio
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFoundError, BadRequestError
from app.core.logging import get_logger
from app.models.application import Application
from app.services.preparation.safety_guard import PlaywrightSafetyGuard

logger = get_logger("app.services.preparation.browser_session_manager")


class ActiveBrowserSession:
    """Represents a live Playwright browser session attached to a specific Application ID."""

    def __init__(
        self,
        application_id: int,
        job_id: int,
        portal_url: str,
        playwright_obj: Any,
        browser: Any,
        browser_context: Any,
        page: Any,
        is_headless: bool = False,
    ):
        self.application_id = application_id
        self.job_id = job_id
        self.portal_url = portal_url
        self.playwright_obj = playwright_obj
        self.browser = browser
        self.browser_context = browser_context
        self.page = page
        self.is_headless = is_headless
        self.created_at = datetime.now(timezone.utc)

    async def is_alive(self) -> bool:
        """Returns True if the browser context and page remain open and responsive."""
        try:
            if not self.browser or not self.browser.is_connected():
                return False
            if not self.page or self.page.is_closed():
                return False
            return True
        except Exception:
            return False

    async def bring_to_front(self) -> bool:
        """Brings the application browser tab to the foreground on the user's desktop."""
        try:
            if await self.is_alive():
                if self.is_headless:
                    return False
                await self.page.bring_to_front()
                return True
        except Exception as e:
            logger.warning(f"[PID {os.getpid()}] Failed to bring page to front for App #{self.application_id}: {e}")
        return False

    async def close(self):
        """Safely closes the page, browser context, and Playwright driver."""
        logger.info(f"[PID {os.getpid()}] Closing session for App #{self.application_id} (Page: {id(self.page)}, Browser: {id(self.browser)})")
        try:
            if self.page and not self.page.is_closed():
                await self.page.close()
        except Exception:
            pass

        try:
            if self.browser_context:
                await self.browser_context.close()
        except Exception:
            pass

        try:
            if self.browser and self.browser.is_connected():
                await self.browser.close()
        except Exception:
            pass

        try:
            if self.playwright_obj:
                await self.playwright_obj.stop()
        except Exception:
            pass


class BrowserSessionManager:
    """Manages live interactive browser sessions for Application staging and human handoffs."""

    def __init__(self):
        self._sessions: Dict[int, ActiveBrowserSession] = {}
        self._lock = threading.Lock()
        logger.info(f"[PID {os.getpid()}] BrowserSessionManager initialized (Instance ID: {id(self)})")

    def get_session(self, application_id: int) -> Optional[ActiveBrowserSession]:
        """Retrieves active browser session for an Application ID."""
        with self._lock:
            session = self._sessions.get(application_id)
        logger.info(
            f"[PID {os.getpid()}] Manager (ID {id(self)}) get_session({application_id}) -> "
            f"{'Found (Page ID ' + str(id(session.page)) + ')' if session else 'None'}. "
            f"Active Sessions: {list(self._sessions.keys())}"
        )
        return session

    async def is_session_active(self, application_id: int) -> bool:
        """Checks if a valid, active browser session exists for the given application."""
        session = self.get_session(application_id)
        if not session:
            return False
        alive = await session.is_alive()
        logger.info(f"[PID {os.getpid()}] App #{application_id} session is_alive: {alive}")
        if not alive:
            # Clean up stale session
            await self.close_session(application_id)
            return False
        return True

    async def register_session(
        self,
        application_id: int,
        job_id: int,
        portal_url: str,
        playwright_obj: Any,
        browser: Any,
        browser_context: Any,
        page: Any,
        is_headless: bool = False,
    ) -> ActiveBrowserSession:
        """Registers a live Playwright session, closing any existing session for the same application."""
        old_session = None
        with self._lock:
            if application_id in self._sessions:
                old_session = self._sessions.pop(application_id)
                logger.info(f"[PID {os.getpid()}] Replacing existing session for App #{application_id}")

            session = ActiveBrowserSession(
                application_id=application_id,
                job_id=job_id,
                portal_url=portal_url,
                playwright_obj=playwright_obj,
                browser=browser,
                browser_context=browser_context,
                page=page,
                is_headless=is_headless,
            )
            self._sessions[application_id] = session

        if old_session:
            await old_session.close()

        logger.info(
            f"[PID {os.getpid()}] Registered active browser session for Application #{application_id} (Job #{job_id}). "
            f"Page ID: {id(page)}, Browser ID: {id(browser)}, Headless: {is_headless}. "
            f"Total Active Sessions: {len(self._sessions)}"
        )
        return session

    async def focus_session(self, application_id: int) -> Optional[Dict[str, Any]]:
        """Focuses the existing live browser session for the given application."""
        session = self.get_session(application_id)
        if not session or not await session.is_alive():
            logger.warning(f"[PID {os.getpid()}] focus_session({application_id}) failed: session not found or not alive.")
            await self.close_session(application_id)
            return None

        if not session.is_headless:
            brought = await session.bring_to_front()
            logger.info(f"[PID {os.getpid()}] Existing headed session brought to front for App #{application_id} (Success: {brought})")
            return {
                "session_active": True,
                "application_id": session.application_id,
                "job_id": session.job_id,
                "portal_url": session.portal_url,
                "is_headless": False,
                "page_alive": True,
                "browser_connected": True,
                "page_url": session.page.url if (session.page and not session.page.is_closed()) else session.portal_url,
                "focused": brought,
                "message": "Existing browser session focused.",
            }
        else:
            # Session is alive but was headless; report active so open_or_focus can upgrade it
            logger.info(f"[PID {os.getpid()}] App #{application_id} session is alive but headless.")
            return {
                "session_active": True,
                "application_id": session.application_id,
                "job_id": session.job_id,
                "portal_url": session.portal_url,
                "is_headless": True,
                "page_alive": True,
                "browser_connected": True,
                "page_url": session.page.url if (session.page and not session.page.is_closed()) else session.portal_url,
                "focused": False,
                "message": "Paused browser session is currently headless.",
            }

    async def open_or_focus_session(
        self,
        db: Session,
        application_id: int,
    ) -> Dict[str, Any]:
        """Reuses existing active browser session if alive and headed, or opens an interactive headed browser window."""
        session = self.get_session(application_id)
        if session and await session.is_alive():
            if not session.is_headless:
                brought = await session.bring_to_front()
                logger.info(f"[PID {os.getpid()}] Existing headed session focused for App #{application_id} (focused={brought}).")
                return {
                    "session_active": True,
                    "application_id": session.application_id,
                    "job_id": session.job_id,
                    "portal_url": session.portal_url,
                    "is_headless": False,
                    "page_alive": True,
                    "browser_connected": True,
                    "page_url": session.page.url if (session.page and not session.page.is_closed()) else session.portal_url,
                    "focused": brought,
                    "message": "Existing browser session focused.",
                }
            else:
                logger.info(f"[PID {os.getpid()}] Upgrading paused headless session for App #{application_id} to interactive headed window.")
                target_url = session.page.url if (session.page and not session.page.is_closed()) else session.portal_url
                await self.close_session(application_id)
        else:
            target_url = None

        # Look up application & job
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise NotFoundError(f"Application #{application_id} not found.")

        job = application.job
        if not job:
            raise NotFoundError(f"Job not found for application #{application_id}.")

        portal_url = target_url or application.portal_url or job.url
        if not portal_url:
            raise BadRequestError(f"No target portal URL configured for application #{application_id}.")

        from playwright.async_api import async_playwright
        from pathlib import Path
        from app.services.preparation.adapter_registry import preparation_adapter_registry
        from app.services.preparation.adapter_base import PreparationContext

        logger.info(f"[PID {os.getpid()}] Launching interactive headed browser for App #{application_id} at {portal_url}")
        p = None
        browser = None
        browser_context = None
        page = None

        try:
            p = await async_playwright().start()
            browser = await p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
            browser_context = await browser.new_context(
                viewport={"width": 1280, "height": 850},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            )
            page = await browser_context.new_page()

            # Register session early so it is tracked
            await self.register_session(
                application_id=application.id,
                job_id=job.id,
                portal_url=portal_url,
                playwright_obj=p,
                browser=browser,
                browser_context=browser_context,
                page=page,
                is_headless=False,
            )

            # Build PreparationContext and stage/fill form on the headed page
            settings = get_settings()
            temp_resume_file: Optional[Path] = None
            if application.tailored_resume:
                if application.tailored_resume.file_path and Path(application.tailored_resume.file_path).exists():
                    temp_resume_file = Path(application.tailored_resume.file_path)
                else:
                    resume_content = (
                        application.tailored_resume.compiled_markdown
                        or application.tailored_resume.compiled_text
                        or application.tailored_resume.cover_letter
                        or (f"# {application.candidate_profile.full_name}\n\nCandidate Resume" if application.candidate_profile else "Candidate Resume")
                    )
                    resumes_dir = Path(settings.STORAGE_DIR) / "staged_resumes"
                    resumes_dir.mkdir(parents=True, exist_ok=True)
                    temp_resume_file = resumes_dir / f"approved_resume_app_{application_id}.txt"
                    temp_resume_file.write_text(resume_content, encoding="utf-8")

            screenshot_dir = Path(settings.STORAGE_DIR) / "screenshots" / f"app_{application_id}"
            context = PreparationContext(
                application_id=application.id,
                job=job,
                candidate=application.candidate_profile,
                tailored_resume=application.tailored_resume,
                answers_payload=application.answers_payload or {},
                approval_token=application.approval_token or "",
                portal_url=portal_url,
                screenshot_dir=screenshot_dir,
                resume_file_path=temp_resume_file,
            )

            adapter = preparation_adapter_registry.get_adapter(application.portal_type, portal_url)
            try:
                await adapter.prepare(page, context)
            except Exception as e:
                logger.warning(f"Adapter preparation had note for headed session App #{application_id}: {e}")

            # Safely verify page state before bringing to front
            focused = False
            page_alive = False
            page_url = portal_url

            active_sess = self.get_session(application_id)
            if active_sess and await active_sess.is_alive():
                focused = await active_sess.bring_to_front()
                page_alive = True
                try:
                    if active_sess.page and not active_sess.page.is_closed():
                        page_url = active_sess.page.url
                except Exception:
                    pass

            logger.info(f"[PID {os.getpid()}] Headed browser session ready for App #{application.id} (page_alive={page_alive}, focused={focused}).")
            return {
                "session_active": page_alive,
                "application_id": application.id,
                "job_id": job.id,
                "portal_url": portal_url,
                "is_headless": False,
                "page_alive": page_alive,
                "browser_connected": browser.is_connected() if browser else False,
                "page_url": page_url,
                "focused": focused,
                "message": "Interactive browser session opened and pre-populated on your desktop." if page_alive else "Browser window was closed.",
            }

        except Exception as e:
            logger.error(f"[PID {os.getpid()}] Error opening interactive browser session for App #{application_id}: {e}")
            await self.close_session(application_id)
            return {
                "session_active": False,
                "application_id": application.id,
                "job_id": job.id,
                "portal_url": portal_url,
                "is_headless": False,
                "page_alive": False,
                "browser_connected": False,
                "page_url": portal_url,
                "focused": False,
                "message": f"Could not launch browser session: {str(e)}",
            }

    async def close_session(self, application_id: int):
        """Closes and removes an active browser session."""
        session = None
        with self._lock:
            session = self._sessions.pop(application_id, None)
        if session:
            await session.close()
            logger.info(f"[PID {os.getpid()}] Closed browser session for Application #{application_id}.")

    async def close_all(self):
        """Closes all active browser sessions."""
        sessions_to_close = []
        with self._lock:
            sessions_to_close = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions_to_close:
            await session.close()
        logger.info(f"[PID {os.getpid()}] Closed all active browser sessions.")


browser_session_manager = BrowserSessionManager()
