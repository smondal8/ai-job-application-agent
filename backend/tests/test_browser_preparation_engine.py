import pytest
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.errors import ForbiddenError, BadRequestError
from app.models.job import Job
from app.models.candidate import CandidateProfile, CandidateSkill, WorkExperience
from app.models.analysis import JobAnalysis
from app.models.resume import TailoredResume
from app.models.application import Application
from app.models.preparation import BrowserPreparationRun
from app.services.approval import approval_service
from app.services.preparation import browser_preparation_engine, browser_session_manager

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "portals"


@pytest.fixture(autouse=True)
async def cleanup_browser_sessions():
    yield
    await browser_session_manager.close_all()


@pytest.fixture
def setup_phase9_approved_app(db_session: Session):
    profile = CandidateProfile(
        full_name="Katherine Johnson",
        email="katherine@nasa.gov",
        phone="+1 757-864-1000",
        location="Hampton, VA",
        headline="NASA Orbital Trajectory Mathematician",
        linkedin_url="https://linkedin.com/in/katherine-johnson",
        github_url="https://github.com/katherine-johnson",
        is_verified=True,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    skill = CandidateSkill(profile_id=profile.id, name="Orbital Mechanics", category="Engineering", proficiency="expert", is_verified=True)
    db_session.add(skill)
    db_session.commit()

    job = Job(
        title="Senior Flight Dynamics Engineer",
        company="NASA Jet Propulsion Laboratory",
        location="Pasadena, CA",
        remote_type="hybrid",
        description_raw="Calculating celestial trajectories and entry descent landing trajectories.",
        description_clean="Calculating celestial trajectories and entry descent landing trajectories.",
        source="phase9_test",
        url="https://jpl.nasa.gov/careers/orbital-1",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    analysis = JobAnalysis(
        job_id=job.id,
        candidate_profile_id=profile.id,
        fit_score=95.0,
        status="completed",
    )
    db_session.add(analysis)
    db_session.commit()

    resume = TailoredResume(
        job_id=job.id,
        candidate_profile_id=profile.id,
        job_analysis_id=analysis.id,
        prompt_version="v1.0.0",
        tailored_summary="Calculated orbital trajectories for Mercury, Apollo, and Space Shuttle missions.",
        compiled_markdown="# Katherine Johnson\n\nMathematician specializing in orbital mechanics.",
        validation_status="valid",
        status="ready_for_review",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    app_entity = Application(
        job_id=job.id,
        candidate_profile_id=profile.id,
        tailored_resume_id=resume.id,
        status="ready_for_review",
        portal_type="greenhouse",
        answers_payload={"work_auth": True, "sponsorship": False},
    )
    db_session.add(app_entity)
    db_session.commit()
    db_session.refresh(app_entity)

    return {
        "profile": profile,
        "job": job,
        "resume": resume,
        "app": app_entity,
    }


@pytest.mark.asyncio
async def test_preparation_engine_security_gate_blocks_unapproved_application(db_session: Session, setup_phase9_approved_app: dict):
    app_entity = setup_phase9_approved_app["app"]

    fixture_url = f"file://{FIXTURES_DIR / 'greenhouse_job_app.html'}"
    with pytest.raises(ForbiddenError):
        await browser_preparation_engine.prepare_application_async(
            db=db_session,
            application_id=app_entity.id,
            headless=True,
            custom_portal_url=fixture_url,
        )


@pytest.mark.asyncio
async def test_preparation_engine_security_gate_blocks_tampered_application(db_session: Session, setup_phase9_approved_app: dict):
    app_entity = setup_phase9_approved_app["app"]
    profile = setup_phase9_approved_app["profile"]

    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    profile.full_name = "Katherine Johnson (Tampered)"
    db_session.commit()

    fixture_url = f"file://{FIXTURES_DIR / 'greenhouse_job_app.html'}"
    with pytest.raises(ForbiddenError):
        await browser_preparation_engine.prepare_application_async(
            db=db_session,
            application_id=app_entity.id,
            headless=True,
            custom_portal_url=fixture_url,
        )


@pytest.mark.asyncio
async def test_preparation_engine_greenhouse_staging(db_session: Session, setup_phase9_approved_app: dict):
    app_entity = setup_phase9_approved_app["app"]

    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    fixture_url = f"file://{FIXTURES_DIR / 'greenhouse_job_app.html'}"
    run = await browser_preparation_engine.prepare_application_async(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.id is not None
    assert run.status == "staged"
    assert run.portal_type == "greenhouse"
    assert len(run.fields_filled) >= 4
    assert any(f["field"] == "first_name" for f in run.fields_filled)
    assert any(f["field"] == "email" for f in run.fields_filled)
    assert run.resume_uploaded is True
    assert run.screenshot_path is not None
    assert Path(run.screenshot_path).exists()

    assert run.final_submit_clicked is False
    assert run.guard_triggered is True


@pytest.mark.asyncio
async def test_preparation_engine_lever_staging(db_session: Session, setup_phase9_approved_app: dict):
    app_entity = setup_phase9_approved_app["app"]
    app_entity.portal_type = "lever"
    db_session.commit()

    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    fixture_url = f"file://{FIXTURES_DIR / 'lever_job_app.html'}"
    run = await browser_preparation_engine.prepare_application_async(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "staged"
    assert run.portal_type == "lever"
    assert any(f["field"] == "name" and "Katherine" in f["value"] for f in run.fields_filled)
    assert run.final_submit_clicked is False
    assert run.guard_triggered is True


@pytest.mark.asyncio
async def test_non_negotiable_final_submit_guard_on_obvious_submit_button(db_session: Session, setup_phase9_approved_app: dict):
    """Proves that even when a prominent submit button is rendered, the browser engine NEVER clicks submit."""
    app_entity = setup_phase9_approved_app["app"]
    app_entity.portal_type = "generic"
    db_session.commit()
    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    fixture_url = f"file://{FIXTURES_DIR / 'obvious_submit_app.html'}"
    run = await browser_preparation_engine.prepare_application_async(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "staged"
    assert run.final_submit_clicked is False
    assert run.guard_triggered is True


@pytest.mark.asyncio
async def test_preparation_engine_detects_captcha_and_stops_safely(db_session: Session, setup_phase9_approved_app: dict):
    """Proves that when CAPTCHA / bot challenge is present, engine safely pauses without bypassing and puts application into ACTION_REQUIRED."""
    app_entity = setup_phase9_approved_app["app"]
    approval = approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    fixture_url = f"file://{FIXTURES_DIR / 'captcha_challenge_app.html'}"
    run = await browser_preparation_engine.prepare_application_async(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    # 1. Run record checks
    assert run.status == "blocked_by_captcha"
    assert run.captcha_detected is True
    assert run.final_submit_clicked is False
    assert run.screenshot_path is not None

    # 2. Application state checks
    db_session.refresh(app_entity)
    assert app_entity.status == "action_required"
    assert app_entity.error_message is not None
    assert "CAPTCHA" in app_entity.error_message

    # 3. Preserved application state & approval integrity
    assert app_entity.tailored_resume_id == setup_phase9_approved_app["resume"].id
    assert app_entity.candidate_profile_id == setup_phase9_approved_app["profile"].id
    assert app_entity.job_id == setup_phase9_approved_app["job"].id
    assert app_entity.approval_token == approval.approval_token

    # 4. Live browser session registered and active
    assert await browser_session_manager.is_session_active(app_entity.id) is True

    # 5. Hashes remain identical (no resume regeneration or tampering)
    verify_res = approval_service.verify_approval(db=db_session, application_id=app_entity.id)
    assert verify_res["is_valid"] is True

    # 6. User explicitly resumes after manual verification
    from app.services.approval.state_machine import transition_application, ApplicationStatus
    transition_application(app_entity, ApplicationStatus.STAGED_FOR_PREPARATION.value, reason="User completed verification")
    app_entity.error_message = None
    db_session.commit()
    db_session.refresh(app_entity)

    assert app_entity.status == "staged_for_preparation"
    assert app_entity.error_message is None
    assert approval_service.verify_approval(db=db_session, application_id=app_entity.id)["is_valid"] is True


@pytest.mark.asyncio
async def test_preparation_engine_detects_auth_wall_and_stops_safely(db_session: Session, setup_phase9_approved_app: dict):
    """Proves that when login authentication wall is present, engine pauses for human input and sets ACTION_REQUIRED."""
    app_entity = setup_phase9_approved_app["app"]
    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    fixture_url = f"file://{FIXTURES_DIR / 'auth_login_app.html'}"
    run = await browser_preparation_engine.prepare_application_async(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "blocked_by_auth"
    assert run.auth_required is True
    assert run.final_submit_clicked is False

    db_session.refresh(app_entity)
    assert app_entity.status == "action_required"
    assert app_entity.error_message is not None


@pytest.mark.asyncio
async def test_preparation_engine_pauses_on_ambiguous_fields(db_session: Session, setup_phase9_approved_app: dict):
    """Proves that when required unsupported/ambiguous fields exist, engine pauses for human input."""
    app_entity = setup_phase9_approved_app["app"]
    app_entity.portal_type = "generic"
    db_session.commit()
    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    fixture_url = f"file://{FIXTURES_DIR / 'ambiguous_fields_app.html'}"
    run = await browser_preparation_engine.prepare_application_async(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "paused_for_human_input"
    assert len(run.unresolved_fields) >= 1
    assert run.final_submit_clicked is False


@pytest.mark.asyncio
async def test_preparation_engine_resists_adversarial_prompt_injection(db_session: Session, setup_phase9_approved_app: dict):
    """Proves that page content / prompt injections cannot alter system policy or force auto-submit."""
    app_entity = setup_phase9_approved_app["app"]
    app_entity.portal_type = "generic"
    db_session.commit()
    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    fixture_url = f"file://{FIXTURES_DIR / 'prompt_injection_app.html'}"
    run = await browser_preparation_engine.prepare_application_async(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "staged"
    assert run.final_submit_clicked is False
    assert run.guard_triggered is True


@pytest.mark.asyncio
async def test_preparation_populates_all_fields_before_captcha_pause(db_session: Session, setup_phase9_approved_app: dict):
    """Proves that when a form has fields + CAPTCHA widget, engine fills all supported fields AND uploads resume BEFORE pausing."""
    app_entity = setup_phase9_approved_app["app"]
    resume = setup_phase9_approved_app["resume"]
    resume.cover_letter = "Dear NASA JPL Team,\n\nI am thrilled to apply for the Senior Flight Dynamics Engineer position."
    db_session.commit()

    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    fixture_url = f"file://{FIXTURES_DIR / 'greenhouse_with_captcha_app.html'}"
    run = await browser_preparation_engine.prepare_application_async(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    # 1. Run paused for CAPTCHA
    assert run.status == "blocked_by_captcha"
    assert run.captcha_detected is True
    assert run.final_submit_clicked is False

    # 2. BUT fields WERE filled before pausing!
    assert len(run.fields_filled) >= 6
    field_names = [f["field"] for f in run.fields_filled]
    assert "first_name" in field_names
    assert "last_name" in field_names
    assert "email" in field_names
    assert "phone" in field_names
    assert "location" in field_names
    assert "linkedin_url" in field_names
    assert "resume_file" in field_names
    assert run.resume_uploaded is True

    # 3. Session remains alive and application is ACTION_REQUIRED
    db_session.refresh(app_entity)
    assert app_entity.status == "action_required"
    assert await browser_session_manager.is_session_active(app_entity.id) is True

