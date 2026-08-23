from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.errors import NotFoundError
from app.models.company import Company
from app.schemas.company import CompanyResponse, CompanyListResponse

router = APIRouter(prefix="/companies", tags=["Companies Registry (Phase 3)"])


@router.get("", response_model=CompanyListResponse, summary="List Normalized Companies")
def list_companies(
    search: Optional[str] = Query(None, description="Search company name or industry"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> CompanyListResponse:
    query = db.query(Company)
    if search and search.strip():
        s = f"%{search.strip().lower()}%"
        query = query.filter((Company.normalized_name.ilike(s)) | (Company.industry.ilike(s)))

    total = query.count()
    items = (
        query.order_by(Company.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return CompanyListResponse(
        items=[CompanyResponse.model_validate(c) for c in items],
        total=total,
    )


@router.get("/{company_id}", response_model=CompanyResponse, summary="Get Company Details")
def get_company(company_id: int, db: Session = Depends(get_db)) -> CompanyResponse:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise NotFoundError(f"Company with id {company_id} not found.")
    return CompanyResponse.model_validate(company)
