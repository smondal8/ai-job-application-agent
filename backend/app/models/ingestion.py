from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class JobIngestionBatch(Base, TimestampMixin):
    """Job Ingestion Batch Execution & Audit Ledger Record."""

    __tablename__ = "job_ingestion_batches"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    batch_id = Column(String(64), unique=True, nullable=False, index=True)
    source = Column(String(100), nullable=False)  # json_import, csv_import, fixture_seed
    filename = Column(String(255), nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)
    total_records = Column(Integer, default=0, nullable=False)
    inserted_count = Column(Integer, default=0, nullable=False)
    updated_count = Column(Integer, default=0, nullable=False)
    duplicate_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="completed", nullable=False)  # processing, completed, failed
    error_log = Column(JSON, default=list, nullable=True)

    # Relationships
    jobs = relationship("Job", back_populates="batch")
