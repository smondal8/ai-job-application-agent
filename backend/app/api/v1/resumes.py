from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.errors import NotFoundError
from app.models.resume import Resume
from app.schemas.resume import ResumeCreate, ResumeResponse, ResumeListResponse

router = APIRouter(prefix="/resumes", tags=["Resumes (Phase 4 Foundation)"])


@router.get("", response_model=ResumeListResponse, summary="List Stored Resumes")
def list_resumes(db: Session = Depends(get_db)) -> ResumeListResponse:
    items = db.query(Resume).order_by(desc(Resume.created_at)).all()
    return ResumeListResponse(
        items=[ResumeResponse.model_validate(item) for item in items],
        total=len(items),
    )


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED, summary="Create Resume Entry")
def create_resume(resume_in: ResumeCreate, db: Session = Depends(get_db)) -> ResumeResponse:
    resume = Resume(**resume_in.model_dump())
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return ResumeResponse.model_validate(resume)


@router.get("/{resume_id}", response_model=ResumeResponse, summary="Get Resume Details")
def get_resume(resume_id: int, db: Session = Depends(get_db)) -> ResumeResponse:
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise NotFoundError(f"Resume with id {resume_id} was not found", details={"resume_id": resume_id})
    return ResumeResponse.model_validate(resume)
