from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class CandidateProfile(Base, TimestampMixin):
    """Verified Master Candidate Profile (Ground Truth for AI Agents)."""

    __tablename__ = "candidate_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    headline = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    website = Column(String(512), nullable=True)
    linkedin_url = Column(String(512), nullable=True)
    github_url = Column(String(512), nullable=True)
    portfolio_url = Column(String(512), nullable=True)
    
    # Ground Truth Verification Gate:
    # Only verified facts are exposed through the authoritative LLM service boundary.
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    experiences = relationship(
        "WorkExperience",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="WorkExperience.order_index",
    )
    educations = relationship(
        "Education",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    skills = relationship(
        "CandidateSkill",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    projects = relationship(
        "Project",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    raw_imports = relationship(
        "RawResumeImport",
        back_populates="profile",
        cascade="all, delete-orphan",
    )


class WorkExperience(Base, TimestampMixin):
    """Candidate Employment & Work Experience Record."""

    __tablename__ = "work_experiences"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    profile_id = Column(
        Integer,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company = Column(String(255), nullable=False)
    position = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=False)
    end_date = Column(String(50), nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)
    highlights = Column(JSON, nullable=True, default=list)  # Bullet points list
    skills_used = Column(JSON, nullable=True, default=list)  # Skill tags list
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    order_index = Column(Integer, default=0, nullable=False)

    profile = relationship("CandidateProfile", back_populates="experiences")


class Education(Base, TimestampMixin):
    """Candidate Education & Academic Credentials Record."""

    __tablename__ = "educations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    profile_id = Column(
        Integer,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution = Column(String(255), nullable=False)
    degree = Column(String(255), nullable=False)
    field_of_study = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    gpa = Column(String(50), nullable=True)
    highlights = Column(JSON, nullable=True, default=list)
    is_verified = Column(Boolean, default=False, nullable=False, index=True)

    profile = relationship("CandidateProfile", back_populates="educations")


class CandidateSkill(Base, TimestampMixin):
    """Categorized Candidate Competency & Skill Record."""

    __tablename__ = "candidate_skills"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    profile_id = Column(
        Integer,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), default="general", nullable=False)
    proficiency = Column(String(50), default="intermediate", nullable=False)
    years_of_experience = Column(Float, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False, index=True)

    profile = relationship("CandidateProfile", back_populates="skills")


class Project(Base, TimestampMixin):
    """Candidate Project Portfolio Record."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    profile_id = Column(
        Integer,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(512), nullable=True)
    highlights = Column(JSON, nullable=True, default=list)
    technologies = Column(JSON, nullable=True, default=list)
    is_verified = Column(Boolean, default=False, nullable=False, index=True)

    profile = relationship("CandidateProfile", back_populates="projects")


class RawResumeImport(Base, TimestampMixin):
    """Untrusted Raw Resume Import & Ingestion Record."""

    __tablename__ = "raw_resume_imports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    profile_id = Column(
        Integer,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    filename = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    raw_text = Column(Text, nullable=True)
    # Draft extracted facts (tagged as UNTRUSTED_DRAFT until human verification)
    parsed_data = Column(JSON, nullable=True, default=dict)
    status = Column(String(50), default="uploaded", nullable=False)  # uploaded, parsed, applied, archived

    profile = relationship("CandidateProfile", back_populates="raw_imports")
