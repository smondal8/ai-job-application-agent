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
from app.services.preparation import browser_preparation_engine

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "portals"


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
        fit_score=99.0,
        status="completed",
    )
    db_session.add(analysis)

    resume = TailoredResume(
        job_id=job.id,
        candidate_profile_id=profile.id,
        job_analysis_id=analysis.id,
        prompt_version="v1.0.0",
        tailored_summary="Mathematician whose calculations of orbital mechanics were critical to the success of crewed spaceflights.",
        cover_letter="Dear JPL Team,\n\nI am eager to contribute trajectory mathematics to your upcoming Mars landing missions.",
        compiled_markdown="# Katherine Johnson\n\nTrajectory Mathematician",
        validation_status="valid",
        status="ready_for_review",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    app_entity = Application(
        job_id=job.id,
        tailored_resume_id=resume.id,
        candidate_profile_id=profile.id,
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


def test_preparation_engine_security_gate_blocks_unapproved_application(db_session: Session, setup_phase9_approved_app: dict):
    app_entity = setup_phase9_approved_app["app"]

    # Application is in ready_for_review (NOT APPROVED)
    # Calling preparation engine MUST raise ForbiddenError without opening browser
    fixture_url = f"file://{FIXTURES_DIR / 'greenhouse_job_app.html'}"
    with pytest.raises(ForbiddenError):
        browser_preparation_engine.prepare_application(
            db=db_session,
            application_id=app_entity.id,
            headless=True,
            custom_portal_url=fixture_url,
        )


def test_preparation_engine_security_gate_blocks_tampered_application(db_session: Session, setup_phase9_approved_app: dict):
    app_entity = setup_phase9_approved_app["app"]
    profile = setup_phase9_approved_app["profile"]

    # 1. Grant human approval
    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    # 2. Tamper with candidate profile
    profile.full_name = "Katherine Johnson (Tampered)"
    db_session.commit()

    # 3. Preparation engine MUST detect material change and raise ForbiddenError
    fixture_url = f"file://{FIXTURES_DIR / 'greenhouse_job_app.html'}"
    with pytest.raises(ForbiddenError):
        browser_preparation_engine.prepare_application(
            db=db_session,
            application_id=app_entity.id,
            headless=True,
            custom_portal_url=fixture_url,
        )


def test_preparation_engine_greenhouse_staging(db_session: Session, setup_phase9_approved_app: dict):
    app_entity = setup_phase9_approved_app["app"]

    # 1. Grant approval
    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    fixture_url = f"file://{FIXTURES_DIR / 'greenhouse_job_app.html'}"
    run = browser_preparation_engine.prepare_application(
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

    # NON-NEGOTIABLE CHECK: Submit button was NOT clicked
    assert run.final_submit_clicked is False
    assert run.guard_triggered is True


def test_preparation_engine_lever_staging(db_session: Session, setup_phase9_approved_app: dict):
    app_entity = setup_phase9_approved_app["app"]
    app_entity.portal_type = "lever"
    db_session.commit()

    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    fixture_url = f"file://{FIXTURES_DIR / 'lever_job_app.html'}"
    run = browser_preparation_engine.prepare_application(
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


def test_non_negotiable_final_submit_guard_on_obvious_submit_button(db_session: Session, setup_phase9_approved_app: dict):
    """Proves that even when a prominent submit button is rendered, the browser engine NEVER clicks submit."""
    app_entity = setup_phase9_approved_app["app"]
    app_entity.portal_type = "generic"
    db_session.commit()
    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    fixture_url = f"file://{FIXTURES_DIR / 'obvious_submit_app.html'}"
    run = browser_preparation_engine.prepare_application(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "staged"
    assert run.final_submit_clicked is False
    assert run.guard_triggered is True


def test_preparation_engine_detects_captcha_and_stops_safely(db_session: Session, setup_phase9_approved_app: dict):
    """Proves that when CAPTCHA / bot challenge is present, engine safely pauses without bypassing."""
    app_entity = setup_phase9_approved_app["app"]
    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    fixture_url = f"file://{FIXTURES_DIR / 'captcha_challenge_app.html'}"
    run = browser_preparation_engine.prepare_application(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "blocked_by_captcha"
    assert run.captcha_detected is True
    assert run.final_submit_clicked is False
    assert run.screenshot_path is not None


def test_preparation_engine_detects_auth_wall_and_stops_safely(db_session: Session, setup_phase9_approved_app: dict):
    """Proves that when login authentication wall is present, engine pauses for human input."""
    app_entity = setup_phase9_approved_app["app"]
    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    fixture_url = f"file://{FIXTURES_DIR / 'auth_login_app.html'}"
    run = browser_preparation_engine.prepare_application(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "blocked_by_auth"
    assert run.auth_required is True
    assert run.final_submit_clicked is False


def test_preparation_engine_pauses_on_ambiguous_fields(db_session: Session, setup_phase9_approved_app: dict):
    """Proves that when required unsupported/ambiguous fields exist, engine pauses for human input."""
    app_entity = setup_phase9_approved_app["app"]
    app_entity.portal_type = "generic"
    db_session.commit()
    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    fixture_url = f"file://{FIXTURES_DIR / 'ambiguous_fields_app.html'}"
    run = browser_preparation_engine.prepare_application(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "paused_for_human_input"
    assert len(run.unresolved_fields) >= 1
    assert run.final_submit_clicked is False


def test_preparation_engine_resists_adversarial_prompt_injection(db_session: Session, setup_phase9_approved_app: dict):
    """Proves that page content / prompt injections cannot alter system policy or force auto-submit."""
    app_entity = setup_phase9_approved_app["app"]
    app_entity.portal_type = "generic"
    db_session.commit()
    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    fixture_url = f"file://{FIXTURES_DIR / 'prompt_injection_app.html'}"
    run = browser_preparation_engine.prepare_application(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "staged"
    assert run.final_submit_clicked is False
    assert run.guard_triggered is True
