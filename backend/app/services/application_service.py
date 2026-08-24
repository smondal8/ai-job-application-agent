from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.core.errors import NotFoundError, BadRequestError
from app.core.logging import get_logger
from app.models.application import Application
from app.models.approval import ApplicationReview
from app.models.job import Job
from app.models.resume import TailoredResume
from app.models.analysis import JobAnalysis
from app.models.candidate import CandidateProfile
from app.models.audit import AuditLog

logger = get_logger("app.services.application_service")


class ApplicationService:
    """Central Application Management and Dossier Review Subsystem (Phase 7)."""

    def create_application(
        self,
        db: Session,
        job_id: int,
        tailored_resume_id: Optional[int] = None,
        candidate_profile_id: Optional[int] = None,
        portal_type: str = "generic",
        portal_url: Optional[str] = None,
        cover_letter: Optional[str] = None,
        answers_payload: Optional[Dict[str, Any]] = None,
        submission_notes: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Application:
        """Create a new job application entity linked to a single job and selected resume version."""
        # 1. Verify Job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise NotFoundError(f"Job with ID {job_id} not found.")

        # 2. Resolve Tailored Resume if not explicitly passed
        resume: Optional[TailoredResume] = None
        if tailored_resume_id:
            resume = db.query(TailoredResume).filter(TailoredResume.id == tailored_resume_id).first()
            if not resume:
                raise NotFoundError(f"Tailored resume with ID {tailored_resume_id} not found.")
        else:
            # Auto-link latest tailored resume for this job if available
            resume = (
                db.query(TailoredResume)
                .filter(TailoredResume.job_id == job_id)
                .order_by(TailoredResume.updated_at.desc())
                .first()
            )

        # 3. Resolve Candidate Profile
        profile: Optional[CandidateProfile] = None
        if candidate_profile_id:
            profile = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_profile_id).first()
        elif resume and resume.candidate_profile_id:
            profile = db.query(CandidateProfile).filter(CandidateProfile.id == resume.candidate_profile_id).first()
        else:
            profile = db.query(CandidateProfile).order_by(CandidateProfile.id.asc()).first()

        # 4. Determine initial status
        initial_status = status or ("ready_for_review" if resume is not None else "draft")
        initial_cover_letter = cover_letter or (resume.cover_letter if resume else None)

        application = Application(
            job_id=job.id,
            tailored_resume_id=resume.id if resume else None,
            candidate_profile_id=profile.id if profile else None,
            status=initial_status,
            portal_type=portal_type or "generic",
            portal_url=portal_url or job.url,
            cover_letter=initial_cover_letter,
            answers_payload=answers_payload or {},
            submission_notes=submission_notes,
        )
        db.add(application)
        db.commit()
        db.refresh(application)

        # Audit log entry
        audit = AuditLog(
            application_id=application.id,
            stage="application_dashboard",
            action="APPLICATION_CREATED",
            message=f"Created application ID {application.id} for job '{job.title}' at '{job.company}' (Status: {application.status}).",
            payload={
                "application_id": application.id,
                "job_id": job.id,
                "tailored_resume_id": resume.id if resume else None,
                "candidate_profile_id": profile.id if profile else None,
                "status": application.status,
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(application)

        return application

    def get_application(self, db: Session, application_id: int) -> Application:
        """Retrieve single Application by ID."""
        app_entity = db.query(Application).filter(Application.id == application_id).first()
        if not app_entity:
            raise NotFoundError(f"Application with ID {application_id} not found.")
        return app_entity

    def get_application_dossier(self, db: Session, application_id: int) -> Dict[str, Any]:
        """Aggregate comprehensive Application Dossier: Job + Tailored Resume + Analysis + Candidate + Review history."""
        app_entity = self.get_application(db, application_id)
        job = db.query(Job).filter(Job.id == app_entity.job_id).first()
        if not job:
            raise NotFoundError(f"Job linked to application {application_id} not found.")

        # Resolve Tailored Resume
        tailored_resume = None
        if app_entity.tailored_resume_id:
            tailored_resume = db.query(TailoredResume).filter(TailoredResume.id == app_entity.tailored_resume_id).first()
        elif job:
            tailored_resume = db.query(TailoredResume).filter(TailoredResume.job_id == job.id).order_by(TailoredResume.updated_at.desc()).first()

        # Resolve Available Resume Variants for this Job
        available_resumes = []
        if job:
            all_resumes = db.query(TailoredResume).filter(TailoredResume.job_id == job.id).order_by(TailoredResume.updated_at.desc()).all()
            for r in all_resumes:
                available_resumes.append({
                    "id": r.id,
                    "prompt_version": r.prompt_version,
                    "validation_status": r.validation_status,
                    "model_used": r.model_used,
                    "status": r.status,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                })

        # Resolve Job Analysis
        analysis = None
        if job:
            analysis = db.query(JobAnalysis).filter(JobAnalysis.job_id == job.id).order_by(JobAnalysis.updated_at.desc()).first()

        # Resolve Candidate Profile
        profile = None
        if app_entity.candidate_profile_id:
            profile = db.query(CandidateProfile).filter(CandidateProfile.id == app_entity.candidate_profile_id).first()
        elif tailored_resume and tailored_resume.candidate_profile_id:
            profile = db.query(CandidateProfile).filter(CandidateProfile.id == tailored_resume.candidate_profile_id).first()
        else:
            profile = db.query(CandidateProfile).order_by(CandidateProfile.id.asc()).first()

        # Reviews
        reviews = (
            db.query(ApplicationReview)
            .filter(ApplicationReview.application_id == application_id)
            .order_by(desc(ApplicationReview.created_at))
            .all()
        )

        return {
            "application": {
                "id": app_entity.id,
                "job_id": app_entity.job_id,
                "tailored_resume_id": app_entity.tailored_resume_id,
                "candidate_profile_id": app_entity.candidate_profile_id,
                "status": app_entity.status,
                "portal_type": app_entity.portal_type,
                "portal_url": app_entity.portal_url,
                "cover_letter": app_entity.cover_letter,
                "answers_payload": app_entity.answers_payload or {},
                "submission_notes": app_entity.submission_notes,
                "reviewer_notes": app_entity.reviewer_notes,
                "error_message": app_entity.error_message,
                "applied_at": app_entity.applied_at.isoformat() if app_entity.applied_at else None,
                "submitted_at": app_entity.submitted_at.isoformat() if app_entity.submitted_at else None,
                "created_at": app_entity.created_at.isoformat() if app_entity.created_at else None,
                "updated_at": app_entity.updated_at.isoformat() if app_entity.updated_at else None,
            },
            "job": {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "remote_type": job.remote_type,
                "department": job.department,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "currency": job.currency,
                "url": job.url,
                "source": job.source,
                "description_raw": job.description_raw,
                "description_clean": job.description_clean,
                "skills_raw": job.skills_raw or [],
                "status": job.status,
            },
            "tailored_resume": {
                "id": tailored_resume.id,
                "job_id": tailored_resume.job_id,
                "prompt_version": tailored_resume.prompt_version,
                "model_used": tailored_resume.model_used,
                "tailored_summary": tailored_resume.tailored_summary,
                "tailored_experience": tailored_resume.tailored_experience,
                "highlighted_skills": tailored_resume.highlighted_skills,
                "cover_letter": tailored_resume.cover_letter,
                "compiled_markdown": tailored_resume.compiled_markdown or tailored_resume.markdown_content,
                "compiled_text": tailored_resume.compiled_text,
                "compiled_html": tailored_resume.compiled_html,
                "traceability_matrix": tailored_resume.traceability_matrix,
                "validation_status": tailored_resume.validation_status,
                "validation_details": tailored_resume.validation_details,
                "status": tailored_resume.status,
            } if tailored_resume else None,
            "available_resumes": available_resumes,
            "analysis": {
                "id": analysis.id,
                "fit_score": analysis.fit_score,
                "deterministic_score": analysis.deterministic_score,
                "semantic_score": analysis.semantic_score,
                "fit_level": analysis.fit_level,
                "recommendation": analysis.recommendation,
                "summary": analysis.summary,
                "role_summary": analysis.role_summary,
                "key_responsibilities": analysis.key_responsibilities,
                "matched_skills": analysis.matched_skills,
                "missing_skills": analysis.missing_skills,
                "keywords": analysis.keywords,
                "red_flags": analysis.red_flags,
            } if analysis else None,
            "candidate": {
                "id": profile.id,
                "full_name": profile.full_name,
                "email": profile.email,
                "phone": profile.phone,
                "location": profile.location,
                "headline": profile.headline,
                "is_verified": profile.is_verified,
            } if profile else None,
            "reviews": [
                {
                    "id": rev.id,
                    "decision": rev.decision,
                    "reviewer_notes": rev.reviewer_notes,
                    "manual_edits": rev.manual_edits,
                    "reviewed_at": rev.reviewed_at.isoformat() if rev.reviewed_at else None,
                    "created_at": rev.created_at.isoformat() if rev.created_at else None,
                }
                for rev in reviews
            ],
        }

    def list_applications(
        self,
        db: Session,
        status: Optional[str] = None,
        company: Optional[str] = None,
        portal_type: Optional[str] = None,
        job_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List applications with pagination, search, and status filtering."""
        query = db.query(Application).join(Job, Application.job_id == Job.id)

        if status and status != "all":
            query = query.filter(Application.status == status)
        if company and company != "all":
            query = query.filter(Job.company.ilike(f"%{company}%"))
        if portal_type and portal_type != "all":
            query = query.filter(Application.portal_type == portal_type)
        if job_id:
            query = query.filter(Application.job_id == job_id)
        if search:
            query = query.filter(
                (Job.title.ilike(f"%{search}%"))
                | (Job.company.ilike(f"%{search}%"))
                | (Application.submission_notes.ilike(f"%{search}%"))
            )

        total = query.count()
        apps = query.order_by(desc(Application.created_at)).offset((page - 1) * page_size).limit(page_size).all()

        results = []
        for app in apps:
            job = app.job
            tailored = app.tailored_resume
            analysis = None
            if job:
                analysis = db.query(JobAnalysis).filter(JobAnalysis.job_id == job.id).order_by(JobAnalysis.updated_at.desc()).first()

            results.append({
                "id": app.id,
                "job_id": app.job_id,
                "tailored_resume_id": app.tailored_resume_id,
                "candidate_profile_id": app.candidate_profile_id,
                "status": app.status,
                "portal_type": app.portal_type,
                "portal_url": app.portal_url,
                "cover_letter": app.cover_letter,
                "answers_payload": app.answers_payload or {},
                "submission_notes": app.submission_notes,
                "reviewer_notes": app.reviewer_notes,
                "error_message": app.error_message,
                "applied_at": app.applied_at.isoformat() if app.applied_at else None,
                "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
                "created_at": app.created_at.isoformat() if app.created_at else None,
                "updated_at": app.updated_at.isoformat() if app.updated_at else None,
                # Enriched summaries
                "job_title": job.title if job else "Unknown Role",
                "job_company": job.company if job else "Unknown Company",
                "job_location": job.location if job else "Unspecified",
                "job_remote_type": job.remote_type if job else "unspecified",
                "fit_score": analysis.fit_score if analysis else None,
                "fit_level": analysis.fit_level if analysis else None,
                "recommendation": analysis.recommendation if analysis else None,
                "resume_validation_status": tailored.validation_status if tailored else None,
            })

        return results, total

    def update_application(
        self,
        db: Session,
        application_id: int,
        payload_dict: Dict[str, Any],
    ) -> Application:
        """Update application properties, screening answers, portal information, or status."""
        application = self.get_application(db, application_id)

        for key, val in payload_dict.items():
            if hasattr(application, key) and val is not None:
                setattr(application, key, val)

        db.commit()
        db.refresh(application)

        audit = AuditLog(
            application_id=application.id,
            stage="application_dashboard",
            action="APPLICATION_UPDATED",
            message=f"Updated application ID {application.id} (Status: {application.status}).",
            payload={"application_id": application.id, "updated_fields": list(payload_dict.keys())},
        )
        db.add(audit)
        db.commit()
        db.refresh(application)

        return application

    def link_tailored_resume(
        self,
        db: Session,
        application_id: int,
        tailored_resume_id: int,
    ) -> Application:
        """Link or change the selected tailored resume version for this application."""
        application = self.get_application(db, application_id)
        resume = db.query(TailoredResume).filter(TailoredResume.id == tailored_resume_id).first()
        if not resume:
            raise NotFoundError(f"Tailored resume ID {tailored_resume_id} not found.")

        application.tailored_resume_id = resume.id
        if not application.cover_letter and resume.cover_letter:
            application.cover_letter = resume.cover_letter
        if application.status == "draft":
            application.status = "ready_for_review"

        db.commit()
        db.refresh(application)

        audit = AuditLog(
            application_id=application.id,
            stage="application_dashboard",
            action="RESUME_LINKED_TO_APPLICATION",
            message=f"Linked tailored resume #{resume.id} (Prompt: {resume.prompt_version}) to application #{application.id}.",
            payload={"application_id": application.id, "tailored_resume_id": resume.id},
        )
        db.add(audit)
        db.commit()
        db.refresh(application)

        return application

    def add_review(
        self,
        db: Session,
        application_id: int,
        reviewer_notes: Optional[str] = None,
        decision: str = "pending",
        manual_edits: Optional[Dict[str, Any]] = None,
    ) -> ApplicationReview:
        """Record review notes for this application without triggering state transitions (Phase 8 boundary)."""
        application = self.get_application(db, application_id)

        review = ApplicationReview(
            application_id=application.id,
            decision=decision or "pending",
            reviewer_notes=reviewer_notes,
            manual_edits=manual_edits or {},
            reviewed_at=datetime.now(timezone.utc),
        )
        db.add(review)

        if reviewer_notes:
            application.reviewer_notes = reviewer_notes

        db.commit()
        db.refresh(review)

        audit = AuditLog(
            application_id=application.id,
            stage="application_dashboard",
            action="APPLICATION_REVIEWED",
            message=f"Recorded review for application #{application.id} (Decision: {decision}).",
            payload={"application_id": application.id, "review_id": review.id, "decision": decision},
        )
        db.add(audit)
        db.commit()
        db.refresh(review)

        return review

    def get_summary_stats(self, db: Session) -> Dict[str, Any]:
        """Aggregate executive application counts and status metrics."""
        total = db.query(Application).count()
        by_status = dict(
            db.query(Application.status, func.count(Application.id))
            .group_by(Application.status)
            .all()
        )
        by_portal = dict(
            db.query(Application.portal_type, func.count(Application.id))
            .group_by(Application.portal_type)
            .all()
        )

        return {
            "total_applications": total,
            "status_counts": {
                "draft": by_status.get("draft", 0),
                "ready_for_review": by_status.get("ready_for_review", 0),
                "in_review": by_status.get("in_review", 0),
                "approved_pending_submission": by_status.get("approved_pending_submission", 0),
                "submitted": by_status.get("submitted", 0),
                "rejected": by_status.get("rejected", 0),
                "archived": by_status.get("archived", 0),
            },
            "portal_counts": by_portal,
        }

    def delete_application(self, db: Session, application_id: int) -> bool:
        """Delete an application entity."""
        application = self.get_application(db, application_id)
        db.delete(application)
        db.commit()
        return True


application_service = ApplicationService()
