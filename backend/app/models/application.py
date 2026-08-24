from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Application(Base, TimestampMixin):
    """Central Job Application entity linking a single job, candidate profile, and selected tailored resume (Phase 7 & 8)."""

    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    tailored_resume_id = Column(Integer, ForeignKey("tailored_resumes.id", ondelete="SET NULL"), nullable=True, index=True)
    candidate_profile_id = Column(Integer, ForeignKey("candidate_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # State Machine Lifecycle:
    # draft -> ready_for_review -> in_review -> approved -> staged_for_preparation -> requires_reapproval -> rejected -> archived
    status = Column(String(50), default="draft", index=True, nullable=False)
    
    # Approval Security Binding
    approval_token = Column(String(128), index=True, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    invalidation_reason = Column(Text, nullable=True)
    
    portal_type = Column(String(100), default="generic", nullable=False)  # greenhouse, lever, workday, ashby, generic
    portal_url = Column(String(1024), nullable=True)
    cover_letter = Column(Text, nullable=True)
    answers_payload = Column(JSON, nullable=True, default=dict)  # Custom screening answers, form fields
    submission_notes = Column(Text, nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    job = relationship("Job", back_populates="applications")
    tailored_resume = relationship("TailoredResume", back_populates="applications")
    candidate_profile = relationship("CandidateProfile", foreign_keys=[candidate_profile_id])
    reviews = relationship("ApplicationReview", back_populates="application", cascade="all, delete-orphan", order_by="desc(ApplicationReview.created_at)")
    approvals = relationship("ApplicationApproval", back_populates="application", cascade="all, delete-orphan", order_by="desc(ApplicationApproval.created_at)")
    audit_logs = relationship("AuditLog", back_populates="application", cascade="all, delete-orphan")
