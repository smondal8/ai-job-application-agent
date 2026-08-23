from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Job(Base, TimestampMixin):
    """Job listing model representing discovered, imported, or manually added positions."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    external_id = Column(String(255), nullable=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=True)
    remote_type = Column(String(50), nullable=True, default="unspecified")  # remote, hybrid, onsite
    job_type = Column(String(50), nullable=True, default="full-time")  # full-time, contract, part-time
    url = Column(String(1024), nullable=True)
    source = Column(String(100), nullable=False, default="manual")  # linkedin, indeed, greenhouse, manual
    description_raw = Column(Text, nullable=True)
    description_clean = Column(Text, nullable=True)
    salary_min = Column(Numeric(12, 2), nullable=True)
    salary_max = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(10), default="USD")
    status = Column(String(50), default="discovered", index=True, nullable=False)
    posted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships to future phase entities
    analyses = relationship("JobAnalysis", back_populates="job", cascade="all, delete-orphan")
    tailored_resumes = relationship("TailoredResume", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
