from sqlalchemy import Column, Integer, String, Text, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class JobAnalysis(Base, TimestampMixin):
    """Job Description analysis and match scoring model (Phase 5)."""

    __tablename__ = "job_analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_profile_id = Column(Integer, ForeignKey("candidate_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    fit_score = Column(Float, nullable=True)  # Composite score (0.0 to 100.0)
    deterministic_score = Column(Float, nullable=True)  # Deterministic keyword & criteria overlap (0.0 to 100.0)
    semantic_score = Column(Float, nullable=True)  # LLM semantic reasoning score (0.0 to 100.0)
    fit_level = Column(String(50), nullable=True)  # high, medium, low
    recommendation = Column(String(50), nullable=True)  # strong_apply, apply, stretch, skip
    summary = Column(Text, nullable=True)
    role_summary = Column(Text, nullable=True)
    key_responsibilities = Column(JSON, nullable=True, default=list)
    matched_skills = Column(JSON, nullable=True, default=list)
    missing_skills = Column(JSON, nullable=True, default=list)
    required_qualifications = Column(JSON, nullable=True, default=list)
    preferred_qualifications = Column(JSON, nullable=True, default=list)
    keywords = Column(JSON, nullable=True, default=list)
    red_flags = Column(JSON, nullable=True, default=list)
    model_used = Column(String(100), nullable=True)
    raw_llm_response = Column(Text, nullable=True)
    analysis_metadata = Column(JSON, nullable=True, default=dict)
    status = Column(String(50), default="pending", nullable=False)  # pending, completed, failed

    # Relationships
    job = relationship("Job", back_populates="analyses")
    candidate_profile = relationship("CandidateProfile", foreign_keys=[candidate_profile_id])
