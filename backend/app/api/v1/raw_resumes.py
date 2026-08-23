from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.errors import NotFoundError, BadRequestError
from app.models.candidate import RawResumeImport
from app.schemas.candidate import (
    RawResumeImportCreateText,
    RawResumeImportResponse,
    CandidateProfileResponse,
)
from app.services.profile_service import profile_service

router = APIRouter(prefix="/resumes/imports", tags=["Raw Resume Ingestion (Phase 2)"])


@router.post(
    "/upload",
    response_model=RawResumeImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Raw Resume File",
    description="Upload raw resume file (txt, md, json, pdf, docx). Stored securely locally; parsed draft facts remain untrusted until user verification.",
)
async def upload_raw_resume_file(
    file: UploadFile = File(...),
    profile_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
) -> RawResumeImportResponse:
    content_bytes = await file.read()
    if not content_bytes:
        raise BadRequestError("Uploaded file is empty.")

    raw_import = profile_service.import_raw_resume_file(
        db=db,
        filename=file.filename or "uploaded_resume.txt",
        content_bytes=content_bytes,
        mime_type=file.content_type or "application/octet-stream",
        profile_id=profile_id,
    )
    return RawResumeImportResponse.model_validate(raw_import)


@router.post(
    "/text",
    response_model=RawResumeImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import Raw Resume Text",
    description="Ingest raw pasted resume text/markdown string.",
)
def import_raw_resume_text(
    payload: RawResumeImportCreateText,
    profile_id: Optional[int] = None,
    db: Session = Depends(get_db),
) -> RawResumeImportResponse:
    raw_import = profile_service.import_raw_resume_text(
        db=db,
        raw_text=payload.raw_text,
        label=payload.label or "Pasted Resume Text",
        profile_id=profile_id,
    )
    return RawResumeImportResponse.model_validate(raw_import)


@router.get("", response_model=List[RawResumeImportResponse], summary="List Raw Resume Imports")
def list_raw_resume_imports(db: Session = Depends(get_db)) -> List[RawResumeImportResponse]:
    imports = db.query(RawResumeImport).order_by(desc(RawResumeImport.created_at)).all()
    return [RawResumeImportResponse.model_validate(imp) for imp in imports]


@router.get("/{import_id}", response_model=RawResumeImportResponse, summary="Get Raw Resume Import Details")
def get_raw_resume_import(import_id: int, db: Session = Depends(get_db)) -> RawResumeImportResponse:
    raw_import = db.query(RawResumeImport).filter(RawResumeImport.id == import_id).first()
    if not raw_import:
        raise NotFoundError(f"Raw resume import with id {import_id} not found.")
    return RawResumeImportResponse.model_validate(raw_import)


@router.post(
    "/{import_id}/apply-to-profile",
    response_model=CandidateProfileResponse,
    summary="Transfer Extracted Draft Facts to Candidate Profile",
    description="Transfers draft extracted facts into candidate profile as UNVERIFIED entities ready for user review.",
)
def apply_import_to_profile(
    import_id: int,
    profile_id: Optional[int] = None,
    db: Session = Depends(get_db),
) -> CandidateProfileResponse:
    target_profile_id = profile_id
    if not target_profile_id:
        target_profile = profile_service.get_or_create_primary_profile(db)
        target_profile_id = target_profile.id

    updated_profile = profile_service.apply_raw_import_to_profile(
        db=db, import_id=import_id, profile_id=target_profile_id
    )
    return CandidateProfileResponse.model_validate(updated_profile)
