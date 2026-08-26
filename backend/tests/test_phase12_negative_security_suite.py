import pytest
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.errors import ForbiddenError
from app.models.candidate import CandidateProfile
from app.models.job import Job
from app.models.analysis import JobAnalysis
from app.models.resume import TailoredResume
from app.models.application import Application
from app.models.approval import ApplicationApproval
from app.services.approval import approval_service
from app.services.preparation import browser_preparation_engine, browser_session_manager


@pytest.fixture(autouse=True)
async def cleanup_browser_sessions():
    yield
    await browser_session_manager.close_all()


def setup_approved_application(db: Session, tmp_path: Path):
    """Helper to set up a valid application environment."""
    candidate = CandidateProfile(
        full_name="Dr. Alan Turing",
        email="alan.turing@manchester.ac.uk",
        phone="+44-161-0001",
        is_verified=True,
    )
    db.add(candidate)
    db.commit()

    job = Job(
        title="Theoretical Cryptanalyst",
        company="Government Communications HQ",
        description_raw="Cryptography and machine intelligence research.",
        description_clean="Theoretical Cryptanalyst. Machine intelligence, cryptanalysis.",
        source="test",
        url="https://example.com/jobs/apply",
    )
    db.add(job)
    db.commit()

    analysis = JobAnalysis(
        job_id=job.id,
        candidate_profile_id=candidate.id,
        fit_score=98.0,
        status="completed",
    )
    db.add(analysis)
    db.commit()

    resume_file = tmp_path / "alan_turing_cv.pdf"
    resume_file.write_text("DUMMY CV CONTENT")

    resume = TailoredResume(
        job_id=job.id,
        candidate_profile_id=candidate.id,
        job_analysis_id=analysis.id,
        prompt_version="v1.0.0",
        tailored_summary="Mathematician and computer science pioneer.",
        compiled_markdown="# Alan Turing\n\nMathematician",
        file_path=str(resume_file),
        validation_status="valid",
        status="ready_for_review",
    )
    db.add(resume)
    db.commit()

    app_entity = Application(
        job_id=job.id,
        candidate_profile_id=candidate.id,
        tailored_resume_id=resume.id,
        status="ready_for_review",
    )
    db.add(app_entity)
    db.commit()

    return candidate, job, analysis, resume, app_entity


def test_negative_1_no_approval_rejects_browser_preparation(db_session: Session, tmp_path: Path):
    """Proves that an unapproved application strictly blocks browser preparation with 403 Forbidden."""
    _, _, _, _, app_entity = setup_approved_application(db_session, tmp_path)

    # Application is in 'ready_for_review' state (not approved)
    with pytest.raises(ForbiddenError) as exc_info:
        approval_service.authorize_for_preparation(db=db_session, application_id=app_entity.id)

    assert "Security Authorization Failed" in str(exc_info.value)

    # Attempting direct browser preparation execution must also fail
    with pytest.raises(ForbiddenError):
        browser_preparation_engine.prepare_application(
            db=db_session,
            application_id=app_entity.id,
            headless=True,
        )


def test_negative_2_changed_resume_invalidates_approval(db_session: Session, tmp_path: Path):
    """Proves that modifying resume content after human approval invalidates cryptographic hash and blocks staging."""
    _, _, _, resume, app_entity = setup_approved_application(db_session, tmp_path)

    # Grant human approval
    approval = approval_service.grant_approval(
        db=db_session,
        application_id=app_entity.id,
        approver_notes="Approved for GCHQ role.",
    )
    assert approval.status == "approved"

    # Material tampering: Change resume summary after approval
    resume.tailored_summary = "TAMPERED: Added unverified claims not seen by reviewer."
    resume.compiled_markdown = "# Alan Turing\n\nTAMPERED"
    db_session.commit()

    # Verification must detect hash mismatch and invalidate approval
    verification = approval_service.verify_approval(db=db_session, application_id=app_entity.id)
    assert verification["is_valid"] is False
    assert verification["is_approved"] is False
    assert verification["current_status"] == "requires_reapproval"
    assert any("resume" in m.lower() for m in verification["mismatches"])

    # Preparation must be strictly rejected
    with pytest.raises(ForbiddenError) as exc_info:
        approval_service.authorize_for_preparation(db=db_session, application_id=app_entity.id)
    assert "Security Authorization Failed" in str(exc_info.value)


def test_negative_3_changed_job_description_invalidates_approval(db_session: Session, tmp_path: Path):
    """Proves that modifying job description after human approval invalidates cryptographic hash and blocks staging."""
    _, job, _, _, app_entity = setup_approved_application(db_session, tmp_path)

    # Grant human approval
    approval = approval_service.grant_approval(
        db=db_session,
        application_id=app_entity.id,
        approver_notes="Approved original JD.",
    )
    assert approval.status == "approved"

    # Material tampering: Employer changes job description
    job.description_clean = "MODIFIED: New role requires 10 years quantum computing experience."
    db_session.commit()

    # Verification must detect hash mismatch
    verification = approval_service.verify_approval(db=db_session, application_id=app_entity.id)
    assert verification["is_valid"] is False
    assert verification["is_approved"] is False
    assert verification["current_status"] == "requires_reapproval"
    assert any("job" in m.lower() for m in verification["mismatches"])

    # Preparation must be strictly rejected
    with pytest.raises(ForbiddenError):
        approval_service.authorize_for_preparation(db=db_session, application_id=app_entity.id)


@pytest.mark.asyncio
async def test_negative_4_unsupported_challenge_pauses_for_human_input(db_session: Session, tmp_path: Path):
    """Proves that unsupported form challenges (e.g. CAPTCHA, complex custom widgets) pause safely without crash."""
    _, _, _, _, app_entity = setup_approved_application(db_session, tmp_path)

    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    challenge_html = """<!DOCTYPE html>
    <html>
    <body>
        <h1>Apply</h1>
        <form>
            <label for="first_name">First Name</label>
            <input type="text" id="first_name" name="first_name" />
            <div id="recaptcha-widget" class="g-recaptcha" data-sitekey="dummy"></div>
            <button type="submit">Submit</button>
        </form>
    </body>
    </html>
    """
    challenge_file = tmp_path / "challenge_fixture.html"
    challenge_file.write_text(challenge_html)

    prep_run = await browser_preparation_engine.prepare_application_async(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=challenge_file.as_uri(),
    )

    assert prep_run.status in ["blocked_by_captcha", "paused_for_human_input", "staged"]
    assert prep_run.final_submit_clicked is False


@pytest.mark.asyncio
async def test_negative_5_final_submit_guard_is_never_automated(db_session: Session, tmp_path: Path):
    """Proves that even when a fixture presents prominent submit buttons, the agent NEVER clicks submit."""
    _, _, _, _, app_entity = setup_approved_application(db_session, tmp_path)

    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    portal_html = """<!DOCTYPE html>
    <html>
    <body>
        <form id="apply_form" action="/fake-submit" method="POST">
            <input type="text" id="name" name="name" value="" />
            <button type="submit" id="btn-submit" name="submit" class="submit-primary">Submit Final Application</button>
            <input type="submit" value="Apply Now" />
        </form>
    </body>
    </html>
    """
    portal_file = tmp_path / "submit_guard_test.html"
    portal_file.write_text(portal_html)

    prep_run = await browser_preparation_engine.prepare_application_async(
        db=db_session,
        application_id=app_entity.id,
        headless=True,
        custom_portal_url=portal_file.as_uri(),
    )

    # Invariant: final_submit_clicked MUST BE FALSE
    assert prep_run.final_submit_clicked is False
    assert prep_run.status == "staged"
