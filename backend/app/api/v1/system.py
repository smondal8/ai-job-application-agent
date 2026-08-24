from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.observability.observability_service import observability_service
from app.services.recovery.crash_recovery_service import crash_recovery_service
from app.services.backup.backup_service import backup_service
from app.services.redaction.redaction_service import redaction_service
from app.core.logging import get_logger

logger = get_logger("app.api.v1.system")

router = APIRouter(prefix="/system", tags=["System Hardening & Observability"])


@router.get("/metrics", status_code=status.HTTP_200_OK)
def get_system_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieves real-time observability telemetry, counters, latencies, and health diagnostics."""
    return observability_service.get_metrics_snapshot(db)


@router.post("/recover-stale", status_code=status.HTTP_200_OK)
def recover_stale_tasks(
    max_age_minutes: int = Query(default=15, ge=1, le=1440),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Scans and safely reconciles any crashed, interrupted, or zombie background tasks."""
    observability_service.increment("recoveries_executed")
    return crash_recovery_service.reconcile_stale_runs(db=db, max_age_minutes=max_age_minutes)


@router.post("/backups", status_code=status.HTTP_201_CREATED)
def create_backup(
    include_artifacts: bool = Query(default=True),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Creates a verified database snapshot and compressed artifact tarball."""
    observability_service.increment("backups_created")
    return backup_service.create_backup(db=db, include_artifacts=include_artifacts)


@router.get("/backups", status_code=status.HTTP_200_OK)
def list_backups() -> List[Dict[str, Any]]:
    """Lists all available system backups with integrity and size metadata."""
    return backup_service.list_backups()


@router.post("/backups/{backup_id}/verify", status_code=status.HTTP_200_OK)
def verify_backup(backup_id: str) -> Dict[str, Any]:
    """Verifies SHA-256 cryptographic checksums and database integrity of a backup."""
    return backup_service.verify_backup(backup_id)


@router.post("/backups/{backup_id}/restore", status_code=status.HTTP_200_OK)
def restore_backup(backup_id: str) -> Dict[str, Any]:
    """Restores database and storage artifacts from a verified backup."""
    return backup_service.restore_backup(backup_id)


@router.post("/redact", status_code=status.HTTP_200_OK)
def redact_sensitive_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Utility endpoint to test sensitive credential and PII redaction."""
    return redaction_service.redact_structure(payload)
