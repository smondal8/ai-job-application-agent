from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.candidate import CandidateProfile, WorkExperience, CandidateSkill
from app.models.analysis import JobAnalysis
from app.models.resume import TailoredResume
from app.models.application import Application


def test_negative_security_unauthorized_preparation_attempts(client: TestClient, db_session: Session):
    # 1. Candidate Profile (Verified)
    profile = CandidateProfile(
        full_name="Grace Hopper",
        email="grace@navy.mil",
        location="Arlington, VA",
        headline="Rear Admiral & Computer Scientist",
        is_verified=True,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    skill = CandidateSkill(profile_id=profile.id, name="Compilers", category="Software", proficiency="expert", is_verified=True)
    db_session.add(skill)
    db_session.commit()

    # 2. Job Listing
    job = Job(
        title="Principal Compiler Architect",
        company="NVIDIA",
        location="Santa Clara, CA",
        remote_type="hybrid",
        description_raw="Developing CUDA JIT compiler toolchains and parallel optimization passes.",
        description_clean="Developing CUDA JIT compiler toolchains and parallel optimization passes.",
        source="unit_test",
        url="https://nvidia.com/jobs/comp-1",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    # 3. Job Analysis
    analysis = JobAnalysis(
        job_id=job.id,
        candidate_profile_id=profile.id,
        fit_score=99.0,
        status="completed",
    )
    db_session.add(analysis)

    # 4. Tailored Resume (Valid)
    resume = TailoredResume(
        job_id=job.id,
        candidate_profile_id=profile.id,
        job_analysis_id=analysis.id,
        prompt_version="v1.0.0",
        tailored_summary="Pioneered first compiler (A-0) and machine-independent programming languages.",
        compiled_markdown="# Grace Hopper\n\nCompiler Architect...",
        validation_status="valid",
        status="ready_for_review",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    # 5. Create Draft Application
    app_res = client.post(
        "/api/v1/applications",
        json={"job_id": job.id, "tailored_resume_id": resume.id, "status": "draft", "answers_payload": {"security_clearance": "Top Secret"}},
    )
    assert app_res.status_code == 201
    app_id = app_res.json()["id"]

    # --- NEGATIVE TEST 1: Attempt preparation on DRAFT application without approval -> 403 FORBIDDEN ---
    prep_res1 = client.post(f"/api/v1/applications/{app_id}/authorize-preparation")
    assert prep_res1.status_code == 403
    assert "Security Authorization Failed" in prep_res1.json()["error"]["message"]

    # --- NEGATIVE TEST 2: Move to READY_FOR_REVIEW without approval -> 403 FORBIDDEN ---
    client.put(f"/api/v1/applications/{app_id}", json={"status": "ready_for_review"})
    prep_res2 = client.post(f"/api/v1/applications/{app_id}/authorize-preparation")
    assert prep_res2.status_code == 403

    # --- POSITIVE STEP: Grant Valid Human Approval ---
    approve_res = client.post(
        f"/api/v1/applications/{app_id}/approve",
        json={"approver_notes": "Security credentials and compiler publications verified.", "approver_id": "lead_reviewer"},
    )
    assert approve_res.status_code == 200
    approval_token = approve_res.json()["approval_token"]
    assert approval_token is not None

    # Verify authorization succeeds when approval is intact
    prep_res3 = client.post(f"/api/v1/applications/{app_id}/authorize-preparation")
    assert prep_res3.status_code == 200
    assert prep_res3.json()["authorization_granted"] is True
    assert prep_res3.json()["status"] == "staged_for_preparation"

    # --- NEGATIVE TEST 3: Material change in Candidate Profile invalidates approval -> 403 FORBIDDEN ---
    # Tamper with profile (e.g. modify name or email)
    client.put(f"/api/v1/profile/{profile.id}", json={"full_name": "Grace Brewster Murray Hopper (Modified)"})
    
    # Attempt preparation now -> Must detect material change and reject with 403 Forbidden
    prep_res4 = client.post(f"/api/v1/applications/{app_id}/authorize-preparation")
    assert prep_res4.status_code == 403
    assert "Approval invalidated due to material changes" in prep_res4.json()["error"]["message"]

    # --- POSITIVE STEP: Re-approve application after profile change ---
    reapprove_res = client.post(
        f"/api/v1/applications/{app_id}/approve",
        json={"approver_notes": "Re-approved updated legal name.", "approver_id": "lead_reviewer"},
    )
    assert reapprove_res.status_code == 200

    # Authorization succeeds again
    prep_res5 = client.post(f"/api/v1/applications/{app_id}/authorize-preparation")
    assert prep_res5.status_code == 200

    # --- NEGATIVE TEST 4: Material change in Screening Answers payload invalidates approval -> 403 FORBIDDEN ---
    client.put(f"/api/v1/applications/{app_id}", json={"answers_payload": {"security_clearance": "Expired"}})

    prep_res6 = client.post(f"/api/v1/applications/{app_id}/authorize-preparation")
    assert prep_res6.status_code == 403

    # --- NEGATIVE TEST 5: Revoke approval explicitly -> 403 FORBIDDEN ---
    # First re-approve
    client.post(f"/api/v1/applications/{app_id}/approve", json={"approver_notes": "Re-approved answers."})
    # Then revoke
    revoke_res = client.post(f"/api/v1/applications/{app_id}/revoke-approval?reason=Security+audit+hold")
    assert revoke_res.status_code == 200
    # Attempt preparation
    prep_res7 = client.post(f"/api/v1/applications/{app_id}/authorize-preparation")
    assert prep_res7.status_code == 403

    # --- NEGATIVE TEST 6: Reject application -> 403 FORBIDDEN ---
    reject_res = client.post(f"/api/v1/applications/{app_id}/reject?reason=Role+filled")
    assert reject_res.status_code == 200
    prep_res8 = client.post(f"/api/v1/applications/{app_id}/authorize-preparation")
    assert prep_res8.status_code == 403


def test_approval_gate_blocks_unverified_candidate_profile(client: TestClient, db_session: Session):
    # Candidate profile is UNVERIFIED
    profile = CandidateProfile(
        full_name="Unverified Applicant",
        email="unverified@example.com",
        is_verified=False,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    job = Job(title="Backend Dev", company="Acme", source="test")
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    resume = TailoredResume(
        job_id=job.id,
        candidate_profile_id=profile.id,
        prompt_version="v1.0.0",
        validation_status="valid",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    app_res = client.post("/api/v1/applications", json={"job_id": job.id, "tailored_resume_id": resume.id, "candidate_profile_id": profile.id})
    app_id = app_res.json()["id"]

    # Attempting to grant approval on unverified candidate profile MUST fail with 400 Bad Request
    approve_res = client.post(f"/api/v1/applications/{app_id}/approve", json={"approver_notes": "Attempting unverified approval"})
    assert approve_res.status_code == 400
    assert "Candidate profile must be verified" in approve_res.json()["error"]["message"]
