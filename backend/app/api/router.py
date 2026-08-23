from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.config import router as config_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.companies import router as companies_router
from app.api.v1.discovery import router as discovery_router
from app.api.v1.applications import router as applications_router
from app.api.v1.resumes import router as resumes_router
from app.api.v1.profile import router as profile_router
from app.api.v1.raw_resumes import router as raw_resumes_router

api_v1_router = APIRouter()

# Core Phase 1 Routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(config_router)
api_v1_router.include_router(applications_router)
api_v1_router.include_router(resumes_router)

# Phase 2 Candidate Profile Routers
api_v1_router.include_router(profile_router)
api_v1_router.include_router(raw_resumes_router)

# Phase 3 Normalized Job Database & Ingestion Routers
api_v1_router.include_router(jobs_router)
api_v1_router.include_router(companies_router)

# Phase 4 Source-Agnostic Job Discovery Framework
api_v1_router.include_router(discovery_router)
