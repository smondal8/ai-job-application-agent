from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import NotFoundError
from app.models.discovery import JobDiscoveryRun, JobSearchProfile
from app.schemas.discovery import (
    AdapterInfoResponse,
    DiscoveryRunRequest,
    DiscoveryRunResponse,
    DiscoveryRunListResponse,
    SearchProfileCreate,
    SearchProfileResponse,
    SearchProfileListResponse,
)
from app.services.discovery.registry import discovery_registry
from app.services.discovery.orchestrator import discovery_orchestrator

router = APIRouter(prefix="/discovery", tags=["Job Discovery Framework"])


@router.get("/adapters", response_model=List[AdapterInfoResponse])
def list_adapters():
    """List all registered source-agnostic discovery adapters and their capabilities."""
    return discovery_registry.list_adapters()


@router.post("/run", response_model=DiscoveryRunResponse, status_code=status.HTTP_201_CREATED)
async def run_discovery(
    payload: DiscoveryRunRequest,
    db: Session = Depends(get_db),
):
    """Execute on-demand multi-source job discovery and ingest discovered listings."""
    run_record = await discovery_orchestrator.execute_discovery_run(
        db=db,
        criteria=payload.criteria,
        specific_source=payload.source,
        search_profile_id=payload.search_profile_id,
    )
    return run_record


@router.get("/runs", response_model=DiscoveryRunListResponse)
def list_discovery_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List historical discovery runs and execution audit ledger."""
    query = db.query(JobDiscoveryRun).order_by(JobDiscoveryRun.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return DiscoveryRunListResponse(
        items=[DiscoveryRunResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/runs/{run_id}", response_model=DiscoveryRunResponse)
def get_discovery_run(run_id: str, db: Session = Depends(get_db)):
    """Get detailed discovery execution metrics and per-adapter logs."""
    run = db.query(JobDiscoveryRun).filter(JobDiscoveryRun.run_id == run_id).first()
    if not run:
        raise NotFoundError(f"Discovery run '{run_id}' not found.")
    return run


@router.post("/search-profiles", response_model=SearchProfileResponse, status_code=status.HTTP_201_CREATED)
def create_search_profile(payload: SearchProfileCreate, db: Session = Depends(get_db)):
    """Save a search criteria template for repeated or automated discovery."""
    existing = db.query(JobSearchProfile).filter(JobSearchProfile.name == payload.name).first()
    if existing:
        # Update existing profile
        existing.description = payload.description
        existing.criteria = payload.criteria.model_dump()
        existing.is_active = payload.is_active
        existing.auto_run_interval_hours = payload.auto_run_interval_hours
        db.commit()
        db.refresh(existing)
        return existing

    new_profile = JobSearchProfile(
        name=payload.name,
        description=payload.description,
        criteria=payload.criteria.model_dump(),
        is_active=payload.is_active,
        auto_run_interval_hours=payload.auto_run_interval_hours,
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile


def _ensure_default_search_profiles(db: Session) -> None:
    """Ensure standard search profile exists for India/Bangalore/Remote backend engineering."""
    existing = db.query(JobSearchProfile).filter(JobSearchProfile.name == "Senior / Staff Backend Engineer (India & Remote)").first()
    if not existing:
        default_profile = JobSearchProfile(
            name="Senior / Staff Backend Engineer (India & Remote)",
            description="Senior & Staff Backend Engineering roles across Bangalore, India and Remote hubs (Java, Spring Boot, Distributed Systems).",
            criteria={
                "keywords": [
                    "Senior Software Engineer",
                    "Staff Software Engineer",
                    "Backend Engineer",
                    "Java",
                    "Spring Boot",
                    "Distributed Systems",
                ],
                "locations": ["Bangalore", "Bengaluru", "India", "Remote"],
                "remote_only": False,
                "seniority_levels": ["senior", "staff", "lead"],
                "sources": ["greenhouse", "lever", "remote_tech"],
                "target_companies": [],
                "max_results_per_source": 25,
            },
            is_active=True,
            auto_run_interval_hours=24,
        )
        db.add(default_profile)
        db.commit()


@router.get("/search-profiles", response_model=SearchProfileListResponse)
def list_search_profiles(db: Session = Depends(get_db)):
    """List all saved job search profiles."""
    _ensure_default_search_profiles(db)
    profiles = db.query(JobSearchProfile).order_by(JobSearchProfile.created_at.desc()).all()
    return SearchProfileListResponse(
        items=[SearchProfileResponse.model_validate(p) for p in profiles],
        total=len(profiles),
    )


@router.delete("/search-profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_search_profile(profile_id: int, db: Session = Depends(get_db)):
    """Delete a saved search profile."""
    profile = db.query(JobSearchProfile).filter(JobSearchProfile.id == profile_id).first()
    if not profile:
        raise NotFoundError(f"Search profile {profile_id} not found.")
    db.delete(profile)
    db.commit()
    return None
