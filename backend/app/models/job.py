from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Job(Base, TimestampMixin):
    """Normalized Job Listing Model representing discovered, imported, or manually added positions."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    external_id = Column(String(255), nullable=True, index=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    batch_id = Column(
        String(64),
        ForeignKey("job_ingestion_batches.batch_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Core Attributes
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True)

    # Normalized & Deduplication Signature Columns
    dedup_hash = Column(String(64), index=True, nullable=True)
    normalized_company = Column(String(255), index=True, nullable=True)
    normalized_title = Column(String(255), index=True, nullable=True)
    normalized_location = Column(String(255), index=True, nullable=True)

    # Employment & Workplace Metadata
    remote_type = Column(String(50), nullable=True, default="unspecified")  # remote, hybrid, on_site, unspecified
    workplace_type = Column(String(50), nullable=True, default="unspecified")  # remote, hybrid, on_site
    job_type = Column(String(50), nullable=True, default="full-time")  # full-time, contract, part-time, internship
    employment_type = Column(String(50), nullable=True, default="full_time")  # full_time, contract, part_time, internship
    seniority_level = Column(String(50), nullable=True)  # entry, mid, senior, staff, lead, principal, executive
    experience_years_min = Column(Integer, nullable=True)
    experience_years_max = Column(Integer, nullable=True)

    # Description & Compensation
    url = Column(String(1024), nullable=True)
    source = Column(String(100), nullable=False, default="manual")  # json_import, csv_import, manual, etc.
    description_raw = Column(Text, nullable=True)
    description_clean = Column(Text, nullable=True)
    salary_min = Column(Numeric(12, 2), nullable=True)
    salary_max = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(10), default="USD")

    # Structured metadata
    skills_raw = Column(JSON, default=list, nullable=True)
    benefits = Column(JSON, default=list, nullable=True)
    metadata_extra = Column(JSON, default=dict, nullable=True)

    # Lifecycle & Active State
    status = Column(String(50), default="discovered", index=True, nullable=False)
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    company_rel = relationship("Company", back_populates="jobs")
    batch = relationship("JobIngestionBatch", back_populates="jobs")
    analyses = relationship("JobAnalysis", back_populates="job", cascade="all, delete-orphan")
    tailored_resumes = relationship("TailoredResume", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
