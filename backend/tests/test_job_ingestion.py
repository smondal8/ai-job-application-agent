from pathlib import Path
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.company import Company
from app.models.ingestion import JobIngestionBatch
from app.services.job_ingestion_service import job_ingestion_service


def test_ingest_json_fixture(db_session: Session):
    fixture_path = Path(__file__).parent.parent / "fixtures" / "jobs_sample.json"
    assert fixture_path.exists()
    
    json_text = fixture_path.read_text(encoding="utf-8")
    result = job_ingestion_service.ingest_json_text(
        db_session, json_text=json_text, source="fixture_json", filename="jobs_sample.json"
    )

    # Fixture contains 6 items: 5 unique + 1 exact duplicate
    assert result["total_records"] == 6
    assert result["inserted_count"] == 5
    assert result["duplicate_count"] == 1
    assert result["error_count"] == 0
    assert result["status"] == "completed"

    # Verify company normalization registry
    companies = db_session.query(Company).all()
    assert len(companies) >= 3
    company_names = {c.normalized_name for c in companies}
    assert "stripe" in company_names
    assert "google deepmind" in company_names
    assert "openai" in company_names

    # Verify batch ledger
    batch = db_session.query(JobIngestionBatch).filter(JobIngestionBatch.batch_id == result["batch_id"]).first()
    assert batch is not None
    assert batch.inserted_count == 5
    assert batch.duplicate_count == 1


def test_ingest_csv_fixture(db_session: Session):
    fixture_path = Path(__file__).parent.parent / "fixtures" / "jobs_sample.csv"
    assert fixture_path.exists()

    csv_text = fixture_path.read_text(encoding="utf-8")
    result = job_ingestion_service.ingest_csv_text(
        db_session, csv_text=csv_text, source="fixture_csv", filename="jobs_sample.csv"
    )

    # CSV has 4 items: 3 unique + 1 duplicate (Cloudflare SRE duplicate)
    assert result["total_records"] == 4
    assert result["inserted_count"] == 3
    assert result["duplicate_count"] == 1
    assert result["error_count"] == 0

    # Verify jobs in DB
    jobs = db_session.query(Job).all()
    assert len(jobs) >= 3
    sre_job = db_session.query(Job).filter(Job.normalized_title == "senior site reliability engineer").first()
    assert sre_job is not None
    assert sre_job.remote_type == "remote"


def test_ingestion_handles_malformed_records_without_crashing(db_session: Session):
    malformed_payload = [
        {"title": "Valid Job 1", "company": "Vercel", "location": "Remote"},
        {"location": "San Francisco, CA"},  # Missing title & company
        {"title": "Valid Job 2", "company": "Supabase", "location": "Remote"},
    ]

    result = job_ingestion_service.ingest_records(db_session, malformed_payload, source="test_feed")
    assert result["total_records"] == 3
    assert result["inserted_count"] == 2
    assert result["error_count"] == 1
    assert len(result["error_log"]) == 1
    assert "missing required title or company" in result["error_log"][0]["error"]
