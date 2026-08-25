import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session

from app.schemas.discovery import SearchCriteria
from app.services.discovery.base import BaseJobDiscoveryAdapter
from app.services.discovery.adapters.greenhouse import GreenhouseDiscoveryAdapter
from app.services.discovery.adapters.lever import LeverDiscoveryAdapter
from app.services.discovery.adapters.remote_tech import RemoteTechDiscoveryAdapter
from app.services.discovery.orchestrator import discovery_orchestrator
from app.models.job import Job
from app.models.ingestion import JobIngestionBatch
from app.models.audit import AuditLog


class MockMultiLocationAdapter(BaseJobDiscoveryAdapter):
    source_name = "mock_india_test"
    display_name = "Mock India Adapter"

    async def fetch_jobs(self, criteria: SearchCriteria):
        raw = [
            {
                "external_id": "job-blr-1",
                "title": "Senior Backend Engineer (Java)",
                "company": "PhonePe",
                "location": "Bengaluru, Karnataka, India",
                "remote_type": "on_site",
                "salary_min": 3500000,
                "description_raw": "Looking for Senior Engineer with Java and Spring Boot experience.",
            },
            {
                "external_id": "job-blr-2",
                "title": "Staff Distributed Systems Architect",
                "company": "Okta",
                "location": "Bangalore",
                "remote_type": "hybrid",
                "salary_min": 4500000,
                "description_raw": "Design distributed microservices.",
            },
            {
                "external_id": "job-blr-3",
                "title": "Principal Java Developer",
                "company": "Rubrik",
                "location": "BLR Office",
                "remote_type": "on_site",
                "salary_min": 5000000,
                "description_raw": "Core platform Java development.",
            },
            {
                "external_id": "job-in-4",
                "title": "Lead Software Engineer",
                "company": "Stripe",
                "location": "India (Remote)",
                "remote_type": "remote",
                "salary_min": 4000000,
                "description_raw": "Distributed payment processing in Java and Go.",
            },
            {
                "external_id": "job-rem-5",
                "title": "Senior Cloud Engineer",
                "company": "GitLab",
                "location": "Remote - Worldwide",
                "remote_type": "remote",
                "salary_min": 150000,
                "description_raw": "Infrastructure automation.",
            },
            {
                "external_id": "job-sf-6",
                "title": "Staff Backend Engineer",
                "company": "OpenAI",
                "location": "San Francisco, CA",
                "remote_type": "on_site",
                "salary_min": 250000,
                "description_raw": "AI Platform.",
            },
            {
                "external_id": "job-lon-7",
                "title": "Senior Platform Engineer",
                "company": "DeepMind",
                "location": "London, UK",
                "remote_type": "hybrid",
                "salary_min": 140000,
                "description_raw": "Autonomous agent compute.",
            },
        ]
        return self.filter_by_criteria(raw, criteria)


@pytest.mark.asyncio
async def test_bangalore_matches_bengaluru():
    """Verify searching 'Bangalore' matches listings with 'Bengaluru'."""
    adapter = MockMultiLocationAdapter()
    criteria = SearchCriteria(keywords=["Backend"], locations=["Bangalore"], remote_only=False)
    jobs = await adapter.fetch_jobs(criteria)

    assert len(jobs) >= 1
    companies = [j["company"] for j in jobs]
    assert "PhonePe" in companies  # Location is 'Bengaluru, Karnataka, India'


@pytest.mark.asyncio
async def test_bengaluru_matches_bangalore():
    """Verify searching 'Bengaluru' matches listings with 'Bangalore'."""
    adapter = MockMultiLocationAdapter()
    criteria = SearchCriteria(keywords=["Distributed"], locations=["Bengaluru"], remote_only=False)
    jobs = await adapter.fetch_jobs(criteria)

    assert len(jobs) >= 1
    assert any(j["company"] == "Okta" for j in jobs)  # Location is 'Bangalore'


@pytest.mark.asyncio
async def test_bangalore_matches_india_and_blr():
    """Verify searching 'Bangalore' matches 'BLR Office' and 'India' listings."""
    adapter = MockMultiLocationAdapter()
    criteria = SearchCriteria(keywords=["Java", "Developer"], locations=["Bangalore"], remote_only=False)
    jobs = await adapter.fetch_jobs(criteria)

    companies = [j["company"] for j in jobs]
    assert "Rubrik" in companies  # Location: BLR Office
    assert "PhonePe" in companies  # Location: Bengaluru, Karnataka, India


@pytest.mark.asyncio
async def test_remote_matches_remote_worldwide():
    """Verify searching 'Remote' matches Remote Worldwide and India Remote."""
    adapter = MockMultiLocationAdapter()
    criteria = SearchCriteria(keywords=["Engineer"], locations=["Remote"], remote_only=True)
    jobs = await adapter.fetch_jobs(criteria)

    companies = [j["company"] for j in jobs]
    assert "GitLab" in companies
    assert "Stripe" in companies
    assert "PhonePe" not in companies  # On-site PhonePe should NOT match remote_only
    assert "DeepMind" not in companies  # Hybrid London should NOT match remote_only


@pytest.mark.asyncio
async def test_non_matching_locations_excluded():
    """Verify searches for Bangalore/India do not leak San Francisco or London on-site roles."""
    adapter = MockMultiLocationAdapter()
    criteria = SearchCriteria(keywords=["Backend", "Platform", "Engineer"], locations=["Bangalore"], remote_only=False)
    jobs = await adapter.fetch_jobs(criteria)

    companies = [j["company"] for j in jobs]
    assert "OpenAI" not in companies  # San Francisco, CA
    assert "DeepMind" not in companies  # London, UK


@pytest.mark.asyncio
async def test_source_distinction_and_ingestion_pipeline(db_session: Session):
    """Verify discovery jobs are ingested with source='discovery_<adapter>' and distinct from fixture_seed."""
    mock_gh_jobs = [
        {
            "external_id": "gh-india-test-100",
            "source": "discovery_greenhouse",
            "title": "Senior Java Backend Engineer",
            "company": "PhonePe",
            "location": "Bengaluru, India",
            "url": "https://job-boards.greenhouse.io/phonepe/jobs/100",
            "description_raw": "Spring Boot and Distributed Systems.",
            "remote_type": "on_site",
            "job_type": "full-time",
        }
    ]

    with patch.object(GreenhouseDiscoveryAdapter, "fetch_jobs", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_gh_jobs

        criteria = SearchCriteria(keywords=["Java"], locations=["Bengaluru"], sources=["greenhouse"])
        run = await discovery_orchestrator.execute_discovery_run(
            db=db_session,
            criteria=criteria,
            specific_source="greenhouse",
        )

        assert run.status == "completed"
        assert run.total_discovered == 1
        assert run.inserted_count == 1
        assert run.duplicate_count == 0

        # Check job in database
        saved_job = db_session.query(Job).filter(Job.external_id == "gh-india-test-100").first()
        assert saved_job is not None
        assert saved_job.title == "Senior Java Backend Engineer"
        assert saved_job.source == "discovery_greenhouse"
        assert saved_job.source != "fixture_seed_json"
        assert saved_job.source != "fixture_seed_csv"
        assert saved_job.url == "https://job-boards.greenhouse.io/phonepe/jobs/100"

        # Re-running same discovery tests deduplication
        run2 = await discovery_orchestrator.execute_discovery_run(
            db=db_session,
            criteria=criteria,
            specific_source="greenhouse",
        )
        assert run2.status == "completed"
        assert run2.inserted_count == 0
        assert run2.duplicate_count == 1
