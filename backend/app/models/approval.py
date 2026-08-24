from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class ApplicationReview(Base, TimestampMixin):
    """Human-in-the-loop review notes and assessment records."""

    __tablename__ = "application_reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    decision = Column(String(50), default="pending", nullable=False)  # pending, approved, rejected, changes_requested
    reviewer_notes = Column(Text, nullable=True)
    manual_edits = Column(JSON, nullable=True, default=dict)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    application = relationship("Application", back_populates="reviews")


class ApplicationApproval(Base, TimestampMixin):
    """Cryptographic human approval certificate binding material inputs to application authorization (Phase 8 Security Boundary)."""

    __tablename__ = "application_approvals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="approved", nullable=False, index=True)  # approved, invalidated, revoked, rejected
    
    # Material input snapshots / hashes
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    approved_job_hash = Column(String(64), nullable=False)
    
    candidate_profile_id = Column(Integer, ForeignKey("candidate_profiles.id", ondelete="SET NULL"), nullable=True)
    approved_candidate_hash = Column(String(64), nullable=False)
    
    tailored_resume_id = Column(Integer, ForeignKey("tailored_resumes.id", ondelete="SET NULL"), nullable=True)
    approved_resume_hash = Column(String(64), nullable=False)
    
    approved_answers_hash = Column(String(64), nullable=False)
    
    # Cryptographic Authorization Token
    approval_token = Column(String(128), unique=True, index=True, nullable=False)
    approver_id = Column(String(100), default="human_reviewer", nullable=False)
    approver_notes = Column(Text, nullable=True)
    
    # Invalidation & Validity tracking
    is_valid = Column(Boolean, default=True, index=True, nullable=False)
    invalidation_reason = Column(Text, nullable=True)
    invalidated_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    application = relationship("Application", back_populates="approvals")
    job = relationship("Job")
    tailored_resume = relationship("TailoredResume")
    candidate_profile = relationship("CandidateProfile")
