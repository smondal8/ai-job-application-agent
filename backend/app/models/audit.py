from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(Base):
    """Audit log tracking system events, automated actions, and pipeline steps."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True)
    stage = Column(String(50), nullable=False, index=True)  # discovery, analysis, tailoring, approval, submission, system
    action = Column(String(100), nullable=False)
    level = Column(String(20), default="info", nullable=False)  # info, warning, error
    message = Column(Text, nullable=False)
    payload = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    application = relationship("Application", back_populates="audit_logs")
