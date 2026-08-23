from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


def test_discovery_api_endpoints(client: TestClient):
    # 1. List adapters
    adapters_res = client.get("/api/v1/discovery/adapters")
    assert adapters_res.status_code == 200
    adapters = adapters_res.json()
    assert len(adapters) >= 4
    names = {a["source_name"] for a in adapters}
    assert "greenhouse" in names
    assert "protected_portal_fallback" in names

    # 2. Create Saved Search Profile
    profile_payload = {
        "name": "Senior Remote Python Roles",
        "description": "High-priority distributed backend searches",
        "criteria": {
            "keywords": ["Python", "FastAPI", "Distributed Systems"],
            "locations": ["San Francisco, CA", "Remote"],
            "remote_only": True,
            "target_companies": ["stripe", "openai", "anthropic"],
            "sources": ["greenhouse", "lever"],
        },
        "is_active": True,
        "auto_run_interval_hours": 12,
    }
    create_prof_res = client.post("/api/v1/discovery/search-profiles", json=profile_payload)
    assert create_prof_res.status_code == 201
    profile_data = create_prof_res.json()
    assert profile_data["id"] is not None
    profile_id = profile_data["id"]

    # 3. List Saved Search Profiles
    list_prof_res = client.get("/api/v1/discovery/search-profiles")
    assert list_prof_res.status_code == 200
    assert list_prof_res.json()["total"] >= 1

    # 4. Trigger on-demand discovery run with mocked adapter
    mock_gh_jobs = [
        {
            "external_id": "api-gh-1",
            "source": "greenhouse",
            "title": "Senior AI Systems Engineer",
            "company": "Anthropic",
            "location": "San Francisco, CA",
            "remote_type": "hybrid",
        }
    ]

    with patch("app.services.discovery.adapters.greenhouse.GreenhouseDiscoveryAdapter.fetch_jobs", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_gh_jobs

        run_payload = {
            "search_profile_id": profile_id,
            "source": "greenhouse",
        }
        run_res = client.post("/api/v1/discovery/run", json=run_payload)
        assert run_res.status_code == 201
        run_data = run_res.json()
        assert run_data["run_id"].startswith("disc_")
        assert run_data["total_discovered"] == 1
        assert run_data["inserted_count"] == 1
        run_id = run_data["run_id"]

        # 5. List Discovery Runs
        runs_list_res = client.get("/api/v1/discovery/runs")
        assert runs_list_res.status_code == 200
        assert runs_list_res.json()["total"] >= 1

        # 6. Get Discovery Run Detail
        run_detail_res = client.get(f"/api/v1/discovery/runs/{run_id}")
        assert run_detail_res.status_code == 200
        assert run_detail_res.json()["run_id"] == run_id

    # 7. Delete Search Profile
    del_prof_res = client.delete(f"/api/v1/discovery/search-profiles/{profile_id}")
    assert del_prof_res.status_code == 204
