from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationLinkResumeRequest,
    ApplicationReviewCreate,
    ApplicationApprovalRequest,
    ApplicationApprovalResponse,
    ApprovalVerificationResponse,
    PreparationAuthorizationResponse,
    ApplicationResponse,
    ApplicationListResponse,
    ApplicationReviewResponse,
    ApplicationDossierResponse,
    ApplicationStatsResponse,
)
from app.services.application_service import application_service
from app.services.approval import approval_service

router = APIRouter(prefix="/applications", tags=["Application Dashboard & Human Approval Security (Phases 7 & 8)"])


@router.get("", response_model=ApplicationListResponse, summary="List Applications with Filters")
def list_applications(
    status: Optional[str] = Query(None, description="Filter by status (draft, ready_for_review, approved, etc.)"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    portal_type: Optional[str] = Query(None, description="Filter by portal type (greenhouse, lever, etc.)"),
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    search: Optional[str] = Query(None, description="Search term for job title, company, or notes"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> ApplicationListResponse:
    """Retrieve filtered, paginated list of job applications with enriched job and match summary metadata."""
    items, total = application_service.list_applications(
        db=db,
        status=status,
        company=company,
        portal_type=portal_type,
        job_id=job_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    return ApplicationListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED, summary="Create Application")
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    """Create a new Application linked to a single job and selected resume version when available."""
    application = application_service.create_application(
        db=db,
        job_id=payload.job_id,
        tailored_resume_id=payload.tailored_resume_id,
        candidate_profile_id=payload.candidate_profile_id,
        status=payload.status,
        portal_type=payload.portal_type,
        portal_url=payload.portal_url,
        cover_letter=payload.cover_letter,
        answers_payload=payload.answers_payload,
        submission_notes=payload.submission_notes,
    )
    return ApplicationResponse.model_validate(application)


@router.get("/stats/summary", response_model=ApplicationStatsResponse, summary="Get Application Dashboard Stats")
def get_application_stats(db: Session = Depends(get_db)) -> ApplicationStatsResponse:
    """Retrieve summary counts of applications grouped by status and portal type."""
    stats = application_service.get_summary_stats(db)
    return ApplicationStatsResponse(**stats)


@router.get("/{application_id}", response_model=ApplicationResponse, summary="Get Application Details")
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    """Retrieve basic details of a single application."""
    application = application_service.get_application(db, application_id)
    return ApplicationResponse.model_validate(application)


@router.get("/{application_id}/dossier", response_model=ApplicationDossierResponse, summary="Get Complete Application Dossier")
def get_application_dossier(
    application_id: int,
    db: Session = Depends(get_db),
) -> ApplicationDossierResponse:
    """Retrieve comprehensive application dossier including Job, Tailored Resume, Job Analysis, Candidate, and Approval info."""
    dossier = application_service.get_application_dossier(db, application_id)
    return ApplicationDossierResponse(**dossier)


@router.put("/{application_id}", response_model=ApplicationResponse, summary="Update Application Details")
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    """Update application properties, screening answers, portal information, or status notes."""
    updated = application_service.update_application(
        db=db,
        application_id=application_id,
        payload_dict=payload.model_dump(exclude_unset=True),
    )
    return ApplicationResponse.model_validate(updated)


@router.post("/{application_id}/link-resume", response_model=ApplicationResponse, summary="Link Tailored Resume")
def link_tailored_resume(
    application_id: int,
    payload: ApplicationLinkResumeRequest,
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    """Link or switch the tailored resume version assigned to this application."""
    updated = application_service.link_tailored_resume(
        db=db,
        application_id=application_id,
        tailored_resume_id=payload.tailored_resume_id,
    )
    return ApplicationResponse.model_validate(updated)


@router.post("/{application_id}/reviews", response_model=ApplicationReviewResponse, summary="Add Application Review Note")
def add_application_review(
    application_id: int,
    payload: ApplicationReviewCreate,
    db: Session = Depends(get_db),
) -> ApplicationReviewResponse:
    """Record a human review note or decision for an application in the review ledger."""
    review = application_service.add_review(
        db=db,
        application_id=application_id,
        reviewer_notes=payload.reviewer_notes,
        decision=payload.decision,
        manual_edits=payload.manual_edits,
    )
    return ApplicationReviewResponse(
        id=review.id,
        decision=review.decision,
        reviewer_notes=review.reviewer_notes,
        manual_edits=review.manual_edits,
        reviewed_at=review.reviewed_at.isoformat() if review.reviewed_at else None,
        created_at=review.created_at.isoformat() if review.created_at else None,
    )


# --- Phase 8: Human Approval Security & Authorization Boundary Endpoints ---

@router.post("/{application_id}/approve", response_model=ApplicationApprovalResponse, summary="Grant Human Approval (Security Gate)")
def approve_application(
    application_id: int,
    payload: ApplicationApprovalRequest = ApplicationApprovalRequest(),
    db: Session = Depends(get_db),
) -> ApplicationApprovalResponse:
    """Grant cryptographically signed human approval bound to exact job, candidate, resume, and screening hashes."""
    approval = approval_service.grant_approval(
        db=db,
        application_id=application_id,
        approver_notes=payload.approver_notes,
        approver_id=payload.approver_id,
    )
    return ApplicationApprovalResponse.model_validate(approval)


@router.get("/{application_id}/verify-approval", response_model=ApprovalVerificationResponse, summary="Verify Approval Integrity")
def verify_application_approval(
    application_id: int,
    db: Session = Depends(get_db),
) -> ApprovalVerificationResponse:
    """Verify live approval status against current material hashes; invalidates approval if any material input changed."""
    res = approval_service.verify_approval(db=db, application_id=application_id)
    return ApprovalVerificationResponse(**res)


@router.post("/{application_id}/revoke-approval", response_model=ApplicationApprovalResponse, summary="Revoke Human Approval")
def revoke_application_approval(
    application_id: int,
    reason: Optional[str] = Query("Revoked by user", description="Reason for revoking approval"),
    db: Session = Depends(get_db),
) -> ApplicationApprovalResponse:
    """Explicitly revoke human approval certificate for an application."""
    approval = approval_service.revoke_approval(db=db, application_id=application_id, reason=reason)
    return ApplicationApprovalResponse.model_validate(approval)


@router.post("/{application_id}/reject", response_model=ApplicationResponse, summary="Reject Application")
def reject_application(
    application_id: int,
    reason: Optional[str] = Query(None, description="Reason for rejection"),
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    """Reject application and invalidate active approvals."""
    rejected_app = approval_service.reject_application(db=db, application_id=application_id, reason=reason)
    return ApplicationResponse.model_validate(rejected_app)


@router.post("/{application_id}/authorize-preparation", response_model=PreparationAuthorizationResponse, summary="Authorize Browser Preparation (Security Gate)")
def authorize_preparation(
    application_id: int,
    db: Session = Depends(get_db),
) -> PreparationAuthorizationResponse:
    """Strict server-side authorization check before browser preparation. Raises 403 Forbidden if unapproved or invalidated."""
    res = approval_service.authorize_for_preparation(db=db, application_id=application_id)
    return PreparationAuthorizationResponse(**res)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Application")
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
):
    """Delete an application record."""
    application_service.delete_application(db, application_id)
    return None
