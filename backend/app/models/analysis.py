from sqlalchemy import Column, Integer, String, Text, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class JobAnalysis(Base, TimestampMixin):
    """Job Description analysis and match scoring model (Phase 3 foundation)."""

    __tablename__ = "job_analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    fit_score = Column(Float, nullable=True)  # 0.0 to 100.0
    fit_level = Column(String(50), nullable=True)  # high, medium, low
    summary = Column(Text, nullable=True)
    matched_skills = Column(JSON, nullable=True, default=list)
    missing_skills = Column(JSON, nullable=True, default=list)
    required_qualifications = Column(JSON, nullable=True, default=list)
    preferred_qualifications = Column(JSON, nullable=True, default=list)
    keywords = Column(JSON, nullable=True, default=list)
    analysis_metadata = Column(JSON, nullable=True, default=dict)
    status = Column(String(50), default="pending", nullable=False)  # pending, completed, failed

    # Relationships
    job = relationship("Job", back_populates="analyses")
