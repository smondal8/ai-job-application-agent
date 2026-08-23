import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.schemas.discovery import SearchCriteria
from app.services.discovery.base import BaseJobDiscoveryAdapter
from app.services.discovery.adapters.greenhouse import GreenhouseDiscoveryAdapter
from app.services.discovery.adapters.lever import LeverDiscoveryAdapter
from app.services.discovery.adapters.protected_fallback import ProtectedPortalFallbackAdapter
from app.services.discovery.registry import discovery_registry


class MockCustomAdapter(BaseJobDiscoveryAdapter):
    source_name = "mock_test"
    display_name = "Mock Adapter"

    async def fetch_jobs(self, criteria: SearchCriteria):
        raw = [
            {"title": "Senior Python Backend Engineer", "company": "Stripe", "location": "San Francisco, CA", "remote_type": "hybrid", "salary_min": 180000},
            {"title": "Junior React Developer", "company": "Vercel", "location": "Remote", "remote_type": "remote", "salary_min": 110000},
            {"title": "Staff AI Researcher", "company": "Anthropic", "location": "London, UK", "remote_type": "on_site", "salary_min": 250000},
        ]
        return self.filter_by_criteria(raw, criteria)


@pytest.mark.asyncio
async def test_base_adapter_criteria_filtering():
    adapter = MockCustomAdapter()

    # 1. Filter by keyword & remote
    criteria_remote = SearchCriteria(keywords=["Python"], remote_only=False, locations=["San Francisco, CA"])
    jobs = await adapter.fetch_jobs(criteria_remote)
    assert len(jobs) == 1
    assert jobs[0]["company"] == "Stripe"

    # 2. Filter by min salary
    criteria_salary = SearchCriteria(keywords=["Engineer", "Researcher", "Developer"], min_salary=200000)
    jobs_salary = await adapter.fetch_jobs(criteria_salary)
    assert len(jobs_salary) == 1
    assert jobs_salary[0]["company"] == "Anthropic"


@pytest.mark.asyncio
async def test_greenhouse_adapter_parsing_and_html_cleaning():
    adapter = GreenhouseDiscoveryAdapter()
    
    mock_gh_response = {
        "jobs": [
            {
                "id": 9901,
                "title": "Senior Infrastructure Engineer",
                "absolute_url": "https://boards.greenhouse.io/stripe/jobs/9901",
                "location": {"name": "San Francisco, CA"},
                "departments": [{"name": "Core Platform"}],
                "content": "<p>We are looking for a <strong>Senior Engineer</strong> to scale our clusters.</p>",
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_gh_response

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        criteria = SearchCriteria(keywords=["Infrastructure"], target_companies=["stripe"])
        jobs = await adapter.fetch_jobs(criteria)

        assert len(jobs) == 1
        job = jobs[0]
        assert job["title"] == "Senior Infrastructure Engineer"
        assert job["company"] == "Stripe"
        assert job["external_id"] == "9901"
        assert "<p>" not in job["description_raw"]
        assert "Senior Engineer" in job["description_raw"]


@pytest.mark.asyncio
async def test_lever_adapter_parsing():
    adapter = LeverDiscoveryAdapter()

    mock_lever_response = [
        {
            "id": "lev-7788",
            "text": "Staff Distributed Systems Engineer",
            "hostedUrl": "https://jobs.lever.co/openai/lev-7788",
            "categories": {
                "location": "San Francisco, CA",
                "team": "Compute & Infrastructure",
                "commitment": "Full-time",
            },
            "descriptionPlain": "Build large distributed training clusters.",
        }
    ]

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_lever_response

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        criteria = SearchCriteria(keywords=["Distributed"], target_companies=["openai"])
        jobs = await adapter.fetch_jobs(criteria)

        assert len(jobs) == 1
        assert jobs[0]["title"] == "Staff Distributed Systems Engineer"
        assert jobs[0]["company"] == "Openai"
        assert jobs[0]["source"] == "lever"


@pytest.mark.asyncio
async def test_protected_portal_safe_manual_fallback():
    """Verify protected adapter NEVER bypasses protections and provides compliant manual URLs."""
    fallback_adapter = ProtectedPortalFallbackAdapter()
    criteria = SearchCriteria(keywords=["AI Engineer"], locations=["San Francisco, CA"], remote_only=True)

    # 1. Calling fetch_jobs returns 0 scraped records (no scraping attempts)
    jobs = await fallback_adapter.fetch_jobs(criteria)
    assert len(jobs) == 0

    # 2. Generates compliant search links
    links = fallback_adapter.get_fallback_links(criteria)
    assert len(links) >= 2
    assert any("linkedin.com/jobs/search" in item["url"] for item in links)
    assert any("indeed.com/jobs" in item["url"] for item in links)
    assert "AI+Engineer" in links[0]["url"]


def test_discovery_adapter_registry():
    adapters = discovery_registry.list_adapters()
    assert len(adapters) >= 4
    source_names = {a.source_name for a in adapters}
    assert "greenhouse" in source_names
    assert "lever" in source_names
    assert "remote_tech" in source_names
    assert "protected_portal_fallback" in source_names
