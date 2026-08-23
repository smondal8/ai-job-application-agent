from datetime import datetime, timezone
import os
from pathlib import Path
import time
from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.database import check_database_connection
from app.core.logging import get_logger
from app.schemas.health import (
    HealthResponse,
    ReadinessResponse,
    LivenessResponse,
    DatabaseHealth,
    StorageHealth,
)

router = APIRouter(tags=["Health & Diagnostics"])
logger = get_logger("app.api.health")
settings = get_settings()

APP_START_TIME = time.time()


def get_storage_health() -> StorageHealth:
    """Verify local storage directory exists and is writable."""
    storage_path = Path(settings.STORAGE_DIR)
    try:
        storage_path.mkdir(parents=True, exist_ok=True)
        # Test write capability
        test_file = storage_path / ".health_check_probe"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return StorageHealth(
            status="healthy",
            storage_dir=str(storage_path.resolve()),
            writable=True,
        )
    except Exception as exc:
        logger.error("Storage health probe failed: %s", exc)
        return StorageHealth(
            status="unhealthy",
            storage_dir=str(storage_path),
            writable=False,
            error=str(exc),
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Comprehensive System Health Check",
    description="Returns detailed health metrics for database, local storage, uptime, and configuration.",
)
def get_health() -> HealthResponse:
    db_result = check_database_connection()
    storage_result = get_storage_health()
    uptime = round(time.time() - APP_START_TIME, 2)

    is_healthy = db_result["connected"] and storage_result.writable
    overall_status = "healthy" if is_healthy else "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=settings.APP_VERSION,
        uptime_seconds=uptime,
        environment=settings.ENVIRONMENT,
        database=DatabaseHealth(
            status=db_result["status"],
            connected=db_result["connected"],
            latency_ms=db_result["latency_ms"],
            dialect=db_result["dialect"],
            database_target=db_result.get("database_target"),
            error=db_result.get("error"),
        ),
        storage=storage_result,
    )


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    summary="Liveness Probe",
    description="Fast check to verify the process is alive.",
)
def get_liveness() -> LivenessResponse:
    return LivenessResponse(status="alive")


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    description="Verifies backend subsystems are ready to accept traffic.",
)
def get_readiness(response: Response) -> ReadinessResponse:
    db_result = check_database_connection()
    storage_result = get_storage_health()

    db_ready = db_result["connected"]
    storage_ready = storage_result.writable
    is_ready = db_ready and storage_ready

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        ready=is_ready,
        status="ready" if is_ready else "not_ready",
        timestamp=datetime.now(timezone.utc).isoformat(),
        checks={
            "database": db_ready,
            "storage": storage_ready,
        },
    )
