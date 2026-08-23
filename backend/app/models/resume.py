from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Resume(Base, TimestampMixin):
    """Base master resume model (Phase 4 foundation)."""

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
    """Tailored resume variant tailored to a specific job listing."""

    __tablename__ = "tailored_resumes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    base_resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    tailored_summary = Column(Text, nullable=True)
    tailored_experience = Column(JSON, nullable=True, default=list)
    highlighted_skills = Column(JSON, nullable=True, default=list)
    diff_summary = Column(Text, nullable=True)
    file_path = Column(String(1024), nullable=True)

    # Relationships
    job = relationship("Job", back_populates="tailored_resumes")
    base_resume = relationship("Resume", back_populates="tailored_versions")
    applications = relationship("Application", back_populates="tailored_resume")
