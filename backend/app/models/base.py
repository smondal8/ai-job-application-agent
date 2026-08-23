from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Mixin adding created_at and updated_at UTC timestamps."""
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
