from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Application(Base, TimestampMixin):
    """Job application state machine model (Phase 5 & 6 foundation)."""

    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    tailored_resume_id = Column(Integer, ForeignKey("tailored_resumes.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="draft", index=True, nullable=False)
    # Status lifecycle: draft -> prepared -> pending_approval -> approved -> submitting -> submitted -> failed
    portal_type = Column(String(100), default="generic", nullable=False)  # workday, greenhouse, lever, ashby, generic
    portal_url = Column(String(1024), nullable=True)
    cover_letter = Column(Text, nullable=True)
    answers_payload = Column(JSON, nullable=True, default=dict)
    submission_notes = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    job = relationship("Job", back_populates="applications")
    tailored_resume = relationship("TailoredResume", back_populates="applications")
    reviews = relationship("ApplicationReview", back_populates="application", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="application", cascade="all, delete-orphan")
