import pytest
from sqlalchemy.orm import Session

from app.core.errors import BadRequestError, ForbiddenError
from app.models.job import Job
from app.models.candidate import CandidateProfile, WorkExperience, CandidateSkill
from app.models.analysis import JobAnalysis
from app.models.resume import TailoredResume
from app.models.application import Application
from app.models.audit import AuditLog
from app.services.approval import (
    approval_service,
    ApplicationStatus,
    compute_job_hash,
    compute_candidate_hash,
    compute_resume_hash,
    compute_answers_hash,
)


@pytest.fixture
def setup_phase8_data(db_session: Session):
    profile = CandidateProfile(
        full_name="Ada Lovelace",
        email="ada@analytical.org",
        location="London, UK",
        headline="Pioneer of Algorithmic Computation",
        is_verified=True,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    exp = WorkExperience(
        profile_id=profile.id,
        company="Babbage Engine Labs",
        position="Principal Mathematician",
        start_date="1842-01-01",
        is_current=False,
        highlights=["Authored first algorithm intended for mechanical execution."],
        skills_used=["Algorithms", "Applied Mathematics"],
        is_verified=True,
        order_index=0,
    )
    db_session.add(exp)

    skill = CandidateSkill(
        profile_id=profile.id,
        name="Algorithmic Design",
        category="Engineering",
        proficiency="expert",
        is_verified=True,
    )
    db_session.add(skill)
    db_session.commit()
    db_session.refresh(profile)

    job = Job(
        title="Senior Distributed Systems Engineer",
        company="Anthropic",
        location="San Francisco, CA",
        remote_type="remote",
        description_raw="Design reliable training cluster orchestration and state synchronization.",
        description_clean="Design reliable training cluster orchestration and state synchronization.",
        source="unit_test",
        url="https://anthropic.com/careers/dist-sys-1",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    analysis = JobAnalysis(
        job_id=job.id,
        candidate_profile_id=profile.id,
        fit_score=96.0,
        fit_level="high",
        recommendation="strong_apply",
        matched_skills=["Algorithms", "Distributed Systems"],
        status="completed",
    )
    db_session.add(analysis)

    resume = TailoredResume(
        job_id=job.id,
        candidate_profile_id=profile.id,
        job_analysis_id=analysis.id,
        prompt_version="v1.0.0",
        tailored_summary="Mathematician and computing architect specialized in discrete algorithm design.",
        tailored_experience=[
            {
                "company": "Babbage Engine Labs",
                "position": "Principal Mathematician",
                "tailored_highlights": [
                    {"text": "Designed Bernoulli number computation sequence.", "source_fact_ids": ["exp:1:h0"]}
                ],
            }
        ],
        highlighted_skills=["Algorithms", "Applied Mathematics"],
        cover_letter="Dear Anthropic Team,\n\nI am thrilled to apply for the Senior Distributed Systems Engineer role.",
        compiled_markdown="# Ada Lovelace\n\n## Summary\nMathematician...",
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
        answers_payload={"authorized_in_us": True, "notice_period": "none"},
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


def test_grant_approval_and_cryptographic_binding(db_session: Session, setup_phase8_data: dict):
    app_entity = setup_phase8_data["app"]
    job = setup_phase8_data["job"]
    profile = setup_phase8_data["profile"]
    resume = setup_phase8_data["resume"]

    approval = approval_service.grant_approval(
        db=db_session,
        application_id=app_entity.id,
        approver_notes="Verified facts against master record. Ready to apply.",
    )

    assert approval.id is not None
    assert approval.is_valid is True
    assert approval.status == "approved"
    assert approval.approval_token.startswith(f"auth_app_{app_entity.id}_")
    assert approval.approved_job_hash == compute_job_hash(job)
    assert approval.approved_candidate_hash == compute_candidate_hash(profile)
    assert approval.approved_resume_hash == compute_resume_hash(resume)
    assert approval.approved_answers_hash == compute_answers_hash(app_entity.answers_payload)

    # Verify Application updated
    db_session.refresh(app_entity)
    assert app_entity.status == ApplicationStatus.APPROVED.value
    assert app_entity.approval_token == approval.approval_token

    # Verify AuditLog created
    audit = db_session.query(AuditLog).filter(AuditLog.application_id == app_entity.id, AuditLog.action == "APPLICATION_HUMAN_APPROVED").first()
    assert audit is not None


def test_verify_approval_detects_material_change_in_candidate_profile(db_session: Session, setup_phase8_data: dict):
    app_entity = setup_phase8_data["app"]
    profile = setup_phase8_data["profile"]

    # 1. Grant approval
    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    # 2. Verify active approval before tamper
    ver1 = approval_service.verify_approval(db=db_session, application_id=app_entity.id)
    assert ver1["is_valid"] is True

    # 3. Material Change: Add unverified skill or edit profile experience
    new_skill = CandidateSkill(
        profile_id=profile.id,
        name="Quantum Algorithms",
        category="Physics",
        proficiency="intermediate",
        is_verified=False,
    )
    db_session.add(new_skill)
    db_session.commit()
    db_session.refresh(profile)

    # 4. Verify approval: Must detect mismatch and invalidate
    ver2 = approval_service.verify_approval(db=db_session, application_id=app_entity.id)
    assert ver2["is_valid"] is False
    assert "Approval invalidated" in ver2["reason"]

    # 5. Check state machine transition to requires_reapproval
    db_session.refresh(app_entity)
    assert app_entity.status == ApplicationStatus.REQUIRES_REAPPROVAL.value


def test_verify_approval_detects_material_change_in_tailored_resume(db_session: Session, setup_phase8_data: dict):
    app_entity = setup_phase8_data["app"]
    resume = setup_phase8_data["resume"]

    # 1. Grant approval
    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    # 2. Tamper with tailored resume highlights
    resume.tailored_summary = "Modified summary after approval without reviewer signoff."
    db_session.commit()

    # 3. Verification must fail
    ver = approval_service.verify_approval(db=db_session, application_id=app_entity.id)
    assert ver["is_valid"] is False
    assert any("resume" in m.lower() for m in ver["mismatches"])

    db_session.refresh(app_entity)
    assert app_entity.status == ApplicationStatus.REQUIRES_REAPPROVAL.value


def test_verify_approval_detects_material_change_in_screening_answers(db_session: Session, setup_phase8_data: dict):
    app_entity = setup_phase8_data["app"]

    # 1. Grant approval
    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    # 2. Change answers payload
    app_entity.answers_payload = {"authorized_in_us": False, "requires_visa": True}
    db_session.commit()

    # 3. Verification must fail
    ver = approval_service.verify_approval(db=db_session, application_id=app_entity.id)
    assert ver["is_valid"] is False
    assert any("screening" in m.lower() for m in ver["mismatches"])


def test_authorize_preparation_gate_security(db_session: Session, setup_phase8_data: dict):
    app_entity = setup_phase8_data["app"]

    # Attempt to authorize preparation on unapproved application -> MUST RAISE ForbiddenError
    with pytest.raises(ForbiddenError):
        approval_service.authorize_for_preparation(db=db_session, application_id=app_entity.id)

    # Grant valid human approval
    approval_service.grant_approval(db=db_session, application_id=app_entity.id)

    # Now authorization must SUCCEED and stage application
    auth = approval_service.authorize_for_preparation(db=db_session, application_id=app_entity.id)
    assert auth["authorization_granted"] is True
    assert auth["status"] == ApplicationStatus.STAGED_FOR_PREPARATION.value
    assert auth["approval_token"].startswith(f"auth_app_{app_entity.id}_")
