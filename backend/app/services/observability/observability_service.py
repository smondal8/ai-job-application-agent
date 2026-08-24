import os
import platform
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("app.services.observability")


class ObservabilityService:
    """Enterprise Observability & Real-Time Performance Telemetry."""

    def __init__(self):
        self._start_time = time.time()
        self._counters: Dict[str, int] = {
            "requests_total": 0,
            "errors_total": 0,
            "approvals_granted": 0,
            "approvals_revoked": 0,
            "browser_preparations_executed": 0,
            "discovery_runs_total": 0,
            "resumes_tailored_total": 0,
            "backups_created": 0,
            "recoveries_executed": 0,
        }
        self._latencies: Dict[str, List[float]] = {}

    def increment(self, counter_name: str, amount: int = 1) -> None:
        """Increments a telemetry counter."""
        if counter_name in self._counters:
            self._counters[counter_name] += amount
        else:
            self._counters[counter_name] = amount

    @contextmanager
    def record_latency(self, operation: str):
        """Context manager tracking execution duration for a given operation."""
        start = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start) * 1000
            if operation not in self._latencies:
                self._latencies[operation] = []
            self._latencies[operation].append(duration_ms)
            # Keep rolling window of last 200 samples
            if len(self._latencies[operation]) > 200:
                self._latencies[operation] = self._latencies[operation][-200:]

    def get_metrics_snapshot(self, db: Optional[Session] = None) -> Dict[str, Any]:
        """Returns comprehensive observability telemetry snapshot."""
        uptime_seconds = time.time() - self._start_time
        settings = get_settings()

        latency_summary: Dict[str, Dict[str, float]] = {}
        for op, samples in self._latencies.items():
            if samples:
                sorted_samples = sorted(samples)
                p95_idx = int(len(sorted_samples) * 0.95)
                latency_summary[op] = {
                    "count": len(samples),
                    "avg_ms": round(sum(samples) / len(samples), 2),
                    "min_ms": round(min(samples), 2),
                    "max_ms": round(max(samples), 2),
                    "p95_ms": round(sorted_samples[min(p95_idx, len(samples) - 1)], 2),
                }

        db_healthy = False
        db_latency_ms = None
        if db:
            try:
                db_start = time.time()
                db.execute(text("SELECT 1")).scalar()
                db_latency_ms = round((time.time() - db_start) * 1000, 2)
                db_healthy = True
            except Exception as e:
                logger.warning(f"Database health check failed: {e}")
                db_healthy = False

        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "status": "healthy" if db_healthy or db is None else "degraded",
            "uptime_seconds": round(uptime_seconds, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "counters": self._counters,
            "latencies": latency_summary,
            "database": {
                "healthy": db_healthy,
                "latency_ms": db_latency_ms,
                "dialect": "sqlite" if settings.is_sqlite else "other",
            },
            "system": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "pid": os.getpid(),
                "llm_provider": settings.LLM_PROVIDER,
                "llm_model": settings.OLLAMA_MODEL,
            },
        }


observability_service = ObservabilityService()
