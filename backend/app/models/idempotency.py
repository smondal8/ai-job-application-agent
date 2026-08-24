from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from app.models.base import Base


class IdempotencyRecord(Base):
    """Database model for storing and verifying idempotent API and background operations."""

    __tablename__ = "idempotency_records"

    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=False)
    resource_type = Column(String(64), index=True, nullable=False)
    request_hash = Column(String(64), nullable=False)
    response_payload = Column(JSON, nullable=True)
    status = Column(String(32), default="in_progress", nullable=False)  # in_progress, completed, failed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "idempotency_key": self.idempotency_key,
            "resource_type": self.resource_type,
            "request_hash": self.request_hash,
            "response_payload": self.response_payload,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
