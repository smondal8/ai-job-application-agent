import csv
from datetime import datetime, timezone
from decimal import Decimal
import io
import json
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.errors import BadRequestError
from app.core.logging import get_logger
from app.models.job import Job
from app.models.company import Company
from app.models.ingestion import JobIngestionBatch
from app.models.audit import AuditLog
from app.services.job_dedup_service import job_dedup_service

logger = get_logger("app.services.job_ingestion")


class JobIngestionService:
    """Normalized Job Ingestion Subsystem supporting JSON & CSV fixtures and feeds."""

    def _get_or_create_company(self, db: Session, raw_name: str) -> Optional[Company]:
        """Find or create normalized company entry in registry."""
        if not raw_name or not raw_name.strip():
            return None
        norm_name = job_dedup_service.normalize_company(raw_name)
        company = db.query(Company).filter(Company.normalized_name == norm_name).first()
        if not company:
            company = Company(
                name=raw_name.strip(),
                normalized_name=norm_name,
            )
            db.add(company)
            db.flush()
        return company

    def _parse_salary(self, val: Any) -> Optional[Decimal]:
        """Safely parse salary number from numeric or string input."""
        if val is None or val == "":
            return None
        if isinstance(val, (int, float, Decimal)):
            return Decimal(str(val))
        try:
            # Strip currency symbols and commas (e.g. "$150,000.00" -> "150000.00")
            cleaned = re.sub(r"[^\d.]", "", str(val).strip())
            return Decimal(cleaned) if cleaned else None
        except Exception:
            return None

    def _normalize_raw_dict(self, raw_item: Dict[str, Any], default_source: str = "json_import") -> Dict[str, Any]:
        """Map heterogeneous field name aliases to standard Job schema."""
        # Key aliases mapping
        title = (
            raw_item.get("title")
            or raw_item.get("job_title")
            or raw_item.get("position")
            or raw_item.get("role")
            or ""
        )
        company = (
            raw_item.get("company")
            or raw_item.get("company_name")
            or raw_item.get("employer")
            or ""
        )
        location = (
            raw_item.get("location")
            or raw_item.get("job_location")
            or raw_item.get("city")
            or raw_item.get("place")
        )
        url = (
            raw_item.get("url")
            or raw_item.get("link")
            or raw_item.get("job_url")
            or raw_item.get("apply_url")
        )
        description = (
            raw_item.get("description_raw")
            or raw_item.get("description")
            or raw_item.get("job_description")
            or raw_item.get("details")
            or raw_item.get("body")
        )
        external_id = (
            raw_item.get("external_id")
            or raw_item.get("id")
            or raw_item.get("job_id")
            or raw_item.get("req_id")
        )
        source = raw_item.get("source") or default_source

        # Remote / Workplace type
        remote_type = raw_item.get("remote_type") or raw_item.get("workplace_type") or "unspecified"
        if isinstance(remote_type, bool):
            remote_type = "remote" if remote_type else "on_site"
        elif str(remote_type).lower() in ["true", "1", "yes"]:
            remote_type = "remote"

        # Employment type
        job_type = raw_item.get("job_type") or raw_item.get("employment_type") or "full-time"

        # Salary parsing
        salary_min = self._parse_salary(raw_item.get("salary_min"))
        salary_max = self._parse_salary(raw_item.get("salary_max"))
        currency = raw_item.get("currency") or "USD"

        # Skills & Benefits
        skills_raw = raw_item.get("skills_raw") or raw_item.get("skills") or []
        if isinstance(skills_raw, str):
            skills_raw = [s.strip() for s in skills_raw.split(",") if s.strip()]

        benefits = raw_item.get("benefits") or []
        if isinstance(benefits, str):
            benefits = [b.strip() for b in benefits.split(",") if b.strip()]

        return {
            "title": str(title).strip(),
            "company": str(company).strip(),
            "location": str(location).strip() if location else None,
            "url": str(url).strip() if url else None,
            "description_raw": str(description) if description else None,
            "external_id": str(external_id).strip() if external_id else None,
            "source": str(source).strip(),
            "remote_type": str(remote_type).strip().lower(),
            "job_type": str(job_type).strip().lower(),
            "department": raw_item.get("department"),
            "seniority_level": raw_item.get("seniority_level"),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "currency": str(currency).strip().upper(),
            "skills_raw": skills_raw,
            "benefits": benefits,
            "metadata_extra": raw_item.get("metadata_extra") or {},
        }

    def ingest_records(
        self,
        db: Session,
        records: List[Dict[str, Any]],
        source: str = "json_import",
        filename: Optional[str] = None,
        file_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Core batch ingestion engine with conservative deduplication and audit tracking."""
        batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        now = datetime.now(timezone.utc)

        batch = JobIngestionBatch(
            batch_id=batch_id,
            source=source,
            filename=filename,
            file_hash=file_hash,
            total_records=len(records),
            status="processing",
        )
        db.add(batch)
        db.flush()

        inserted_jobs: List[Job] = []
        updated_jobs: List[Job] = []
        duplicate_count = 0
        error_log = []

        for idx, raw in enumerate(records):
            savepoint = db.begin_nested()
            try:
                norm_dict = self._normalize_raw_dict(raw, default_source=source)
                if not norm_dict["title"] or not norm_dict["company"]:
                    error_log.append({
                        "index": idx,
                        "error": "Record missing required title or company field.",
                        "record": str(raw)[:100],
                    })
                    savepoint.rollback()
                    continue

                # 1. Deduplication check
                existing_job = job_dedup_service.find_existing_duplicate(db, norm_dict)
                
                dedup_hash, norm_comp, norm_tit, norm_loc = job_dedup_service.compute_dedup_hash(
                    company=norm_dict["company"],
                    title=norm_dict["title"],
                    location=norm_dict.get("location"),
                    source=norm_dict.get("source", source),
                    external_id=norm_dict.get("external_id"),
                    url=norm_dict.get("url"),
                )

                # Find or register Company
                company_entity = self._get_or_create_company(db, norm_dict["company"])

                if existing_job:
                    # Conservative update: update timestamp, enrich empty fields
                    existing_job.last_seen_at = now
                    existing_job.is_active = True
                    if not existing_job.dedup_hash:
                        existing_job.dedup_hash = dedup_hash
                    if not existing_job.description_raw and norm_dict.get("description_raw"):
                        existing_job.description_raw = norm_dict["description_raw"]
                    if not existing_job.company_id and company_entity:
                        existing_job.company_id = company_entity.id
                    
                    duplicate_count += 1
                    updated_jobs.append(existing_job)
                    savepoint.commit()
                else:
                    # Create new normalized Job
                    new_job = Job(
                        external_id=norm_dict.get("external_id"),
                        company_id=company_entity.id if company_entity else None,
                        batch_id=batch_id,
                        title=norm_dict["title"],
                        company=norm_dict["company"],
                        location=norm_dict.get("location"),
                        department=norm_dict.get("department"),
                        dedup_hash=dedup_hash,
                        normalized_company=norm_comp,
                        normalized_title=norm_tit,
                        normalized_location=norm_loc,
                        remote_type=norm_dict.get("remote_type", "unspecified"),
                        workplace_type=norm_dict.get("remote_type", "unspecified"),
                        job_type=norm_dict.get("job_type", "full-time"),
                        employment_type=norm_dict.get("job_type", "full_time"),
                        seniority_level=norm_dict.get("seniority_level"),
                        url=norm_dict.get("url"),
                        source=norm_dict.get("source", source),
                        description_raw=norm_dict.get("description_raw"),
                        salary_min=norm_dict.get("salary_min"),
                        salary_max=norm_dict.get("salary_max"),
                        currency=norm_dict.get("currency", "USD"),
                        skills_raw=norm_dict.get("skills_raw", []),
                        benefits=norm_dict.get("benefits", []),
                        metadata_extra=norm_dict.get("metadata_extra", {}),
                        status="discovered",
                        is_active=True,
                        posted_at=now,
                        last_seen_at=now,
                    )
                    db.add(new_job)
                    db.flush()
                    inserted_jobs.append(new_job)
                    savepoint.commit()

            except Exception as exc:
                savepoint.rollback()
                logger.error("Error ingesting record %d: %s", idx, exc)
                error_log.append({"index": idx, "error": str(exc)})

        # Finalize batch metrics
        batch.inserted_count = len(inserted_jobs)
        batch.updated_count = len(updated_jobs)
        batch.duplicate_count = duplicate_count
        batch.error_count = len(error_log)
        batch.error_log = error_log
        batch.status = "completed" if not error_log or len(inserted_jobs) > 0 else "failed"

        # Log audit ledger
        audit = AuditLog(
            stage="job_ingestion",
            action="JOB_BATCH_INGESTED",
            level="info",
            message=f"Batch {batch_id}: inserted {len(inserted_jobs)}, duplicates {duplicate_count}, errors {len(error_log)}",
            payload={
                "batch_id": batch_id,
                "source": source,
                "filename": filename,
                "inserted": len(inserted_jobs),
                "duplicates": duplicate_count,
                "errors": len(error_log),
            },
        )
        db.add(audit)
        db.commit()

        return {
            "batch_id": batch_id,
            "source": source,
            "filename": filename,
            "total_records": len(records),
            "inserted_count": len(inserted_jobs),
            "updated_count": len(updated_jobs),
            "duplicate_count": duplicate_count,
            "error_count": len(error_log),
            "status": batch.status,
            "error_log": error_log,
        }

    def ingest_json_text(
        self,
        db: Session,
        json_text: str,
        source: str = "json_import",
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ingest from raw JSON string (object with 'jobs' array or direct array)."""
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise BadRequestError(f"Invalid JSON content: {exc}")

        if isinstance(data, dict):
            records = data.get("jobs") or data.get("items") or data.get("data") or [data]
        elif isinstance(data, list):
            records = data
        else:
            raise BadRequestError("JSON must be an array of jobs or an object containing a 'jobs' array.")

        return self.ingest_records(db=db, records=records, source=source, filename=filename)

    def ingest_csv_text(
        self,
        db: Session,
        csv_text: str,
        source: str = "csv_import",
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ingest from raw CSV formatted text."""
        try:
            reader = csv.DictReader(io.StringIO(csv_text.strip()))
            records = [dict(row) for row in reader]
        except Exception as exc:
            raise BadRequestError(f"Invalid CSV content: {exc}")

        if not records:
            raise BadRequestError("CSV file is empty or contains no data rows.")

        return self.ingest_records(db=db, records=records, source=source, filename=filename)


job_ingestion_service = JobIngestionService()
