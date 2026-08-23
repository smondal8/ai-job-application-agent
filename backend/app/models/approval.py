from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class ApplicationReview(Base, TimestampMixin):
    """Human-in-the-loop review and approval record (Phase 5 foundation)."""

    __tablename__ = "application_reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    decision = Column(String(50), default="pending", nullable=False)  # pending, approved, rejected, changes_requested
    reviewer_notes = Column(Text, nullable=True)
    manual_edits = Column(JSON, nullable=True, default=dict)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    application = relationship("Application", back_populates="reviews")
