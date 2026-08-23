from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import NotFoundError
from app.models.resume import TailoredResume
from app.schemas.tailoring import (
    ResumeTailoringRequest,
    TailoredResumeApprovalRequest,
    TailoredResumeResponse,
    TailoredResumeListResponse,
)
from app.services.tailoring import resume_tailoring_service

router = APIRouter(tags=["Grounded Resume Tailoring & Document Compilation"])


@router.post("/jobs/{job_id}/tailor", response_model=TailoredResumeResponse, status_code=200)
@router.post("/jobs/{job_id}/tailor-resume", response_model=TailoredResumeResponse, status_code=200)
async def tailor_application_materials(
    job_id: int,
    payload: Optional[ResumeTailoringRequest] = None,
    db: Session = Depends(get_db),
):
    """Generate tailored resume and cover letter strictly grounded in verified candidate facts with atomic traceability."""
    candidate_profile_id = payload.candidate_profile_id if payload else None
    tone = payload.tone if payload else "professional"
    target_role_title = payload.target_role_title if payload else None
    custom_instructions = payload.custom_instructions if payload else None
    auto_regenerate = payload.auto_regenerate_on_untraced if payload else True

    tailored = await resume_tailoring_service.tailor_application_materials(
        db=db,
        job_id=job_id,
        candidate_profile_id=candidate_profile_id,
        tone=tone,
        target_role_title=target_role_title,
        custom_instructions=custom_instructions,
        auto_regenerate_on_untraced=auto_regenerate,
    )
    return tailored


@router.get("/jobs/{job_id}/tailored-resume", response_model=TailoredResumeResponse)
def get_job_tailored_resume(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve latest tailored application materials for a job listing."""
    tailored = resume_tailoring_service.get_tailored_resume(db=db, job_id=job_id)
    if not tailored:
        raise NotFoundError(f"No tailored resume found for job ID {job_id}. Generate one first.")
    return tailored


@router.get("/tailored-resumes", response_model=TailoredResumeListResponse)
def list_tailored_resumes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="draft, ready_for_review, approved, rejected"),
    validation_status: Optional[str] = Query(None, description="valid, requires_human_review, rejected"),
    db: Session = Depends(get_db),
):
    """List all tailored resume variants with pagination and validation filters."""
    items = resume_tailoring_service.list_tailored_resumes(
        db=db,
        page=page,
        page_size=page_size,
        status=status,
        validation_status=validation_status,
    )
    total = db.query(TailoredResume).count()
    return TailoredResumeListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/tailored-resumes/{id}", response_model=TailoredResumeResponse)
def get_tailored_resume_by_id(
    id: int,
    db: Session = Depends(get_db),
):
    """Retrieve specific tailored resume by ID with full fact traceability metadata."""
    record = db.query(TailoredResume).filter(TailoredResume.id == id).first()
    if not record:
        raise NotFoundError(f"Tailored resume with ID {id} not found.")
    return record


@router.post("/tailored-resumes/{id}/approve", response_model=TailoredResumeResponse)
def approve_tailored_resume(
    id: int,
    payload: Optional[TailoredResumeApprovalRequest] = None,
    db: Session = Depends(get_db),
):
    """Mark tailored resume approved by human reviewer for downstream portal submission."""
    notes = payload.approver_notes if payload else None
    return resume_tailoring_service.approve_tailored_resume(
        db=db,
        tailored_id=id,
        approver_notes=notes,
    )


@router.get("/tailored-resumes/{id}/download")
def download_tailored_document(
    id: int,
    format: str = Query("markdown", description="markdown, text, html, cover_letter"),
    db: Session = Depends(get_db),
):
    """Download deterministically compiled resume or cover letter document."""
    record = db.query(TailoredResume).filter(TailoredResume.id == id).first()
    if not record:
        raise NotFoundError(f"Tailored resume with ID {id} not found.")

    if format == "html":
        content = record.compiled_html or ""
        media_type = "text/html"
        filename = f"resume_job_{record.job_id}.html"
    elif format == "text":
        content = record.compiled_text or ""
        media_type = "text/plain"
        filename = f"resume_job_{record.job_id}.txt"
    elif format == "cover_letter":
        content = record.cover_letter or ""
        media_type = "text/plain"
        filename = f"cover_letter_job_{record.job_id}.txt"
    else:  # markdown default
        content = record.compiled_markdown or record.markdown_content or ""
        media_type = "text/markdown"
        filename = f"resume_job_{record.job_id}.md"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
