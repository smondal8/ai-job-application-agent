import pytest
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.candidate import CandidateProfile, CandidateSkill, WorkExperience
from app.models.analysis import JobAnalysis
from app.models.resume import TailoredResume
from app.models.application import Application
from app.services.approval import approval_service
from app.services.preparation import (
    browser_preparation_engine,
    preparation_adapter_registry,
)
from app.services.preparation.adapters import (
    GreenhousePreparationAdapter,
    LeverPreparationAdapter,
    AshbyPreparationAdapter,
    WorkdayPreparationAdapter,
    GenericPortalPreparationAdapter,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "portals"


@pytest.fixture
def setup_phase10_candidate_and_job(db_session: Session):
    profile = CandidateProfile(
        full_name="Grace Hopper",
        email="grace.hopper@navy.mil",
        phone="+1 202-555-0199",
        location="Arlington, VA",
        headline="Pioneering Computer Scientist & Rear Admiral",
        linkedin_url="https://linkedin.com/in/grace-hopper",
        github_url="https://github.com/grace-hopper",
        portfolio_url="https://gracehopper.org",
        is_verified=True,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    exp = WorkExperience(
        profile_id=profile.id,
        company="United States Navy",
        position="Director of NAVDAC",
        start_date="1943-12-01",
        is_current=True,
        is_verified=True,
        order_index=0,
    )
    db_session.add(exp)

    skill = CandidateSkill(profile_id=profile.id, name="Compilers", category="Software", proficiency="expert", is_verified=True)
    db_session.add(skill)
    db_session.commit()

    job = Job(
        title="Lead Compiler Architect",
        company="Universal Systems Corp",
        location="Washington, DC",
        remote_type="hybrid",
        description_raw="Design machine-independent programming language compilers.",
        description_clean="Design machine-independent programming language compilers.",
        source="phase10_test",
        url="https://boards.greenhouse.io/universal/jobs/101",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    analysis = JobAnalysis(job_id=job.id, candidate_profile_id=profile.id, fit_score=98.0, status="completed")
    db_session.add(analysis)
    db_session.commit()

    resume = TailoredResume(
        job_id=job.id,
        candidate_profile_id=profile.id,
        job_analysis_id=analysis.id,
        prompt_version="v1.0.0",
        tailored_summary="Creator of the first compiler (A-0) and pioneer of English-like data processing languages.",
        cover_letter="Dear Hiring Team,\n\nI am eager to architect standard compiler toolchains for your modern compute platforms.",
        compiled_markdown="# Grace Hopper\n\nCompiler Architect",
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

    # Grant valid human approval
    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    return {
        "profile": profile,
        "job": job,
        "resume": resume,
        "app": app_entity,
    }


def test_adapter_registry_resolution():
    """Verify registry resolves specialized adapters based on portal_type or target URL."""
    # Greenhouse
    gh_by_type = preparation_adapter_registry.get_adapter("greenhouse", "https://example.com")
    assert isinstance(gh_by_type, GreenhousePreparationAdapter)
    gh_by_url = preparation_adapter_registry.get_adapter(None, "https://boards.greenhouse.io/company/jobs/123")
    assert isinstance(gh_by_url, GreenhousePreparationAdapter)

    # Lever
    lever_by_type = preparation_adapter_registry.get_adapter("lever", "https://example.com")
    assert isinstance(lever_by_type, LeverPreparationAdapter)
    lever_by_url = preparation_adapter_registry.get_adapter(None, "https://jobs.lever.co/company/abc")
    assert isinstance(lever_by_url, LeverPreparationAdapter)

    # Ashby
    ashby_by_type = preparation_adapter_registry.get_adapter("ashby", "https://example.com")
    assert isinstance(ashby_by_type, AshbyPreparationAdapter)
    ashby_by_url = preparation_adapter_registry.get_adapter(None, "https://jobs.ashbyhq.com/company/xyz")
    assert isinstance(ashby_by_url, AshbyPreparationAdapter)

    # Workday
    wd_by_type = preparation_adapter_registry.get_adapter("workday", "https://example.com")
    assert isinstance(wd_by_type, WorkdayPreparationAdapter)
    wd_by_url = preparation_adapter_registry.get_adapter(None, "https://company.myworkdayjobs.com/careers/job/1")
    assert isinstance(wd_by_url, WorkdayPreparationAdapter)

    # Generic Fallback
    gen = preparation_adapter_registry.get_adapter("custom_portal", "https://careers.example.com")
    assert isinstance(gen, GenericPortalPreparationAdapter)


def test_greenhouse_adapter_preparation(db_session: Session, setup_phase10_candidate_and_job: dict):
    app_entity = setup_phase10_candidate_and_job["app"]
    fixture_url = f"file://{FIXTURES_DIR / 'greenhouse_job_app.html'}"

    run = browser_preparation_engine.prepare_application(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "staged"
    assert run.portal_type == "greenhouse"
    assert run.resume_uploaded is True
    assert run.final_submit_clicked is False
    assert run.guard_triggered is True
    assert any(f["field"] == "first_name" and "Grace" in f["value"] for f in run.fields_filled)
    assert any(f["field"] == "last_name" and "Hopper" in f["value"] for f in run.fields_filled)
    assert any(f["field"] == "email" and "grace.hopper@navy.mil" in f["value"] for f in run.fields_filled)
    assert run.screenshot_path is not None


def test_greenhouse_adapter_handles_altered_layout_gracefully(db_session: Session, setup_phase10_candidate_and_job: dict):
    """When Greenhouse DOM structure is altered / missing, adapter safely pauses for human review."""
    app_entity = setup_phase10_candidate_and_job["app"]
    fixture_url = f"file://{FIXTURES_DIR / 'greenhouse_layout_changed.html'}"

    run = browser_preparation_engine.prepare_application(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "paused_for_human_input"
    assert run.portal_type == "greenhouse"
    assert run.final_submit_clicked is False
    assert any("layout" in u["field"] for u in run.unresolved_fields)
    assert run.screenshot_path is not None


def test_lever_adapter_preparation(db_session: Session, setup_phase10_candidate_and_job: dict):
    app_entity = setup_phase10_candidate_and_job["app"]
    app_entity.portal_type = "lever"
    db_session.commit()

    fixture_url = f"file://{FIXTURES_DIR / 'lever_job_app.html'}"
    run = browser_preparation_engine.prepare_application(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "staged"
    assert run.portal_type == "lever"
    assert run.final_submit_clicked is False
    assert run.guard_triggered is True
    assert any(f["field"] == "name" and "Grace Hopper" in f["value"] for f in run.fields_filled)
    assert any(f["field"] == "org" and "United States Navy" in f["value"] for f in run.fields_filled)
    assert any(f["field"] == "linkedin_url" for f in run.fields_filled)
    assert run.screenshot_path is not None


def test_lever_adapter_unresolved_custom_questions(db_session: Session, setup_phase10_candidate_and_job: dict):
    """When Lever portal contains unsupported required questions, adapter pauses for user."""
    app_entity = setup_phase10_candidate_and_job["app"]
    app_entity.portal_type = "lever"
    db_session.commit()

    fixture_url = f"file://{FIXTURES_DIR / 'lever_custom_questions.html'}"
    run = browser_preparation_engine.prepare_application(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "paused_for_human_input"
    assert len(run.unresolved_fields) >= 1
    assert any("custom_notice_period_weeks" in u["field"] for u in run.unresolved_fields)
    assert run.final_submit_clicked is False


def test_ashby_adapter_preparation(db_session: Session, setup_phase10_candidate_and_job: dict):
    app_entity = setup_phase10_candidate_and_job["app"]
    app_entity.portal_type = "ashby"
    db_session.commit()

    fixture_url = f"file://{FIXTURES_DIR / 'ashby_job_app.html'}"
    run = browser_preparation_engine.prepare_application(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "staged"
    assert run.portal_type == "ashby"
    assert run.final_submit_clicked is False
    assert run.guard_triggered is True
    assert any(f["field"] == "name" and "Grace Hopper" in f["value"] for f in run.fields_filled)
    assert any(f["field"] == "email" and "grace.hopper@navy.mil" in f["value"] for f in run.fields_filled)
    assert run.resume_uploaded is True


def test_workday_adapter_preparation(db_session: Session, setup_phase10_candidate_and_job: dict):
    app_entity = setup_phase10_candidate_and_job["app"]
    app_entity.portal_type = "workday"
    db_session.commit()

    fixture_url = f"file://{FIXTURES_DIR / 'workday_job_app.html'}"
    run = browser_preparation_engine.prepare_application(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "staged"
    assert run.portal_type == "workday"
    assert run.final_submit_clicked is False
    assert run.guard_triggered is True
    assert any(f["field"] == "first_name" and "Grace" in f["value"] for f in run.fields_filled)
    assert any(f["field"] == "last_name" and "Hopper" in f["value"] for f in run.fields_filled)
    assert any(f["field"] == "email" and "grace.hopper@navy.mil" in f["value"] for f in run.fields_filled)
    assert run.resume_uploaded is True


def test_workday_adapter_detects_login_wall_and_pauses(db_session: Session, setup_phase10_candidate_and_job: dict):
    """When Workday candidate login screen is encountered, adapter halts safely without attempting bypass."""
    app_entity = setup_phase10_candidate_and_job["app"]
    app_entity.portal_type = "workday"
    db_session.commit()

    fixture_url = f"file://{FIXTURES_DIR / 'workday_auth_wall.html'}"
    run = browser_preparation_engine.prepare_application(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=fixture_url,
    )

    assert run.status == "blocked_by_auth"
    assert run.auth_required is True
    assert run.final_submit_clicked is False
    assert run.screenshot_path is not None
