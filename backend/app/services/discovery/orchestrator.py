import asyncio
from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.discovery import JobDiscoveryRun, JobSearchProfile
from app.models.audit import AuditLog
from app.schemas.discovery import SearchCriteria
from app.services.discovery.registry import discovery_registry
from app.services.discovery.adapters.protected_fallback import ProtectedPortalFallbackAdapter
from app.services.job_ingestion_service import job_ingestion_service

logger = get_logger("app.services.discovery.orchestrator")


class DiscoveryOrchestrationService:
    """Source-Agnostic Job Discovery Orchestration Engine."""

    async def execute_discovery_run(
        self,
        db: Session,
        criteria: Optional[SearchCriteria] = None,
        specific_source: Optional[str] = None,
        search_profile_id: Optional[int] = None,
    ) -> JobDiscoveryRun:
        """Execute on-demand discovery across registered adapters and ingest results."""
        start_time = time.time()
        now = datetime.now(timezone.utc)

        # 1. Resolve search criteria
        if search_profile_id:
            profile = db.query(JobSearchProfile).filter(JobSearchProfile.id == search_profile_id).first()
            if profile and profile.criteria:
                criteria = SearchCriteria(**profile.criteria)
        
        if not criteria:
            criteria = SearchCriteria()

        run_id = f"disc_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        source_label = specific_source if specific_source else "multi_source"

        run_record = JobDiscoveryRun(
            run_id=run_id,
            source=source_label,
            criteria=criteria.model_dump(),
            total_discovered=0,
            inserted_count=0,
            duplicate_count=0,
            error_count=0,
            status="running",
            adapter_logs=[],
        )
        db.add(run_record)
        db.flush()

        # 2. Determine target adapters
        adapters_to_run = []
        if specific_source:
            adapter = discovery_registry.get_adapter(specific_source)
            if adapter:
                adapters_to_run.append(adapter)
        else:
            for s in criteria.sources:
                ad = discovery_registry.get_adapter(s)
                if ad:
                    adapters_to_run.append(ad)

        if not adapters_to_run:
            # Fallback to all reliable adapters
            adapters_to_run = list(discovery_registry.get_all_adapters().values())

        total_discovered = 0
        total_inserted = 0
        total_duplicates = 0
        total_errors = 0
        adapter_logs: List[Dict[str, Any]] = []

        # 3. Execute adapters
        for adapter in adapters_to_run:
            adapter_start = time.time()
            try:
                # Handle safe protected fallback adapter
                if isinstance(adapter, ProtectedPortalFallbackAdapter):
                    fallback_links = adapter.get_fallback_links(criteria)
                    adapter_logs.append({
                        "adapter": adapter.source_name,
                        "status": "manual_fallback_recommended",
                        "discovered_count": 0,
                        "fallback_links": fallback_links,
                        "duration_ms": round((time.time() - adapter_start) * 1000, 2),
                    })
                    continue

                # Fetch jobs from reliable adapter
                raw_jobs = await adapter.fetch_jobs(criteria)
                total_discovered += len(raw_jobs)

                if raw_jobs:
                    # Ingest discovered jobs via Phase 3 Ingestion Subsystem
                    ingest_res = job_ingestion_service.ingest_records(
                        db=db,
                        records=raw_jobs,
                        source=f"discovery_{adapter.source_name}",
                    )
                    total_inserted += ingest_res.get("inserted_count", 0)
                    total_duplicates += ingest_res.get("duplicate_count", 0)
                    total_errors += ingest_res.get("error_count", 0)

                    adapter_logs.append({
                        "adapter": adapter.source_name,
                        "status": "success",
                        "discovered_count": len(raw_jobs),
                        "inserted_count": ingest_res.get("inserted_count", 0),
                        "duplicate_count": ingest_res.get("duplicate_count", 0),
                        "error_count": ingest_res.get("error_count", 0),
                        "duration_ms": round((time.time() - adapter_start) * 1000, 2),
                    })
                else:
                    adapter_logs.append({
                        "adapter": adapter.source_name,
                        "status": "no_matching_jobs",
                        "discovered_count": 0,
                        "duration_ms": round((time.time() - adapter_start) * 1000, 2),
                    })

            except Exception as exc:
                logger.error("Adapter '%s' execution failed: %s", adapter.source_name, exc)
                total_errors += 1
                adapter_logs.append({
                    "adapter": adapter.source_name,
                    "status": "error",
                    "error": str(exc),
                    "duration_ms": round((time.time() - adapter_start) * 1000, 2),
                })

        # 4. Finalize run record
        duration_ms = round((time.time() - start_time) * 1000, 2)
        run_record.total_discovered = total_discovered
        run_record.inserted_count = total_inserted
        run_record.duplicate_count = total_duplicates
        run_record.error_count = total_errors
        run_record.duration_ms = duration_ms
        run_record.adapter_logs = adapter_logs

        if total_errors == len(adapters_to_run):
            run_record.status = "failed"
        elif total_errors > 0:
            run_record.status = "partial"
        else:
            run_record.status = "completed"

        # 5. Audit Log
        audit = AuditLog(
            stage="job_discovery",
            action="DISCOVERY_RUN_COMPLETED",
            level="info" if run_record.status == "completed" else "warning",
            message=f"Discovery run {run_id} ({source_label}): discovered {total_discovered}, inserted {total_inserted}, duplicates {total_duplicates}",
            payload={
                "run_id": run_id,
                "sources": [a.source_name for a in adapters_to_run],
                "status": run_record.status,
                "duration_ms": duration_ms,
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(run_record)

        return run_record


discovery_orchestrator = DiscoveryOrchestrationService()
