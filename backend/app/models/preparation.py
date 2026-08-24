from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base


class BrowserPreparationRun(Base):
    """Execution audit and staging record of Playwright browser application preparation."""

    __tablename__ = "browser_preparation_runs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(
        Integer,
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id = Column(
        Integer,
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    approval_id = Column(
        Integer,
        ForeignKey("application_approvals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    approval_token = Column(String(128), nullable=False, index=True)
    portal_type = Column(String(100), nullable=False, default="generic")
    portal_url = Column(String(1024), nullable=True)

    # Status: initialized, running, staged, paused_for_human_input, blocked_by_captcha, blocked_by_auth, failed
    status = Column(String(50), nullable=False, default="initialized", index=True)

    # Detailed field mappings and actions executed
    fields_filled = Column(JSON, default=list)
    unresolved_fields = Column(JSON, default=list)

    # Document upload status
    resume_uploaded = Column(Boolean, default=False)
    resume_file_path = Column(String(1024), nullable=True)

    # Visual audit artifact
    screenshot_path = Column(String(1024), nullable=True)

    # Strict Safety Boundaries
    final_submit_clicked = Column(Boolean, default=False, nullable=False)
    guard_triggered = Column(Boolean, default=False, nullable=False)
    captcha_detected = Column(Boolean, default=False, nullable=False)
    auth_required = Column(Boolean, default=False, nullable=False)

    error_message = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    application = relationship("Application", backref="preparation_runs")
    job = relationship("Job")
    approval = relationship("ApplicationApproval")
