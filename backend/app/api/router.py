from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.config import router as config_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.applications import router as applications_router
from app.api.v1.resumes import router as resumes_router

api_v1_router = APIRouter()

# Include health routes under /health and root
api_v1_router.include_router(health_router)
api_v1_router.include_router(config_router)
api_v1_router.include_router(jobs_router)
api_v1_router.include_router(applications_router)
api_v1_router.include_router(resumes_router)
