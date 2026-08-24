from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.candidate import CandidateProfile, CandidateSkill
from app.models.analysis import JobAnalysis
from app.models.resume import TailoredResume

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "portals"


def test_phase9_preparation_api_workflow(client: TestClient, db_session: Session):
    # 1. Setup Candidate, Job, Analysis, Resume
    profile = CandidateProfile(
        full_name="Dorothy Vaughan",
        email="dorothy@nasa.gov",
        phone="+1 757-555-0100",
        location="Newport News, VA",
        headline="FORTRAN Programming Pioneer",
        is_verified=True,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    skill = CandidateSkill(profile_id=profile.id, name="FORTRAN", category="Programming", proficiency="expert", is_verified=True)
    db_session.add(skill)
    db_session.commit()

    job = Job(
        title="Supercomputing Systems Engineer",
        company="NASA Langley",
        location="Hampton, VA",
        remote_type="on_site",
        description_raw="Manage IBM 7090 programming and compiler toolchains.",
        description_clean="Manage IBM 7090 programming and compiler toolchains.",
        source="phase9_api_test",
        url="https://nasa.gov/careers/ibm-7090",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    analysis = JobAnalysis(job_id=job.id, candidate_profile_id=profile.id, fit_score=97.0, status="completed")
    db_session.add(analysis)
    db_session.commit()

    resume = TailoredResume(
        job_id=job.id,
        candidate_profile_id=profile.id,
        job_analysis_id=analysis.id,
        prompt_version="v1.0.0",
        tailored_summary="Programmer and mathematician who led transition to algorithmic computing.",
        compiled_markdown="# Dorothy Vaughan\n\nFORTRAN Programmer",
        validation_status="valid",
        status="ready_for_review",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    app_res = client.post("/api/v1/applications", json={
        "job_id": job.id,
        "tailored_resume_id": resume.id,
        "candidate_profile_id": profile.id,
        "status": "ready_for_review",
        "answers_payload": {"work_auth": True},
    })
    assert app_res.status_code == 201
    app_id = app_res.json()["id"]

    fixture_url = f"file://{FIXTURES_DIR / 'greenhouse_job_app.html'}"

    # --- NEGATIVE REST API TEST: Attempt preparation without human approval -> 403 Forbidden ---
    prep_unauth_res = client.post(f"/api/v1/applications/{app_id}/prepare", json={"custom_portal_url": fixture_url})
    assert prep_unauth_res.status_code == 403
    assert "Security Authorization Failed" in prep_unauth_res.json()["error"]["message"]

    # --- POSITIVE REST API STEP: Grant Human Approval ---
    approve_res = client.post(f"/api/v1/applications/{app_id}/approve", json={"approver_notes": "Ground-truth verified."})
    assert approve_res.status_code == 200

    # --- EXECUTE PREPARATION VIA REST API ---
    prep_res = client.post(f"/api/v1/applications/{app_id}/prepare", json={"custom_portal_url": fixture_url, "headless": True})
    assert prep_res.status_code == 200
    data = prep_res.json()
    assert data["status"] == "staged"
    assert data["application_id"] == app_id
    assert data["final_submit_clicked"] is False
    assert data["guard_triggered"] is True
    assert data["screenshot_path"] is not None
    assert len(data["fields_filled"]) > 0

    # --- FETCH PREPARATION RUNS LIST ---
    list_res = client.get(f"/api/v1/applications/{app_id}/preparation-runs")
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1

    # --- FETCH LATEST PREPARATION RUN ---
    latest_res = client.get(f"/api/v1/applications/{app_id}/preparation-runs/latest")
    assert latest_res.status_code == 200
    assert latest_res.json()["id"] == data["id"]
