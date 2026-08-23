from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import NotFoundError
from app.models.resume import TailoredResume
from app.schemas.tailoring import (
    ResumeTailoringRequest,
    TailoredResumeResponse,
    TailoredResumeListResponse,
)
from app.services.resume_tailoring_service import resume_tailoring_service

router = APIRouter(tags=["Resume Tailoring & Cover Letters"])


@router.post("/jobs/{job_id}/tailor", response_model=TailoredResumeResponse, status_code=200)
async def tailor_resume(
    job_id: int,
    payload: Optional[ResumeTailoringRequest] = None,
    db: Session = Depends(get_db),
):
    """Generate tailored resume and personalized cover letter for a job using local Ollama model."""
    candidate_profile_id = payload.candidate_profile_id if payload else None
    tone = payload.tone if payload and payload.tone else "professional"
    target_role_title = payload.target_role_title if payload else None
    custom_instructions = payload.custom_instructions if payload else None

    tailored = await resume_tailoring_service.tailor_application_materials(
        db=db,
        job_id=job_id,
        candidate_profile_id=candidate_profile_id,
        tone=tone,
        target_role_title=target_role_title,
        custom_instructions=custom_instructions,
    )
    return tailored


@router.get("/jobs/{job_id}/tailored-resume", response_model=TailoredResumeResponse)
def get_job_tailored_resume(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve the latest tailored resume and cover letter for a job listing."""
    tailored = resume_tailoring_service.get_tailored_resume(db=db, job_id=job_id)
    if not tailored:
        raise NotFoundError(f"No tailored resume found for job ID {job_id}. Generate one first.")
    return tailored


@router.get("/tailored-resumes", response_model=TailoredResumeListResponse)
def list_tailored_resumes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all generated tailored resumes with pagination."""
    items = resume_tailoring_service.list_tailored_resumes(db=db, page=page, page_size=page_size)
    total = db.query(TailoredResume).count()
    return TailoredResumeListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/tailored-resumes/{id}", response_model=TailoredResumeResponse)
def get_tailored_resume_by_id(
    id: int,
    db: Session = Depends(get_db),
):
    """Retrieve specific tailored resume by ID."""
    tailored = db.query(TailoredResume).filter(TailoredResume.id == id).first()
    if not tailored:
        raise NotFoundError(f"Tailored resume with ID {id} not found.")
    return tailored
