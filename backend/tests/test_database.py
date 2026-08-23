from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.analysis import JobAnalysis
from app.models.resume import Resume, TailoredResume
from app.models.application import Application
from app.models.approval import ApplicationReview
from app.models.audit import AuditLog


def test_job_model_crud(db_session: Session):
    job = Job(
        title="AI Engineer",
        company="DeepMind",
        location="London, UK",
        remote_type="hybrid",
        source="manual",
        status="discovered",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    assert job.id is not None
    assert job.title == "AI Engineer"
    assert job.company == "DeepMind"
    assert job.created_at is not None
    assert job.updated_at is not None

    # Query
    fetched = db_session.query(Job).filter(Job.id == job.id).first()
    assert fetched is not None
    assert fetched.title == "AI Engineer"


def test_full_pipeline_entities_relational_integrity(db_session: Session):
    # 1. Create Job
    job = Job(title="Senior ML Engineer", company="Anthropic", status="analyzed")
    db_session.add(job)
    db_session.commit()

    # 2. Create JobAnalysis (Phase 3 entity)
    analysis = JobAnalysis(
        job_id=job.id,
        fit_score=92.5,
        fit_level="high",
        matched_skills=["Python", "PyTorch", "FastAPI"],
        missing_skills=["Kubernetes"],
        status="completed",
    )
    db_session.add(analysis)
    db_session.commit()

    # 3. Create Base Resume & Tailored Resume (Phase 4 entities)
    resume = Resume(
        name="ML Engineer Profile",
        version="1.0",
        skills=["Python", "PyTorch", "SQL"],
        is_default=True,
    )
    db_session.add(resume)
    db_session.commit()

    tailored_resume = TailoredResume(
        job_id=job.id,
        base_resume_id=resume.id,
        tailored_summary="Experienced ML engineer specialized in scalable inference.",
        highlighted_skills=["Python", "PyTorch", "FastAPI"],
    )
    db_session.add(tailored_resume)
    db_session.commit()

    # 4. Create Application (Phase 5 & 6 entity)
    application = Application(
        job_id=job.id,
        tailored_resume_id=tailored_resume.id,
        status="pending_approval",
        portal_type="greenhouse",
    )
    db_session.add(application)
    db_session.commit()

    # 5. Create Review (Phase 5 entity)
    review = ApplicationReview(
        application_id=application.id,
        decision="approved",
        reviewer_notes="Ready for submission.",
    )
    db_session.add(review)
    db_session.commit()

    # 6. Create Audit Log (Cross-cutting entity)
    audit = AuditLog(
        application_id=application.id,
        stage="approval",
        action="HUMAN_APPROVED",
        level="info",
        message="Application approved by human reviewer.",
    )
    db_session.add(audit)
    db_session.commit()

    # Verify query and relationships
    saved_app = db_session.query(Application).filter(Application.id == application.id).first()
    assert saved_app is not None
    assert saved_app.job.title == "Senior ML Engineer"
    assert saved_app.tailored_resume.base_resume.name == "ML Engineer Profile"
    assert len(saved_app.reviews) == 1
    assert saved_app.reviews[0].decision == "approved"
    assert len(saved_app.audit_logs) == 1


def test_cascade_delete_job_deletes_dependents(db_session: Session):
    job = Job(title="Backend Dev", company="Acme Corp")
    db_session.add(job)
    db_session.commit()

    analysis = JobAnalysis(job_id=job.id, fit_score=80.0)
    db_session.add(analysis)
    db_session.commit()

    analysis_id = analysis.id
    db_session.delete(job)
    db_session.commit()

    # Verify analysis is deleted
    orphaned_analysis = db_session.query(JobAnalysis).filter(JobAnalysis.id == analysis_id).first()
    assert orphaned_analysis is None
