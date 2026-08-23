from sqlalchemy.orm import Session
from app.services.job_dedup_service import job_dedup_service
from app.services.job_ingestion_service import job_ingestion_service
from app.models.job import Job


def test_url_canonicalization_and_deduplication():
    url_with_tracking = "https://jobs.lever.co/stripe/abc-123?utm_source=linkedin&utm_campaign=summer&ref=feed"
    clean_url = job_dedup_service.normalize_url(url_with_tracking)
    assert clean_url == "https://jobs.lever.co/stripe/abc-123"
    assert "utm_source" not in clean_url
    assert "ref" not in clean_url


def test_company_normalization():
    assert job_dedup_service.normalize_company("Google, Inc.") == "google"
    assert job_dedup_service.normalize_company("Stripe LLC") == "stripe"
    assert job_dedup_service.normalize_company("Databricks Corporation") == "databricks"
    assert job_dedup_service.normalize_company("Cloudflare Technologies Ltd.") == "cloudflare"


def test_exact_duplicate_by_external_id_and_source(db_session: Session):
    record_1 = {
        "external_id": "req-999",
        "source": "greenhouse",
        "title": "Platform Engineer",
        "company": "Figma",
        "location": "San Francisco, CA",
    }
    record_2 = {
        "external_id": "req-999",
        "source": "greenhouse",
        "title": "Platform Engineer",
        "company": "Figma Inc",
        "location": "San Francisco, CA",
        "description": "Updated enriched description from feed.",
    }

    res_1 = job_ingestion_service.ingest_records(db_session, [record_1], source="greenhouse")
    assert res_1["inserted_count"] == 1
    assert res_1["duplicate_count"] == 0

    res_2 = job_ingestion_service.ingest_records(db_session, [record_2], source="greenhouse")
    assert res_2["inserted_count"] == 0
    assert res_2["duplicate_count"] == 1

    # Total jobs in database must remain 1
    jobs = db_session.query(Job).filter(Job.external_id == "req-999").all()
    assert len(jobs) == 1
    assert jobs[0].description_raw == "Updated enriched description from feed."


def test_conservative_deduplication_preserves_distinct_locations(db_session: Session):
    """Conservative Rule: Same company and title in different locations are DISTINCT jobs."""
    jobs_payload = [
        {
            "title": "Senior Distributed Systems Engineer",
            "company": "OpenAI",
            "location": "San Francisco, CA",
        },
        {
            "title": "Senior Distributed Systems Engineer",
            "company": "OpenAI",
            "location": "London, UK",
        },
        {
            "title": "Senior Distributed Systems Engineer",
            "company": "OpenAI",
            "location": "Tokyo, Japan",
        },
    ]

    res = job_ingestion_service.ingest_records(db_session, jobs_payload, source="json_import")
    assert res["inserted_count"] == 3
    assert res["duplicate_count"] == 0

    jobs = db_session.query(Job).filter(Job.company == "OpenAI").all()
    assert len(jobs) == 3
    locations = {j.location for j in jobs}
    assert locations == {"San Francisco, CA", "London, UK", "Tokyo, Japan"}


def test_conservative_deduplication_preserves_distinct_seniorities(db_session: Session):
    """Conservative Rule: Different seniority levels (e.g. Senior vs Staff vs Principal) are NEVER discarded."""
    jobs_payload = [
        {
            "title": "Software Engineer II - Payments",
            "company": "Stripe",
            "location": "Seattle, WA",
            "seniority_level": "mid",
        },
        {
            "title": "Senior Software Engineer - Payments",
            "company": "Stripe",
            "location": "Seattle, WA",
            "seniority_level": "senior",
        },
        {
            "title": "Staff Software Engineer - Payments",
            "company": "Stripe",
            "location": "Seattle, WA",
            "seniority_level": "staff",
        },
    ]

    res = job_ingestion_service.ingest_records(db_session, jobs_payload, source="json_import")
    assert res["inserted_count"] == 3
    assert res["duplicate_count"] == 0

    jobs = db_session.query(Job).filter(Job.company == "Stripe").all()
    assert len(jobs) == 3


def test_conservative_deduplication_preserves_distinct_departments(db_session: Session):
    """Conservative Rule: Same title across different teams/departments are distinct positions."""
    jobs_payload = [
        {
            "title": "Engineering Manager - Machine Learning Core",
            "company": "Anthropic",
            "location": "San Francisco, CA",
        },
        {
            "title": "Engineering Manager - Security & Governance",
            "company": "Anthropic",
            "location": "San Francisco, CA",
        },
    ]

    res = job_ingestion_service.ingest_records(db_session, jobs_payload, source="json_import")
    assert res["inserted_count"] == 2
    assert res["duplicate_count"] == 0
