from fastapi.testclient import TestClient


def test_api_v1_config_endpoint(client: TestClient):
    response = client.get("/api/v1/config")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "AI Job Application Agent"
    assert data["environment"] == "testing"
    assert "pipeline_stages" in data
    assert len(data["pipeline_stages"]) == 6


def test_api_v1_pipeline_endpoint(client: TestClient):
    response = client.get("/api/v1/pipeline")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 6
    stage_ids = [s["stage_id"] for s in data]
    assert "core_foundation" in stage_ids
    assert "candidate_profile" in stage_ids
    assert "browser_preparation" in stage_ids


def test_job_crud_endpoints(client: TestClient):
    # 1. Create Job
    job_payload = {
        "title": "Platform Engineer",
        "company": "Stripe",
        "location": "Seattle, WA",
        "remote_type": "remote",
        "salary_min": "150000.00",
        "salary_max": "200000.00",
        "currency": "USD",
        "url": "https://stripe.com/jobs/123",
        "source": "manual",
        "status": "discovered",
    }
    create_res = client.post("/api/v1/jobs", json=job_payload)
    assert create_res.status_code == 201
    created_job = create_res.json()
    assert created_job["id"] is not None
    assert created_job["title"] == "Platform Engineer"
    job_id = created_job["id"]

    # 2. Get Job Details
    get_res = client.get(f"/api/v1/jobs/{job_id}")
    assert get_res.status_code == 200
    assert get_res.json()["company"] == "Stripe"

    # 3. List Jobs
    list_res = client.get("/api/v1/jobs")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert len(list_data["items"]) >= 1

    # 4. Search Filter
    search_res = client.get("/api/v1/jobs?search=Stripe")
    assert search_res.status_code == 200
    assert search_res.json()["total"] >= 1

    # 5. Delete Job
    del_res = client.delete(f"/api/v1/jobs/{job_id}")
    assert del_res.status_code == 204

    # 6. Verify 404 after delete
    get_del_res = client.get(f"/api/v1/jobs/{job_id}")
    assert get_del_res.status_code == 404


def test_resume_and_application_endpoints(client: TestClient):
    # 1. List resumes (empty initial)
    resumes_res = client.get("/api/v1/resumes")
    assert resumes_res.status_code == 200
    assert "items" in resumes_res.json()

    # 2. Create resume
    resume_payload = {
        "name": "Default Tech Resume",
        "version": "1.0",
        "skills": ["Python", "FastAPI", "React", "TypeScript"],
        "is_default": True,
    }
    create_resume_res = client.post("/api/v1/resumes", json=resume_payload)
    assert create_resume_res.status_code == 201
    resume_id = create_resume_res.json()["id"]

    # 3. Get resume
    get_resume_res = client.get(f"/api/v1/resumes/{resume_id}")
    assert get_resume_res.status_code == 200
    assert get_resume_res.json()["name"] == "Default Tech Resume"

    # 4. List applications (empty initial)
    apps_res = client.get("/api/v1/applications")
    assert apps_res.status_code == 200
    assert "items" in apps_res.json()
