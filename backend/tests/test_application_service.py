import pytest
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.candidate import CandidateProfile, WorkExperience
from app.models.analysis import JobAnalysis
from app.models.resume import TailoredResume
from app.models.application import Application
from app.models.audit import AuditLog
from app.services.application_service import application_service


@pytest.fixture
def setup_application_data(db_session: Session):
    # 1. Candidate Profile
    profile = CandidateProfile(
        full_name="Taylor Swift",
        email="taylor@example.com",
        location="New York, NY",
        headline="Lead Platform Engineer",
        summary="High-scale distributed infrastructure builder.",
        is_verified=True,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)

    # 2. Job Listing
    job = Job(
        title="Staff Infrastructure Architect",
        company="Spotify",
        location="New York, NY",
        remote_type="hybrid",
        description_raw="Leading global audio streaming infrastructure and playback reliability.",
        source="unit_test",
        url="https://spotify.jobs/staff-infra-123",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    # 3. Job Analysis
    analysis = JobAnalysis(
        job_id=job.id,
        candidate_profile_id=profile.id,
        fit_score=94.5,
        fit_level="high",
        recommendation="strong_apply",
        matched_skills=["Python", "Distributed Systems", "Kubernetes"],
        missing_skills=["Kafka Streams"],
        keywords=["Infrastructure", "Reliability", "Streaming"],
        status="completed",
    )
    db_session.add(analysis)

    # 4. Tailored Resume
    resume = TailoredResume(
        job_id=job.id,
        candidate_profile_id=profile.id,
        job_analysis_id=analysis.id,
        prompt_version="v1.0.0",
        model_used="qwen3:8b",
        tailored_summary="Lead Platform Engineer with proven track record scaling high-throughput streaming systems.",
        tailored_experience=[
            {
                "company": "SoundCloud",
                "position": "Staff Engineer",
                "tailored_highlights": [
                    {"text": "Scaled audio transcoding pipeline to 200k ops/sec.", "source_fact_ids": ["exp:1:h0"]}
                ],
            }
        ],
        highlighted_skills=["Python", "Kubernetes", "Distributed Systems"],
        cover_letter="Dear Spotify Hiring Team,\n\nI am thrilled to apply for the Staff Infrastructure Architect role.",
        compiled_markdown="# Taylor Swift\n\n## Summary\nLead Platform Engineer...",
        compiled_text="TAYLOR SWIFT\nLead Platform Engineer...",
        compiled_html="<h1>Taylor Swift</h1>",
        validation_status="valid",
        validation_details={"traceability_score": 100.0, "total_claims": 2, "verified_claims": 2},
        status="ready_for_review",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    return {
        "profile": profile,
        "job": job,
        "analysis": analysis,
        "resume": resume,
    }


def test_create_application_with_auto_resume_linking(db_session: Session, setup_application_data: dict):
    job = setup_application_data["job"]
    resume = setup_application_data["resume"]
    profile = setup_application_data["profile"]

    app_entity = application_service.create_application(
        db=db_session,
        job_id=job.id,
        portal_type="greenhouse",
        submission_notes="High priority target role.",
    )

    assert app_entity.id is not None
    assert app_entity.job_id == job.id
    assert app_entity.tailored_resume_id == resume.id  # Auto-linked
    assert app_entity.candidate_profile_id == profile.id
    assert app_entity.status == "ready_for_review"
    assert app_entity.portal_type == "greenhouse"
    assert app_entity.portal_url == job.url
    assert "Dear Spotify Hiring Team" in app_entity.cover_letter

    # Verify audit log
    audit = db_session.query(AuditLog).filter(AuditLog.application_id == app_entity.id).first()
    assert audit is not None
    assert audit.action == "APPLICATION_CREATED"


def test_get_application_dossier(db_session: Session, setup_application_data: dict):
    job = setup_application_data["job"]
    resume = setup_application_data["resume"]
    profile = setup_application_data["profile"]
    analysis = setup_application_data["analysis"]

    app_entity = application_service.create_application(
        db=db_session,
        job_id=job.id,
        tailored_resume_id=resume.id,
    )

    # Add a review note
    application_service.add_review(
        db=db_session,
        application_id=app_entity.id,
        reviewer_notes="Resume looks very solid. Cover letter aligns well with audio streaming.",
        decision="pending",
    )

    dossier = application_service.get_application_dossier(db=db_session, application_id=app_entity.id)

    assert dossier["application"]["id"] == app_entity.id
    assert dossier["job"]["title"] == "Staff Infrastructure Architect"
    assert dossier["job"]["company"] == "Spotify"
    assert dossier["tailored_resume"]["id"] == resume.id
    assert dossier["tailored_resume"]["prompt_version"] == "v1.0.0"
    assert dossier["analysis"]["fit_score"] == 94.5
    assert dossier["candidate"]["full_name"] == "Taylor Swift"
    assert len(dossier["reviews"]) == 1
    assert "Cover letter aligns well" in dossier["reviews"][0]["reviewer_notes"]


def test_update_and_link_resume_workflow(db_session: Session, setup_application_data: dict):
    job = setup_application_data["job"]
    profile = setup_application_data["profile"]

    # 1. Create draft application without tailored resume initially
    app_entity = Application(
        job_id=job.id,
        candidate_profile_id=profile.id,
        status="draft",
        portal_type="generic",
    )
    db_session.add(app_entity)
    db_session.commit()
    db_session.refresh(app_entity)

    # 2. Update screening questions answers
    answers = {
        "years_experience": "10+",
        "sponsorship_required": "No",
        "notice_period": "2 weeks",
    }
    updated_app = application_service.update_application(
        db=db_session,
        application_id=app_entity.id,
        payload_dict={"answers_payload": answers, "reviewer_notes": "Awaiting final screening answers."},
    )
    assert updated_app.answers_payload["years_experience"] == "10+"
    assert updated_app.reviewer_notes == "Awaiting final screening answers."

    # 3. Explicitly link tailored resume
    resume = setup_application_data["resume"]
    linked_app = application_service.link_tailored_resume(
        db=db_session,
        application_id=app_entity.id,
        tailored_resume_id=resume.id,
    )
    assert linked_app.tailored_resume_id == resume.id
    assert linked_app.status == "ready_for_review"
    assert "Dear Spotify Hiring Team" in linked_app.cover_letter


def test_list_applications_and_stats(db_session: Session, setup_application_data: dict):
    job = setup_application_data["job"]

    app1 = application_service.create_application(db=db_session, job_id=job.id, status="draft", portal_type="workday")
    app2 = application_service.create_application(db=db_session, job_id=job.id, status="ready_for_review", portal_type="greenhouse")

    # List with filters
    items, total = application_service.list_applications(db=db_session, status="ready_for_review")
    assert total >= 1
    assert all(item["status"] == "ready_for_review" for item in items)

    # Search filter
    search_items, search_total = application_service.list_applications(db=db_session, search="Spotify")
    assert search_total >= 2

    # Stats
    stats = application_service.get_summary_stats(db=db_session)
    assert stats["total_applications"] >= 2
    assert stats["status_counts"]["draft"] >= 1
    assert stats["status_counts"]["ready_for_review"] >= 1
    assert "greenhouse" in stats["portal_counts"]
