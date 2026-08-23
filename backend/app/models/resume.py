from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Resume(Base, TimestampMixin):
    """Base master resume model."""

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    version = Column(String(50), default="1.0", nullable=False)
    contact_info = Column(JSON, nullable=True, default=dict)
    summary = Column(Text, nullable=True)
    skills = Column(JSON, nullable=True, default=list)
    experience = Column(JSON, nullable=True, default=list)
    education = Column(JSON, nullable=True, default=list)
    raw_content = Column(Text, nullable=True)
    file_path = Column(String(1024), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)

    # Relationships
    tailored_versions = relationship("TailoredResume", back_populates="base_resume", cascade="all, delete-orphan")


class TailoredResume(Base, TimestampMixin):
    """Tailored resume and application materials with strict fact traceability (Phase 6)."""

    __tablename__ = "tailored_resumes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_profile_id = Column(Integer, ForeignKey("candidate_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    job_analysis_id = Column(Integer, ForeignKey("job_analyses.id", ondelete="SET NULL"), nullable=True, index=True)
    base_resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Model & Prompt Versioning
    prompt_version = Column(String(50), default="v1.0.0", nullable=False)
    model_used = Column(String(100), nullable=True)
    generation_metadata = Column(JSON, nullable=True, default=dict)

    # Structured Tailored Content (Claims with source_fact_ids)
    tailored_summary = Column(Text, nullable=True)
    tailored_experience = Column(JSON, nullable=True, default=list)
    highlighted_skills = Column(JSON, nullable=True, default=list)
    cover_letter = Column(Text, nullable=True)
    cover_letter_paragraphs = Column(JSON, nullable=True, default=list)
    diff_summary = Column(Text, nullable=True)

    # Deterministically Compiled Documents
    compiled_markdown = Column(Text, nullable=True)
    compiled_text = Column(Text, nullable=True)
    compiled_html = Column(Text, nullable=True)
    markdown_content = Column(Text, nullable=True)  # Backward compatibility alias
    file_path = Column(String(1024), nullable=True)

    # Traceability & Validation Subsystem
    traceability_matrix = Column(JSON, nullable=True, default=dict)
    validation_status = Column(String(50), default="valid", nullable=False)  # valid, requires_human_review, rejected
    validation_details = Column(JSON, nullable=True, default=dict)
    human_approved_at = Column(DateTime, nullable=True)
    human_approver_notes = Column(Text, nullable=True)

    # Workflow Status
    status = Column(String(50), default="ready_for_review", nullable=False)  # draft, ready_for_review, approved, rejected

    # Relationships
    job = relationship("Job", back_populates="tailored_resumes")
    base_resume = relationship("Resume", back_populates="tailored_versions")
    candidate_profile = relationship("CandidateProfile", foreign_keys=[candidate_profile_id])
    job_analysis = relationship("JobAnalysis", foreign_keys=[job_analysis_id])
    applications = relationship("Application", back_populates="tailored_resume")
