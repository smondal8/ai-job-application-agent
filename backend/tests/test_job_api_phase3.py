from fastapi.testclient import TestClient


def test_job_ingest_json_and_csv_apis(client: TestClient):
    # 1. Ingest via JSON API
    json_payload = {
        "jobs": [
            {
                "title": "Staff AI Infrastructure Engineer",
                "company": "Anthropic",
                "location": "San Francisco, CA",
                "remote_type": "hybrid",
                "salary_min": 220000,
                "salary_max": 280000,
                "currency": "USD",
                "skills": ["Python", "PyTorch", "Kubernetes"],
            },
            {
                "title": "Frontend Engineer",
                "company": "Vercel",
                "location": "Remote",
                "remote_type": "remote",
                "salary_min": 140000,
                "salary_max": 180000,
                "currency": "USD",
                "skills": ["TypeScript", "Next.js", "React"],
            },
        ],
        "source": "api_test_json",
    }
    json_res = client.post("/api/v1/jobs/ingest/json", json=json_payload)
    assert json_res.status_code == 201
    json_batch = json_res.json()
    assert json_batch["inserted_count"] == 2
    assert json_batch["status"] == "completed"

    # 2. Ingest via CSV API
    csv_payload = {
        "csv_text": """title,company,location,remote_type,salary_min,salary_max
Founding Backend Engineer,Cursor,San Francisco, CA,on_site,180000,240000
AI Alignment Researcher,Anthropic,San Francisco, CA,hybrid,200000,260000
""",
        "source": "api_test_csv",
    }
    csv_res = client.post("/api/v1/jobs/ingest/csv", json=csv_payload)
    assert csv_res.status_code == 201
    csv_batch = csv_res.json()
    assert csv_batch["inserted_count"] == 2

    # 3. Test Seed Fixtures endpoint
    seed_res = client.post("/api/v1/jobs/ingest/seed-fixtures")
    assert seed_res.status_code == 200
    batches = seed_res.json()
    assert len(batches) >= 1

    # 4. Filter Jobs by remote_type and search
    filter_res = client.get("/api/v1/jobs?remote_type=remote")
    assert filter_res.status_code == 200
    remote_jobs = filter_res.json()
    assert remote_jobs["total"] >= 1
    assert all(j["remote_type"] == "remote" for j in remote_jobs["items"])

    # 5. List Companies Registry
    comp_res = client.get("/api/v1/companies")
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["total"] >= 2
    assert any(c["name"] == "Anthropic" or c["normalized_name"] == "anthropic" for c in comp_data["items"])

    # 6. List Ingestion Batches
    batches_res = client.get("/api/v1/jobs/ingest/batches")
    assert batches_res.status_code == 200
    assert batches_res.json()["total"] >= 2
