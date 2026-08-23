from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class DatabaseHealth(BaseModel):
    """Health check details for SQLite database subsystem."""
    status: str = Field(..., examples=["healthy"])
    connected: bool = Field(..., examples=[True])
    latency_ms: float = Field(..., examples=[1.25])
    dialect: str = Field(..., examples=["sqlite"])
    database_target: Optional[str] = Field(None, examples=["/path/to/job_agent.db"])
    error: Optional[str] = Field(None)


class StorageHealth(BaseModel):
    """Health check details for local storage subsystem."""
    status: str = Field(..., examples=["healthy"])
    storage_dir: str = Field(..., examples=["./data/storage"])
    writable: bool = Field(..., examples=[True])
    error: Optional[str] = Field(None)


class HealthResponse(BaseModel):
    """Comprehensive health check response."""
    status: str = Field("healthy", examples=["healthy"])
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = Field(..., examples=["0.1.0"])
    uptime_seconds: float = Field(..., examples=[120.45])
    environment: str = Field(..., examples=["development"])
    database: DatabaseHealth
    storage: StorageHealth


class ReadinessResponse(BaseModel):
    """Readiness probe response for traffic gating."""
    ready: bool = Field(..., examples=[True])
    status: str = Field(..., examples=["ready"])
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    checks: Dict[str, bool] = Field(
        ...,
        examples=[{"database": True, "storage": True}]
    )


class LivenessResponse(BaseModel):
    """Minimal liveness probe response."""
    status: str = "alive"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
