import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.idempotency import IdempotencyRecord
from app.core.logging import get_logger

logger = get_logger("app.services.idempotency")


class IdempotencyService:
    """Enterprise idempotency and duplicate request prevention manager."""

    @staticmethod
    def compute_request_hash(payload: Any) -> str:
        """Computes deterministic SHA-256 hash of JSON-serializable request payload."""
        if payload is None:
            return hashlib.sha256(b"null").hexdigest()
        try:
            serialized = json.dumps(payload, sort_keys=True, default=str)
        except Exception:
            serialized = str(payload)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def process_idempotent_request(
        self,
        db: Session,
        idempotency_key: Optional[str],
        resource_type: str,
        request_payload: Any,
        ttl_seconds: int = 86400,
    ) -> Tuple[Optional[IdempotencyRecord], bool]:
        """Checks for existing idempotent execution.
        
        Returns:
            (record, is_cached)
            - If is_cached is True, record contains completed response_payload.
            - If is_cached is False, caller should execute work and call complete_idempotent_request.
        """
        if not idempotency_key:
            return None, False

        req_hash = self.compute_request_hash(request_payload)

        record = (
            db.query(IdempotencyRecord)
            .filter(IdempotencyRecord.idempotency_key == idempotency_key)
            .first()
        )

        if record:
            if record.status == "completed":
                logger.info(f"Idempotency cache HIT for key '{idempotency_key}' ({resource_type})")
                return record, True
            else:
                logger.warning(f"Idempotent request for key '{idempotency_key}' is currently {record.status}")
                return record, False

        # Create new in-progress record
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        new_record = IdempotencyRecord(
            idempotency_key=idempotency_key,
            resource_type=resource_type,
            request_hash=req_hash,
            status="in_progress",
            expires_at=expires_at,
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return new_record, False

    def complete_idempotent_request(
        self,
        db: Session,
        idempotency_key: Optional[str],
        response_payload: Any,
    ) -> None:
        """Marks idempotent record as completed and stores the response payload."""
        if not idempotency_key:
            return

        record = (
            db.query(IdempotencyRecord)
            .filter(IdempotencyRecord.idempotency_key == idempotency_key)
            .first()
        )
        if record:
            record.status = "completed"
            try:
                record.response_payload = json.loads(json.dumps(response_payload, default=str))
            except Exception:
                record.response_payload = str(response_payload)
            db.commit()
            logger.info(f"Idempotency record '{idempotency_key}' marked COMPLETED")

    def fail_idempotent_request(
        self,
        db: Session,
        idempotency_key: Optional[str],
        error_message: str,
    ) -> None:
        """Marks idempotent record as failed."""
        if not idempotency_key:
            return

        record = (
            db.query(IdempotencyRecord)
            .filter(IdempotencyRecord.idempotency_key == idempotency_key)
            .first()
        )
        if record:
            record.status = "failed"
            record.response_payload = {"error": error_message}
            db.commit()


idempotency_service = IdempotencyService()
