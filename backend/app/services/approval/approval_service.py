from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, BadRequestError, ForbiddenError
from app.core.logging import get_logger
from app.models.application import Application
from app.models.approval import ApplicationApproval
from app.models.job import Job
from app.models.candidate import CandidateProfile
from app.models.resume import TailoredResume
from app.models.audit import AuditLog
from app.services.approval.hasher import (
    compute_job_hash,
    compute_candidate_hash,
    compute_resume_hash,
    compute_answers_hash,
    generate_approval_token,
)
from app.services.approval.state_machine import (
    ApplicationStatus,
    transition_application,
)

logger = get_logger("app.services.approval")


class ApprovalService:
    """Server-side Human Approval & Cryptographic Security Authorization Gate (Phase 8)."""

    def grant_approval(
        self,
        db: Session,
        application_id: int,
        approver_notes: Optional[str] = None,
        approver_id: str = "human_reviewer",
    ) -> ApplicationApproval:
        """Grant cryptographically signed human approval bound to exact job, profile, resume, and screening hashes."""
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise NotFoundError(f"Application #{application_id} not found.")

        job = db.query(Job).filter(Job.id == application.job_id).first()
        if not job:
            raise NotFoundError(f"Job #{application.job_id} linked to application #{application_id} not found.")

        # Candidate profile resolution & validation
        profile = None
        if application.candidate_profile_id:
            profile = db.query(CandidateProfile).filter(CandidateProfile.id == application.candidate_profile_id).first()
        if not profile:
            profile = db.query(CandidateProfile).order_by(CandidateProfile.id.asc()).first()
            if profile:
                application.candidate_profile_id = profile.id

        if not profile or not profile.is_verified:
            raise BadRequestError(
                "Cannot approve application: Candidate profile must be verified before human approval can be granted.",
                details={"candidate_profile_id": profile.id if profile else None, "is_verified": profile.is_verified if profile else False},
            )

        # Tailored resume resolution & validation
        resume = None
        if application.tailored_resume_id:
            resume = db.query(TailoredResume).filter(TailoredResume.id == application.tailored_resume_id).first()
        if not resume:
            resume = (
                db.query(TailoredResume)
                .filter(TailoredResume.job_id == job.id)
                .order_by(TailoredResume.updated_at.desc())
                .first()
            )
            if resume:
                application.tailored_resume_id = resume.id

        if not resume:
            raise BadRequestError(
                "Cannot approve application: No tailored resume is linked. Tailor a resume first in Phase 6 Studio.",
                details={"application_id": application_id, "job_id": job.id},
            )

        if resume.validation_status not in ("valid", "approved") and resume.status != "approved":
            raise BadRequestError(
                f"Cannot approve application: Linked tailored resume #{resume.id} has unverified or invalid claims (Validation Status: {resume.validation_status}).",
                details={"resume_id": resume.id, "validation_status": resume.validation_status},
            )

        # Invalidate any prior active approvals for this application
        prior_approvals = (
            db.query(ApplicationApproval)
            .filter(ApplicationApproval.application_id == application_id, ApplicationApproval.is_valid == True)
            .all()
        )
        for pa in prior_approvals:
            pa.is_valid = False
            pa.invalidation_reason = "Superseded by newly granted approval."
            pa.invalidated_at = datetime.now(timezone.utc)

        # Compute Material Input Hashes
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        job_hash = compute_job_hash(job)
        cand_hash = compute_candidate_hash(profile)
        res_hash = compute_resume_hash(resume)
        ans_hash = compute_answers_hash(application.answers_payload)

        approval_token = generate_approval_token(
            application_id=application.id,
            job_hash=job_hash,
            candidate_hash=cand_hash,
            resume_hash=res_hash,
            answers_hash=ans_hash,
            approved_at_iso=now_iso,
        )

        # Transition Application State Machine
        transition_application(application, ApplicationStatus.APPROVED.value)
        application.approval_token = approval_token
        application.approved_at = now
        application.invalidation_reason = None
        if approver_notes:
            application.reviewer_notes = approver_notes

        approval = ApplicationApproval(
            application_id=application.id,
            status="approved",
            job_id=job.id,
            approved_job_hash=job_hash,
            candidate_profile_id=profile.id,
            approved_candidate_hash=cand_hash,
            tailored_resume_id=resume.id,
            approved_resume_hash=res_hash,
            approved_answers_hash=ans_hash,
            approval_token=approval_token,
            approver_id=approver_id,
            approver_notes=approver_notes,
            is_valid=True,
            approved_at=now,
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)
        db.refresh(application)

        # Audit Log
        audit = AuditLog(
            application_id=application.id,
            stage="approval_and_submission",
            action="APPLICATION_HUMAN_APPROVED",
            message=f"Human approval granted for Application #{application.id}. Token: {approval_token}",
            payload={
                "application_id": application.id,
                "approval_id": approval.id,
                "approval_token": approval_token,
                "approved_job_hash": job_hash,
                "approved_candidate_hash": cand_hash,
                "approved_resume_hash": res_hash,
                "approved_answers_hash": ans_hash,
            },
        )
        db.add(audit)
        db.commit()

        logger.info(f"Granted human approval for Application #{application.id} (Token: {approval_token})")
        return approval

    def verify_approval(self, db: Session, application_id: int) -> Dict[str, Any]:
        """Verify that application approval exists and that none of the material inputs have changed."""
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise NotFoundError(f"Application #{application_id} not found.")

        # Find latest approval
        approval = (
            db.query(ApplicationApproval)
            .filter(ApplicationApproval.application_id == application_id)
            .order_by(ApplicationApproval.created_at.desc())
            .first()
        )

        if not approval or not approval.is_valid:
            return {
                "is_valid": False,
                "is_approved": False,
                "reason": "No active human approval certificate found for this application.",
                "application_id": application_id,
                "current_status": application.status,
                "mismatches": [],
            }

        # Resolve live entities
        job = db.query(Job).filter(Job.id == application.job_id).first()
        profile = db.query(CandidateProfile).filter(CandidateProfile.id == application.candidate_profile_id).first() if application.candidate_profile_id else None
        if not profile:
            profile = db.query(CandidateProfile).order_by(CandidateProfile.id.asc()).first()
        resume = db.query(TailoredResume).filter(TailoredResume.id == application.tailored_resume_id).first() if application.tailored_resume_id else None

        # Compute Live Hashes
        live_job_hash = compute_job_hash(job)
        live_cand_hash = compute_candidate_hash(profile)
        live_res_hash = compute_resume_hash(resume)
        live_ans_hash = compute_answers_hash(application.answers_payload)

        mismatches = []
        if live_job_hash != approval.approved_job_hash:
            mismatches.append("Job description, title, or workplace parameters modified after approval.")
        if live_cand_hash != approval.approved_candidate_hash:
            mismatches.append("Candidate profile facts (experience, skills, education) modified after approval.")
        if live_res_hash != approval.approved_resume_hash:
            mismatches.append("Tailored resume content, cover letter, or fact traceability modified after approval.")
        if live_ans_hash != approval.approved_answers_hash:
            mismatches.append("Screening questions answers payload modified after approval.")

        if mismatches:
            invalidation_reason = f"Approval invalidated due to material changes: {'; '.join(mismatches)}"
            approval.is_valid = False
            approval.status = "invalidated"
            approval.invalidation_reason = invalidation_reason
            approval.invalidated_at = datetime.now(timezone.utc)

            # Transition state machine to requires_reapproval
            try:
                transition_application(application, ApplicationStatus.REQUIRES_REAPPROVAL.value, reason=invalidation_reason)
            except BadRequestError:
                application.status = ApplicationStatus.REQUIRES_REAPPROVAL.value
                application.invalidation_reason = invalidation_reason

            application.approval_token = None

            audit = AuditLog(
                application_id=application.id,
                stage="approval_and_submission",
                action="APPROVAL_INVALIDATED",
                message=f"Approval invalidated for Application #{application.id}. Reason: {invalidation_reason}",
                payload={"application_id": application.id, "mismatches": mismatches},
            )
            db.add(audit)
            db.commit()
            db.refresh(application)

            logger.warning(f"Invalidated approval for Application #{application.id}: {invalidation_reason}")

            return {
                "is_valid": False,
                "is_approved": False,
                "reason": invalidation_reason,
                "application_id": application_id,
                "current_status": application.status,
                "mismatches": mismatches,
            }

        return {
            "is_valid": True,
            "is_approved": True,
            "application_id": application_id,
            "current_status": application.status,
            "approval_token": approval.approval_token,
            "approved_at": approval.approved_at.isoformat() if approval.approved_at else None,
            "approved_by": approval.approver_id,
            "hashes": {
                "job_hash": live_job_hash,
                "candidate_hash": live_cand_hash,
                "resume_hash": live_res_hash,
                "answers_hash": live_ans_hash,
            },
            "mismatches": [],
        }

    def revoke_approval(
        self,
        db: Session,
        application_id: int,
        reason: str = "Revoked by human reviewer",
    ) -> ApplicationApproval:
        """Explicitly revoke human approval certificate."""
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise NotFoundError(f"Application #{application_id} not found.")

        approval = (
            db.query(ApplicationApproval)
            .filter(ApplicationApproval.application_id == application_id, ApplicationApproval.is_valid == True)
            .order_by(ApplicationApproval.created_at.desc())
            .first()
        )

        now = datetime.now(timezone.utc)
        if approval:
            approval.is_valid = False
            approval.status = "revoked"
            approval.invalidation_reason = reason
            approval.invalidated_at = now

        transition_application(application, ApplicationStatus.IN_REVIEW.value, reason=reason)
        application.approval_token = None
        application.invalidation_reason = reason

        audit = AuditLog(
            application_id=application.id,
            stage="approval_and_submission",
            action="APPROVAL_REVOKED",
            message=f"Human approval revoked for Application #{application.id}. Reason: {reason}",
            payload={"application_id": application.id, "reason": reason},
        )
        db.add(audit)
        db.commit()
        db.refresh(application)

        if approval:
            db.refresh(approval)
            return approval

        # Return a synthetic placeholder approval if none was in DB
        return ApplicationApproval(
            application_id=application.id,
            status="revoked",
            job_id=application.job_id,
            approved_job_hash="",
            approved_candidate_hash="",
            approved_resume_hash="",
            approved_answers_hash="",
            approval_token="",
            is_valid=False,
            invalidation_reason=reason,
            approved_at=now,
        )

    def reject_application(
        self,
        db: Session,
        application_id: int,
        reason: Optional[str] = None,
    ) -> Application:
        """Reject application through strict state machine."""
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise NotFoundError(f"Application #{application_id} not found.")

        # Invalidate active approvals
        active_approvals = (
            db.query(ApplicationApproval)
            .filter(ApplicationApproval.application_id == application_id, ApplicationApproval.is_valid == True)
            .all()
        )
        for ap in active_approvals:
            ap.is_valid = False
            ap.status = "rejected"
            ap.invalidation_reason = reason or "Application was rejected."
            ap.invalidated_at = datetime.now(timezone.utc)

        transition_application(application, ApplicationStatus.REJECTED.value, reason=reason)
        application.approval_token = None
        application.invalidation_reason = reason or "Application was rejected."

        audit = AuditLog(
            application_id=application.id,
            stage="approval_and_submission",
            action="APPLICATION_REJECTED",
            message=f"Application #{application.id} marked as REJECTED. Reason: {reason}",
            payload={"application_id": application.id, "reason": reason},
        )
        db.add(audit)
        db.commit()
        db.refresh(application)
        return application

    def authorize_for_preparation(
        self,
        db: Session,
        application_id: int,
    ) -> Dict[str, Any]:
        """Strict server-side authorization gate for browser preparation operations.
        
        Raises ForbiddenError if human approval is missing or invalidated.
        """
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise NotFoundError(f"Application #{application_id} not found.")

        # 1. Strict Security Verification
        verification = self.verify_approval(db, application_id)
        if not verification["is_valid"]:
            logger.error(f"Security authorization failed for Application #{application_id}: {verification['reason']}")
            raise ForbiddenError(
                f"Security Authorization Failed: Application #{application_id} is not authorized for browser preparation. "
                f"Reason: {verification['reason']}",
                details=verification,
            )

        # 2. State Transition to STAGED_FOR_PREPARATION
        if application.status == ApplicationStatus.APPROVED.value:
            transition_application(application, ApplicationStatus.STAGED_FOR_PREPARATION.value)
            db.commit()
            db.refresh(application)

        now = datetime.now(timezone.utc)
        audit = AuditLog(
            application_id=application.id,
            stage="approval_and_submission",
            action="APPLICATION_PREPARATION_AUTHORIZED",
            message=f"Security gate verified. Application #{application.id} authorized and staged for preparation.",
            payload={
                "application_id": application.id,
                "approval_token": verification["approval_token"],
                "authorized_at": now.isoformat(),
            },
        )
        db.add(audit)
        db.commit()

        logger.info(f"Security authorization GRANTED for Application #{application.id} (Token: {verification['approval_token']})")

        return {
            "authorization_granted": True,
            "application_id": application.id,
            "approval_token": verification["approval_token"],
            "status": application.status,
            "authorized_at": now.isoformat(),
            "approved_at": verification.get("approved_at"),
            "approved_by": verification.get("approved_by"),
            "snapshot_hashes": verification.get("hashes"),
        }


approval_service = ApprovalService()
