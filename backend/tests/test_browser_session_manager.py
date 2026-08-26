import pytest
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.candidate import CandidateProfile, CandidateSkill
from app.models.analysis import JobAnalysis
from app.models.resume import TailoredResume
from app.models.application import Application
from app.models.audit import AuditLog
from app.services.approval import approval_service
from app.services.preparation import browser_session_manager, browser_preparation_engine
from app.services.preparation.browser_session_manager import ActiveBrowserSession

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "portals"


@pytest.fixture
def setup_multi_app_fixtures(db_session: Session):
    profile = CandidateProfile(
        full_name="Grace Hopper",
        email="grace@navy.mil",
        phone="+1 202-555-0199",
        location="Arlington, VA",
        headline="Rear Admiral & Pioneer Computer Scientist",
        is_verified=True,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    job1 = Job(
        title="Lead Compiler Architect",
        company="COBOL Systems Inc",
        location="Washington, DC",
        remote_type="hybrid",
        description_raw="Developing machine-independent programming languages.",
        source="test_feed",
        url="https://cobol.example.com/jobs/1",
    )
    job2 = Job(
        title="Senior Systems Engineer",
        company="UNIVAC Corp",
        location="Philadelphia, PA",
        remote_type="onsite",
        description_raw="Mainframe architecture and tape storage diagnostics.",
        source="test_feed",
        url="https://univac.example.com/jobs/2",
    )
    db_session.add_all([job1, job2])
    db_session.commit()
    db_session.refresh(job1)
    db_session.refresh(job2)

    resume1 = TailoredResume(
        job_id=job1.id,
        candidate_profile_id=profile.id,
        prompt_version="v1.0.0",
        compiled_markdown="# Grace Hopper\nCompiler Pioneer",
        validation_status="valid",
        status="ready_for_review",
    )
    resume2 = TailoredResume(
        job_id=job2.id,
        candidate_profile_id=profile.id,
        prompt_version="v1.0.0",
        compiled_markdown="# Grace Hopper\nUNIVAC Specialist",
        validation_status="valid",
        status="ready_for_review",
    )
    db_session.add_all([resume1, resume2])
    db_session.commit()
    db_session.refresh(resume1)
    db_session.refresh(resume2)

    app1 = Application(
        job_id=job1.id,
        tailored_resume_id=resume1.id,
        candidate_profile_id=profile.id,
        status="action_required",
        error_message="CAPTCHA detected",
        portal_type="greenhouse",
    )
    app2 = Application(
        job_id=job2.id,
        tailored_resume_id=resume2.id,
        candidate_profile_id=profile.id,
        status="action_required",
        error_message="Auth wall detected",
        portal_type="lever",
    )
    db_session.add_all([app1, app2])
    db_session.commit()
    db_session.refresh(app1)
    db_session.refresh(app2)

    approval_service.grant_approval(db=db_session, application_id=app1.id)
    approval_service.grant_approval(db=db_session, application_id=app2.id)

    from app.services.approval.state_machine import transition_application, ApplicationStatus
    transition_application(app1, ApplicationStatus.ACTION_REQUIRED.value, reason="CAPTCHA detected")
    transition_application(app2, ApplicationStatus.ACTION_REQUIRED.value, reason="Auth challenge detected")
    db_session.commit()
    db_session.refresh(app1)
    db_session.refresh(app2)

    return {
        "profile": profile,
        "job1": job1,
        "job2": job2,
        "resume1": resume1,
        "resume2": resume2,
        "app1": app1,
        "app2": app2,
    }


@pytest.mark.asyncio
async def test_browser_session_manager_registration_and_focus():
    """Proves that active browser sessions can be registered, focused, and isolated by Application ID."""
    app_id = 101
    job_id = 202
    portal_url = "https://example.com/portal/101"

    # Mock page and browser
    class MockPage:
        def __init__(self, url="https://example.com"):
            self.brought_to_front = False
            self.closed = False
            self.url = url

        def is_closed(self):
            return self.closed

        async def bring_to_front(self):
            self.brought_to_front = True

        async def close(self):
            self.closed = True

    class MockBrowser:
        def __init__(self):
            self.connected = True

        def is_connected(self):
            return self.connected

        async def close(self):
            self.connected = False

    class MockContext:
        async def close(self):
            pass

    mock_page = MockPage()
    mock_browser = MockBrowser()
    mock_ctx = MockContext()

    session = await browser_session_manager.register_session(
        application_id=app_id,
        job_id=job_id,
        portal_url=portal_url,
        playwright_obj=None,
        browser=mock_browser,
        browser_context=mock_ctx,
        page=mock_page,
        is_headless=False,
    )

    assert session.application_id == app_id
    assert session.job_id == job_id
    assert await browser_session_manager.is_session_active(app_id) is True

    # Focus session
    focus_res = await browser_session_manager.focus_session(app_id)
    assert focus_res is not None
    assert focus_res["session_active"] is True
    assert focus_res["application_id"] == app_id
    assert focus_res["focused"] is True
    assert mock_page.brought_to_front is True

    # Clean up
    await browser_session_manager.close_session(app_id)
    assert await browser_session_manager.is_session_active(app_id) is False


@pytest.mark.asyncio
async def test_browser_session_isolation_across_multiple_applications(setup_multi_app_fixtures: dict):
    """Proves that multiple applications have isolated browser sessions mapped strictly by Application ID."""
    app1 = setup_multi_app_fixtures["app1"]
    app2 = setup_multi_app_fixtures["app2"]

    class MockPage:
        def __init__(self, name, url="https://example.com"):
            self.name = name
            self.url = url
            self.focused = False

        def is_closed(self):
            return False

        async def bring_to_front(self):
            self.focused = True

        async def close(self):
            pass

    class MockBrowser:
        def is_connected(self):
            return True

        async def close(self):
            pass

    page1 = MockPage("app1_page")
    page2 = MockPage("app2_page")

    await browser_session_manager.register_session(
        application_id=app1.id,
        job_id=app1.job_id,
        portal_url="https://cobol.example.com/app1",
        playwright_obj=None,
        browser=MockBrowser(),
        browser_context=None,
        page=page1,
        is_headless=False,
    )

    await browser_session_manager.register_session(
        application_id=app2.id,
        job_id=app2.job_id,
        portal_url="https://univac.example.com/app2",
        playwright_obj=None,
        browser=MockBrowser(),
        browser_context=None,
        page=page2,
        is_headless=False,
    )

    # Focusing app1 only brings page1 to front
    await browser_session_manager.focus_session(app1.id)
    assert page1.focused is True
    assert page2.focused is False

    # Focusing app2 only brings page2 to front
    await browser_session_manager.focus_session(app2.id)
    assert page2.focused is True

    # Clean up
    await browser_session_manager.close_all()


def test_browser_session_api_endpoints(client, db_session: Session, setup_multi_app_fixtures: dict):
    """Tests GET status, POST focus, and POST continue-after-verification API endpoints."""
    app1 = setup_multi_app_fixtures["app1"]
    resume1 = setup_multi_app_fixtures["resume1"]

    # 1. GET status when no live browser is open
    status_resp = client.get(f"/api/v1/applications/{app1.id}/browser-session/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["session_active"] is False
    assert status_data["application_id"] == app1.id
    assert "unavailable" in status_data["message"].lower()

    # 2. POST focus when session is not open
    focus_resp = client.post(f"/api/v1/applications/{app1.id}/browser-session/focus")
    assert focus_resp.status_code == 200
    focus_data = focus_resp.json()
    assert focus_data["session_active"] is False
    assert "unavailable" in focus_data["message"].lower()

    # 3. Verify application integrity
    assert app1.status == "action_required"
    assert app1.tailored_resume_id == resume1.id
    verify = approval_service.verify_approval(db_session, app1.id)
    assert verify["is_valid"] is True

    # 4. POST continue-after-verification
    cont_resp = client.post(f"/api/v1/applications/{app1.id}/continue-after-verification")
    assert cont_resp.status_code == 200
    assert cont_resp.json()["status"] == "staged_for_preparation"
    assert cont_resp.json()["error_message"] is None

    # Audit log was created
    audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.application_id == app1.id, AuditLog.action == "APPLICATION_CHALLENGE_RESUMED")
        .first()
    )
    assert audit is not None


@pytest.mark.asyncio
async def test_captcha_preserves_live_browser_session_e2e(client, db_session: Session, setup_multi_app_fixtures: dict):
    """Proves that when CAPTCHA is detected during preparation, the Playwright session remains alive, registered, and focusable."""
    app1 = setup_multi_app_fixtures["app1"]
    fixture_url = f"file://{FIXTURES_DIR / 'captcha_challenge_app.html'}"

    # 1. Execute preparation engine (which detects CAPTCHA)
    run_record = await browser_preparation_engine.prepare_application_async(
        db=db_session,
        application_id=app1.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run_record.status == "blocked_by_captcha"
    assert run_record.captcha_detected is True

    # 2. Verify application state
    db_session.refresh(app1)
    assert app1.status == "action_required"

    # 3. Verify that BrowserSessionManager has the active session immediately!
    assert await browser_session_manager.is_session_active(app1.id) is True
    session = browser_session_manager.get_session(app1.id)
    assert session is not None
    assert session.application_id == app1.id
    assert session.job_id == app1.job_id
    assert session.page is not None
    assert not session.page.is_closed()
    assert session.browser is not None
    assert session.browser.is_connected()

    # 4. Verify GET /browser-session/status API returns active session diagnostics
    status_resp = client.get(f"/api/v1/applications/{app1.id}/browser-session/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["session_active"] is True
    assert status_data["application_id"] == app1.id
    assert status_data["job_id"] == app1.job_id
    assert status_data["page_alive"] is True
    assert status_data["browser_connected"] is True

    # 5. Verify POST /browser-session/focus API returns active session
    focus_resp = client.post(f"/api/v1/applications/{app1.id}/browser-session/focus")
    assert focus_resp.status_code == 200
    focus_data = focus_resp.json()
    assert focus_data["session_active"] is True

    # 6. Verify POST continue-after-verification
    cont_resp = client.post(f"/api/v1/applications/{app1.id}/continue-after-verification")
    assert cont_resp.status_code == 200
    assert cont_resp.json()["status"] == "staged_for_preparation"

    # 7. Clean up
    await browser_session_manager.close_session(app1.id)
    assert await browser_session_manager.is_session_active(app1.id) is False

