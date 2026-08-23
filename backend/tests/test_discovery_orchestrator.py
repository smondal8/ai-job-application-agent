import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.discovery import JobDiscoveryRun, JobSearchProfile
from app.models.audit import AuditLog
from app.schemas.discovery import SearchCriteria
from app.services.discovery.orchestrator import discovery_orchestrator


@pytest.mark.asyncio
async def test_discovery_orchestrator_multi_source_execution(db_session: Session):
    # Mock Greenhouse and Lever adapter responses
    mock_gh_jobs = [
        {
            "external_id": "gh-101",
            "source": "greenhouse",
            "title": "Senior Backend Architect",
            "company": "Figma",
            "location": "San Francisco, CA",
            "url": "https://boards.greenhouse.io/figma/jobs/101",
            "description_raw": "Design scalable storage engines.",
            "remote_type": "hybrid",
        }
    ]
    mock_lever_jobs = [
        {
            "external_id": "lev-202",
            "source": "lever",
            "title": "Principal Distributed Systems Engineer",
            "company": "Netflix",
            "location": "Los Gatos, CA",
            "url": "https://jobs.lever.co/netflix/202",
            "description_raw": "Architect global streaming infrastructure.",
            "remote_type": "hybrid",
        }
    ]

    criteria = SearchCriteria(
        keywords=["Backend", "Distributed"],
        sources=["greenhouse", "lever", "protected_portal_fallback"],
    )

    with patch("app.services.discovery.adapters.greenhouse.GreenhouseDiscoveryAdapter.fetch_jobs", new_callable=AsyncMock) as mock_gh_fetch, \
         patch("app.services.discovery.adapters.lever.LeverDiscoveryAdapter.fetch_jobs", new_callable=AsyncMock) as mock_lever_fetch:
        
        mock_gh_fetch.return_value = mock_gh_jobs
        mock_lever_fetch.return_value = mock_lever_jobs

        run_record = await discovery_orchestrator.execute_discovery_run(
            db=db_session,
            criteria=criteria,
        )

        assert run_record.status == "completed"
        assert run_record.total_discovered == 2
        assert run_record.inserted_count == 2
        assert run_record.duplicate_count == 0
        assert len(run_record.adapter_logs) == 3

        # Verify jobs were ingested into the jobs database
        jobs = db_session.query(Job).all()
        assert len(jobs) >= 2
        titles = {j.title for j in jobs}
        assert "Senior Backend Architect" in titles
        assert "Principal Distributed Systems Engineer" in titles

        # Verify audit ledger
        audit = db_session.query(AuditLog).filter(AuditLog.action == "DISCOVERY_RUN_COMPLETED").first()
        assert audit is not None
        assert run_record.run_id in audit.message


@pytest.mark.asyncio
async def test_discovery_orchestrator_partial_failure_resilience(db_session: Session):
    """If one adapter raises an exception, the orchestrator should gracefully record 'partial' status."""
    mock_lever_jobs = [
        {
            "external_id": "lev-303",
            "source": "lever",
            "title": "Staff Platform Security Engineer",
            "company": "Spotify",
            "location": "New York, NY",
        }
    ]

    with patch("app.services.discovery.adapters.greenhouse.GreenhouseDiscoveryAdapter.fetch_jobs", new_callable=AsyncMock) as mock_gh_fetch, \
         patch("app.services.discovery.adapters.lever.LeverDiscoveryAdapter.fetch_jobs", new_callable=AsyncMock) as mock_lever_fetch:
        
        # Greenhouse adapter fails
        mock_gh_fetch.side_effect = Exception("Rate limit exceeded / Timeout")
        mock_lever_fetch.return_value = mock_lever_jobs

        criteria = SearchCriteria(sources=["greenhouse", "lever"])

        run_record = await discovery_orchestrator.execute_discovery_run(
            db=db_session,
            criteria=criteria,
        )

        assert run_record.status == "partial"
        assert run_record.total_discovered == 1
        assert run_record.inserted_count == 1
        assert run_record.error_count == 1

        # Confirm Spotify job was still successfully saved in DB
        spotify_job = db_session.query(Job).filter(Job.company == "Spotify").first()
        assert spotify_job is not None
