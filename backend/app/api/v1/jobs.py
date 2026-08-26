from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.core.database import get_db
from app.core.errors import NotFoundError, BadRequestError
from app.models.job import Job
from app.models.ingestion import JobIngestionBatch
from app.schemas.job import JobCreate, JobUpdate, JobResponse, JobListResponse
from app.schemas.ingestion import (
    JobIngestJsonRequest,
    JobIngestCsvRequest,
    JobIngestionBatchResponse,
    JobIngestionBatchListResponse,
)
from app.services.job_ingestion_service import job_ingestion_service

router = APIRouter(prefix="/jobs", tags=["Normalized Job Database & Ingestion (Phase 3)"])


@router.get("", response_model=JobListResponse, summary="List & Filter Jobs")
def list_jobs(
    search: Optional[str] = Query(None, description="Search keyword in title, company, or description"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    location: Optional[str] = Query(None, description="Filter by location"),
    remote_type: Optional[str] = Query(None, description="Filter: remote, hybrid, on_site"),
    seniority_level: Optional[str] = Query(None, description="Filter: entry, mid, senior, staff, lead, principal"),
    status: Optional[str] = Query(None, description="Filter by job status (discovered, analyzing, applied, archived, rejected)"),
    min_salary: Optional[float] = Query(None, description="Minimum base salary"),
    is_active: Optional[bool] = Query(True, description="Filter active jobs only"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> JobListResponse:
    query = db.query(Job)

    if status and status.strip():
        st = status.strip().lower()
        if st in ["archived", "rejected"]:
            query = query.filter(Job.status == st)
        else:
            query = query.filter(Job.status == st)
            if is_active is not None:
                query = query.filter(Job.is_active == is_active)
    elif is_active is not None:
        query = query.filter(Job.is_active == is_active)

    if search and search.strip():
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Job.title.ilike(s),
                Job.company.ilike(s),
                Job.description_raw.ilike(s),
                Job.normalized_title.ilike(s),
                Job.location.ilike(s),
            )
        )

    if company and company.strip():
        query = query.filter(Job.company.ilike(f"%{company.strip()}%"))

    if location and location.strip():
        query = query.filter(Job.location.ilike(f"%{location.strip()}%"))

    if remote_type and remote_type.strip():
        query = query.filter(Job.remote_type == remote_type.strip().lower())

    if seniority_level and seniority_level.strip():
        query = query.filter(Job.seniority_level == seniority_level.strip().lower())

    if min_salary is not None:
        query = query.filter(Job.salary_max >= min_salary)

    total = query.count()
    items = (
        query.order_by(desc(Job.posted_at), desc(Job.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return JobListResponse(
        items=[JobResponse.model_validate(j) for j in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED, summary="Create Job Manually")
def create_job(job_in: JobCreate, db: Session = Depends(get_db)) -> JobResponse:
    result = job_ingestion_service.ingest_records(
        db=db,
        records=[job_in.model_dump(exclude_unset=True)],
        source="manual",
    )
    # Fetch newly created job
    job = db.query(Job).filter(Job.batch_id == result["batch_id"]).first()
    if not job:
        # If it was duplicate, return existing
        job = db.query(Job).order_by(desc(Job.id)).first()
    return JobResponse.model_validate(job)


@router.get("/{job_id}", response_model=JobResponse, summary="Get Job Details")
def get_job(job_id: int, db: Session = Depends(get_db)) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise NotFoundError(f"Job with id {job_id} not found.")
    return JobResponse.model_validate(job)


@router.put("/{job_id}", response_model=JobResponse, summary="Update Job")
def update_job(job_id: int, job_update: JobUpdate, db: Session = Depends(get_db)) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise NotFoundError(f"Job with id {job_id} not found.")

    update_dict = job_update.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if hasattr(job, field) and value is not None:
            setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return JobResponse.model_validate(job)


@router.patch("/{job_id}", response_model=JobResponse, summary="Patch Job")
def patch_job(job_id: int, job_update: JobUpdate, db: Session = Depends(get_db)) -> JobResponse:
    return update_job(job_id=job_id, job_update=job_update, db=db)


@router.post("/{job_id}/archive", response_model=JobResponse, summary="Archive Job (Not Relevant)")
def archive_job(job_id: int, db: Session = Depends(get_db)) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise NotFoundError(f"Job with id {job_id} not found.")
    job.is_active = False
    job.status = "archived"
    db.commit()
    db.refresh(job)
    return JobResponse.model_validate(job)


@router.post("/{job_id}/reject", response_model=JobResponse, summary="Reject / Skip Job")
def reject_job(job_id: int, db: Session = Depends(get_db)) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise NotFoundError(f"Job with id {job_id} not found.")
    job.is_active = False
    job.status = "rejected"
    db.commit()
    db.refresh(job)
    return JobResponse.model_validate(job)


@router.post("/{job_id}/restore", response_model=JobResponse, summary="Restore Archived / Rejected Job")
def restore_job(job_id: int, db: Session = Depends(get_db)) -> JobResponse:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise NotFoundError(f"Job with id {job_id} not found.")
    job.is_active = True
    if job.analyses and len(job.analyses) > 0:
        job.status = "analyzed"
    elif job.tailored_resumes and len(job.tailored_resumes) > 0:
        job.status = "tailored"
    else:
        job.status = "discovered"
    db.commit()
    db.refresh(job)
    return JobResponse.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Job")
def delete_job(job_id: int, db: Session = Depends(get_db)) -> None:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise NotFoundError(f"Job with id {job_id} not found.")
    if job.applications and any(app.status not in ["withdrawn", "rejected"] for app in job.applications):
        raise BadRequestError("Cannot delete job with active applications. Archive the job instead or withdraw active applications.")
    db.delete(job)
    db.commit()


# --- Ingestion Subsystem Endpoints ---

@router.post(
    "/ingest/json",
    response_model=JobIngestionBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Jobs from JSON",
    description="Ingest an array of job records or JSON text with conservative deduplication.",
)
def ingest_json_jobs(
    payload: JobIngestJsonRequest, db: Session = Depends(get_db)
) -> JobIngestionBatchResponse:
    if payload.jobs:
        result = job_ingestion_service.ingest_records(
            db=db, records=payload.jobs, source=payload.source
        )
    elif payload.json_payload:
        result = job_ingestion_service.ingest_json_text(
            db=db, json_text=payload.json_payload, source=payload.source
        )
    else:
        raise BadRequestError("Either 'jobs' array or 'json_payload' string must be provided.")

    return JobIngestionBatchResponse(**result)


@router.post(
    "/ingest/csv",
    response_model=JobIngestionBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Jobs from CSV",
    description="Ingest raw CSV formatted job listings with column alias mapping and deduplication.",
)
def ingest_csv_jobs(
    payload: JobIngestCsvRequest, db: Session = Depends(get_db)
) -> JobIngestionBatchResponse:
    result = job_ingestion_service.ingest_csv_text(
        db=db, csv_text=payload.csv_text, source=payload.source
    )
    return JobIngestionBatchResponse(**result)


@router.post(
    "/ingest/file",
    response_model=JobIngestionBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload & Ingest Job File (JSON or CSV)",
)
async def upload_job_file(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> JobIngestionBatchResponse:
    content_bytes = await file.read()
    if not content_bytes:
        raise BadRequestError("Uploaded file is empty.")

    filename = file.filename or "uploaded_jobs.txt"
    text_content = content_bytes.decode("utf-8", errors="replace")

    if filename.endswith(".json"):
        result = job_ingestion_service.ingest_json_text(
            db=db, json_text=text_content, source="json_upload", filename=filename
        )
    elif filename.endswith(".csv"):
        result = job_ingestion_service.ingest_csv_text(
            db=db, csv_text=text_content, source="csv_upload", filename=filename
        )
    else:
        # Try JSON then CSV fallback
        try:
            result = job_ingestion_service.ingest_json_text(
                db=db, json_text=text_content, source="file_upload", filename=filename
            )
        except Exception:
            result = job_ingestion_service.ingest_csv_text(
                db=db, csv_text=text_content, source="file_upload", filename=filename
            )

    return JobIngestionBatchResponse(**result)


@router.post(
    "/ingest/seed-fixtures",
    response_model=List[JobIngestionBatchResponse],
    summary="Seed Built-in JSON and CSV Sample Fixtures",
    description="Loads sample test fixtures from backend/fixtures to prove ingestion and conservative deduplication.",
)
def seed_sample_fixtures(db: Session = Depends(get_db)) -> List[JobIngestionBatchResponse]:
    results = []
    fixtures_dir = Path(__file__).parent.parent.parent.parent / "fixtures"

    json_fixture = fixtures_dir / "jobs_sample.json"
    if json_fixture.exists():
        res_json = job_ingestion_service.ingest_json_text(
            db=db,
            json_text=json_fixture.read_text(encoding="utf-8"),
            source="fixture_seed_json",
            filename="jobs_sample.json",
        )
        results.append(JobIngestionBatchResponse(**res_json))

    csv_fixture = fixtures_dir / "jobs_sample.csv"
    if csv_fixture.exists():
        res_csv = job_ingestion_service.ingest_csv_text(
            db=db,
            csv_text=csv_fixture.read_text(encoding="utf-8"),
            source="fixture_seed_csv",
            filename="jobs_sample.csv",
        )
        results.append(JobIngestionBatchResponse(**res_csv))

    return results


@router.get(
    "/ingest/batches",
    response_model=JobIngestionBatchListResponse,
    summary="List Ingestion Batches",
)
def list_ingestion_batches(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> JobIngestionBatchListResponse:
    query = db.query(JobIngestionBatch)
    total = query.count()
    items = (
        query.order_by(desc(JobIngestionBatch.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return JobIngestionBatchListResponse(
        items=[JobIngestionBatchResponse.model_validate(b) for b in items],
        total=total,
    )
