from sqlalchemy import Column, Integer, String, Text, Boolean, Float, JSON
from app.core.database import Base
from app.models.base import TimestampMixin


class JobDiscoveryRun(Base, TimestampMixin):
    """Job Discovery Execution Run & Orchestration Audit Ledger."""

    __tablename__ = "job_discovery_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(String(64), unique=True, nullable=False, index=True)
    source = Column(String(100), nullable=False)  # e.g. multi_source, greenhouse, lever
    criteria = Column(JSON, default=dict, nullable=False)  # SearchCriteria JSON payload
    total_discovered = Column(Integer, default=0, nullable=False)
    inserted_count = Column(Integer, default=0, nullable=False)
    duplicate_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="running", nullable=False)  # running, completed, partial, failed, fallback
    duration_ms = Column(Float, nullable=True)
    adapter_logs = Column(JSON, default=list, nullable=True)  # Detailed per-adapter metrics, errors, fallbacks


class JobSearchProfile(Base, TimestampMixin):
    """Saved Search Criteria Template Profile for Automated & On-Demand Discovery."""

    __tablename__ = "job_search_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    criteria = Column(JSON, default=dict, nullable=False)  # Search criteria configuration
    is_active = Column(Boolean, default=True, nullable=False)
    auto_run_interval_hours = Column(Integer, nullable=True)  # Optional scheduled interval
