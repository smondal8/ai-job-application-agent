import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.job import Job
from app.models.candidate import CandidateProfile
from app.models.analysis import JobAnalysis
from app.models.resume import TailoredResume
from app.models.application import Application
from app.models.approval import ApplicationApproval
from app.services.idempotency import idempotency_service


def test_idempotency_service_caches_and_replays(db_session: Session):
    """Proves idempotency service registers in-progress request and replays completed response."""
    key = "test_key_abc_123"
    payload = {"foo": "bar", "count": 42}

    # 1. First execution: not cached
    rec1, is_cached1 = idempotency_service.process_idempotent_request(
        db=db_session,
        idempotency_key=key,
        resource_type="test_resource",
        request_payload=payload,
    )
    assert is_cached1 is False
    assert rec1 is not None
    assert rec1.status == "in_progress"

    # 2. Complete operation
    response_data = {"result": "success", "id": 999}
    idempotency_service.complete_idempotent_request(db_session, key, response_data)

    # 3. Second execution: cached HIT
    rec2, is_cached2 = idempotency_service.process_idempotent_request(
        db=db_session,
        idempotency_key=key,
        resource_type="test_resource",
        request_payload=payload,
    )
    assert is_cached2 is True
    assert rec2.status == "completed"
    assert rec2.response_payload == response_data


def test_approval_api_idempotency_header(client: TestClient, db_session: Session):
    """Proves that multiple POST requests with identical X-Idempotency-Key return cached approval without duplicate DB rows."""
    profile = CandidateProfile(full_name="Katherine Johnson", email="katherine@nasa.gov", is_verified=True)
    db_session.add(profile)
    db_session.commit()

    job = Job(
        title="Orbital Mechanics Lead",
        company="NASA Langley",
        description_raw="Calculate trajectories.",
        description_clean="Calculate trajectories.",
        source="test",
        url="https://example.com/apply",
    )
    db_session.add(job)
    db_session.commit()

    analysis = JobAnalysis(job_id=job.id, candidate_profile_id=profile.id, fit_score=99.0, status="completed")
    db_session.add(analysis)
    db_session.commit()

    resume = TailoredResume(
        job_id=job.id,
        candidate_profile_id=profile.id,
        job_analysis_id=analysis.id,
        prompt_version="v1.0.0",
        tailored_summary="Pioneering mathematician & aerospace calculation specialist.",
        compiled_markdown="# Katherine Johnson\n\nMathematician",
        validation_status="valid",
        status="ready_for_review",
    )
    db_session.add(resume)
    db_session.commit()

    app_entity = Application(
        job_id=job.id,
        tailored_resume_id=resume.id,
        candidate_profile_id=profile.id,
        status="ready_for_review",
    )
    db_session.add(app_entity)
    db_session.commit()

    idemp_key = "idemp_approval_test_7788"

    # First approval request with header
    res1 = client.post(
        f"/api/v1/applications/{app_entity.id}/approve",
        json={"approver_notes": "First approval call."},
        headers={"X-Idempotency-Key": idemp_key},
    )
    assert res1.status_code == 200
    token1 = res1.json()["approval_token"]

    # Verify 1 approval row in DB
    approvals_count1 = db_session.query(ApplicationApproval).filter(ApplicationApproval.application_id == app_entity.id).count()
    assert approvals_count1 == 1

    # Second approval request with same key
    res2 = client.post(
        f"/api/v1/applications/{app_entity.id}/approve",
        json={"approver_notes": "First approval call."},
        headers={"X-Idempotency-Key": idemp_key},
    )
    assert res2.status_code == 200
    assert res2.json()["approval_token"] == token1

    # Verify STILL only 1 approval row in DB (no duplicates created)
    approvals_count2 = db_session.query(ApplicationApproval).filter(ApplicationApproval.application_id == app_entity.id).count()
    assert approvals_count2 == 1
