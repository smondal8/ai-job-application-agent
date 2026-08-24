from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.candidate import CandidateProfile
from app.models.analysis import JobAnalysis
from app.models.resume import TailoredResume
from app.models.application import Application


def test_phase7_application_endpoints_workflow(client: TestClient, db_session: Session):
    # 1. Setup Candidate, Job, Analysis, and Resume
    profile = CandidateProfile(
        full_name="Sam Altman",
        email="sam@example.com",
        location="San Francisco, CA",
        headline="CEO & Tech Architect",
        is_verified=True,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    job = Job(
        title="Distinguished Systems Architect",
        company="Stripe",
        location="San Francisco, CA",
        remote_type="remote",
        description_raw="Leading global payments consensus engines and distributed state machines.",
        source="unit_test",
        url="https://stripe.com/jobs/dist-sys-1",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    analysis = JobAnalysis(
        job_id=job.id,
        candidate_profile_id=profile.id,
        fit_score=98.0,
        fit_level="high",
        recommendation="strong_apply",
        matched_skills=["Distributed Systems", "Python", "FastAPI"],
        status="completed",
    )
    db_session.add(analysis)

    resume = TailoredResume(
        job_id=job.id,
        candidate_profile_id=profile.id,
        job_analysis_id=analysis.id,
        prompt_version="v1.0.0",
        tailored_summary="Distinguished Architect with 15+ years scaling distributed financial networks.",
        highlighted_skills=["Distributed Systems", "Python"],
        cover_letter="Dear Stripe Hiring Team,\n\nI am applying for the Distinguished Systems Architect role.",
        compiled_markdown="# Sam Altman\n\nDistinguished Architect...",
        validation_status="valid",
        status="ready_for_review",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    # 2. Test POST /api/v1/applications
    create_res = client.post(
        "/api/v1/applications",
        json={
            "job_id": job.id,
            "tailored_resume_id": resume.id,
            "portal_type": "lever",
            "answers_payload": {"authorized_in_us": True},
            "submission_notes": "Applied via referral queue.",
        },
    )
    assert create_res.status_code == 201
    app_data = create_res.json()
    app_id = app_data["id"]
    assert app_data["job_id"] == job.id
    assert app_data["tailored_resume_id"] == resume.id
    assert app_data["status"] == "ready_for_review"
    assert app_data["portal_type"] == "lever"

    # 3. Test GET /api/v1/applications
    list_res = client.get("/api/v1/applications?status=ready_for_review")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(item["id"] == app_id for item in list_data["items"])
    item = next(i for i in list_data["items"] if i["id"] == app_id)
    assert item["job_title"] == "Distinguished Systems Architect"
    assert item["job_company"] == "Stripe"
    assert item["fit_score"] == 98.0

    # 4. Test GET /api/v1/applications/{id}
    get_res = client.get(f"/api/v1/applications/{app_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == app_id

    # 5. Test GET /api/v1/applications/{id}/dossier
    dossier_res = client.get(f"/api/v1/applications/{app_id}/dossier")
    assert dossier_res.status_code == 200
    dossier = dossier_res.json()
    assert dossier["application"]["id"] == app_id
    assert dossier["job"]["company"] == "Stripe"
    assert dossier["tailored_resume"]["id"] == resume.id
    assert dossier["analysis"]["fit_score"] == 98.0
    assert dossier["candidate"]["full_name"] == "Sam Altman"

    # 6. Test PUT /api/v1/applications/{id}
    update_res = client.put(
        f"/api/v1/applications/{app_id}",
        json={"reviewer_notes": "Approved for staging review.", "status": "in_review"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "in_review"
    assert update_res.json()["reviewer_notes"] == "Approved for staging review."

    # 7. Test POST /api/v1/applications/{id}/reviews
    review_res = client.post(
        f"/api/v1/applications/{app_id}/reviews",
        json={"reviewer_notes": "Reviewed dossier; verified facts and cover letter.", "decision": "approved"},
    )
    assert review_res.status_code == 200
    assert review_res.json()["decision"] == "approved"
    assert "Reviewed dossier" in review_res.json()["reviewer_notes"]

    # 8. Test GET /api/v1/applications/stats/summary
    stats_res = client.get("/api/v1/applications/stats/summary")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_applications"] >= 1
    assert "lever" in stats["portal_counts"]

    # 9. Test DELETE /api/v1/applications/{id}
    del_res = client.delete(f"/api/v1/applications/{app_id}")
    assert del_res.status_code == 204

    # Verify 404
    get_after_del = client.get(f"/api/v1/applications/{app_id}")
    assert get_after_del.status_code == 404
