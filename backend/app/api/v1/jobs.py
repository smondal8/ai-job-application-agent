from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.core.database import get_db
from app.core.errors import NotFoundError
from app.models.job import Job
from app.schemas.job import JobCreate, JobResponse, JobListResponse

router = APIRouter(prefix="/jobs", tags=["Jobs (Phase 2 Foundation)"])


@router.get("", response_model=JobListResponse, summary="List Job Postings")
def list_jobs(
    status: Optional[str] = Query(None, description="Filter by job status (e.g. discovered, applied)"),
    search: Optional[str] = Query(None, description="Search term across title and company"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> JobListResponse:
    query = db.query(Job)

    if status:
        query = query.filter(Job.status == status)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(Job.title.ilike(search_pattern), Job.company.ilike(search_pattern))
        )

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(desc(Job.created_at)).offset(offset).limit(page_size).all()

    return JobListResponse(
        items=[JobResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or Import Job Posting",
)
def create_job(job_in: JobCreate, db: Session = Depends(get_db)) -> JobResponse:
    job = Job(**job_in.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return JobResponse.model_validate(job)


@router.get("/{job_id}", response_model=JobResponse, summary="Get Job Details")
def get_job(job_id: int, db: Session = Depends(get_db)) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise NotFoundError(f"Job with id {job_id} was not found", details={"job_id": job_id})
    return JobResponse.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Job Posting")
def delete_job(job_id: int, db: Session = Depends(get_db)) -> None:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise NotFoundError(f"Job with id {job_id} was not found", details={"job_id": job_id})
    db.delete(job)
    db.commit()
