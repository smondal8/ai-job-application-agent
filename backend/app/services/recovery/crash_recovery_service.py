from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.discovery import JobDiscoveryRun
from app.models.preparation import BrowserPreparationRun
from app.models.audit import AuditLog
from app.core.logging import get_logger

logger = get_logger("app.services.recovery")


class CrashRecoveryService:
    """Enterprise crash recovery, orphan task reconciliation, and stale state cleanup."""

    @staticmethod
    def _to_utc_aware(dt: Any) -> Optional[datetime]:
        if not dt:
            return None
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except Exception:
                return None
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        return None

    def reconcile_stale_runs(
        self,
        db: Session,
        max_age_minutes: int = 15,
    ) -> Dict[str, Any]:
        """Scans for and transitions any zombie/stale background tasks that crashed during execution."""
        now_utc = datetime.now(timezone.utc)
        cutoff = now_utc - timedelta(minutes=max_age_minutes)
        reconciled_discovery = 0
        reconciled_preparation = 0

        # 1. Reconcile Stale Discovery Runs
        active_discovery = (
            db.query(JobDiscoveryRun)
            .filter(JobDiscoveryRun.status == "running")
            .all()
        )
        for disc in active_discovery:
            created = self._to_utc_aware(disc.created_at)
            if created and created < cutoff:
                disc.status = "failed"
                disc.error_count = (disc.error_count or 0) + 1
                logs = list(disc.adapter_logs or [])
                logs.append({"event": "crash_recovery", "message": f"Task was abandoned in running state since {disc.created_at}."})
                disc.adapter_logs = logs
                reconciled_discovery += 1
                logger.warning(f"Reconciled crashed discovery run #{disc.id}")

                # Audit log
                audit = AuditLog(
                    stage="discovery",
                    action="DISCOVERY_CRASH_RECOVERED",
                    level="warning",
                    message=f"Auto-recovered crashed discovery run #{disc.id}",
                    payload={"run_id": disc.run_id, "recovered_at": now_utc.isoformat()},
                )
                db.add(audit)

        # 2. Reconcile Stale Preparation Runs
        active_prep = (
            db.query(BrowserPreparationRun)
            .filter(BrowserPreparationRun.status.in_(["initialized", "in_progress"]))
            .all()
        )
        for prep in active_prep:
            created = self._to_utc_aware(prep.created_at)
            if created and created < cutoff:
                prep.status = "failed"
                prep.error_message = f"Process crash recovery: Staging run was interrupted/crashed without finalization since {prep.created_at}."
                reconciled_preparation += 1
                logger.warning(f"Reconciled crashed preparation run #{prep.id}")

                # Audit log
                audit = AuditLog(
                    application_id=prep.application_id,
                    stage="submission",
                    action="PREPARATION_CRASH_RECOVERED",
                    level="warning",
                    message=f"Auto-recovered crashed preparation run #{prep.id}",
                    payload={"prep_id": prep.id, "recovered_at": now_utc.isoformat()},
                )
                db.add(audit)

        db.commit()

        return {
            "reconciled_discovery_runs": reconciled_discovery,
            "reconciled_preparation_runs": reconciled_preparation,
            "total_recovered": reconciled_discovery + reconciled_preparation,
            "timestamp": now_utc.isoformat(),
        }


crash_recovery_service = CrashRecoveryService()
