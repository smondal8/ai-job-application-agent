from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.errors import NotFoundError
from app.models.application import Application
from app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationListResponse

router = APIRouter(prefix="/applications", tags=["Applications (Phase 5 & 6 Foundation)"])


@router.get("", response_model=ApplicationListResponse, summary="List Job Applications")
def list_applications(
    status: Optional[str] = Query(None, description="Filter by status (e.g. draft, pending_approval)"),
    db: Session = Depends(get_db),
) -> ApplicationListResponse:
    query = db.query(Application)
    if status:
        query = query.filter(Application.status == status)

    total = query.count()
    items = query.order_by(desc(Application.created_at)).all()

    return ApplicationListResponse(
        items=[ApplicationResponse.model_validate(item) for item in items],
        total=total,
    )


@router.get("/{application_id}", response_model=ApplicationResponse, summary="Get Application Details")
def get_application(application_id: int, db: Session = Depends(get_db)) -> ApplicationResponse:
    app_entity = db.query(Application).filter(Application.id == application_id).first()
    if not app_entity:
        raise NotFoundError(
            f"Application with id {application_id} was not found",
            details={"application_id": application_id},
        )
    return ApplicationResponse.model_validate(app_entity)
