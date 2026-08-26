import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.application import Application
from app.models.analysis import JobAnalysis


def test_job_archive_and_reject_lifecycle(client: TestClient, db_session: Session):
    # 1. Ingest test jobs
    payload = {
        "jobs": [
            {
                "title": "Senior Distributed Systems Engineer",
                "company": "Temporal",
                "location": "Remote",
                "remote_type": "remote",
                "seniority_level": "senior",
                "salary_min": 180000,
                "salary_max": 230000,
                "currency": "USD",
                "url": "https://temporal.io/careers/101",
            },
            {
                "title": "Junior QA Specialist",
                "company": "IrrelevantCorp",
                "location": "On-Site",
                "remote_type": "on_site",
                "seniority_level": "entry",
                "salary_min": 50000,
                "salary_max": 65000,
                "currency": "USD",
                "url": "https://irrelevant.com/careers/202",
            },
        ],
        "source": "lifecycle_test",
    }
    ingest_res = client.post("/api/v1/jobs/ingest/json", json=payload)
    assert ingest_res.status_code == 201

    # Fetch both jobs
    list_active = client.get("/api/v1/jobs")
    assert list_active.status_code == 200
    active_items = list_active.json()["items"]
    temporal_job = next(j for j in active_items if j["company"] == "Temporal")
    irrelevant_job = next(j for j in active_items if j["company"] == "IrrelevantCorp")

    # 2. User marks IrrelevantCorp job as rejected / Not Relevant
    reject_res = client.post(f"/api/v1/jobs/{irrelevant_job['id']}/reject")
    assert reject_res.status_code == 200
    rejected_data = reject_res.json()
    assert rejected_data["status"] == "rejected"
    assert rejected_data["is_active"] is False

    # 3. User marks Temporal job as archived
    archive_res = client.post(f"/api/v1/jobs/{temporal_job['id']}/archive")
    assert archive_res.status_code == 200
    archived_data = archive_res.json()
    assert archived_data["status"] == "archived"
    assert archived_data["is_active"] is False

    # 4. Verify BOTH are excluded from default active list
    list_active_after = client.get("/api/v1/jobs")
    assert list_active_after.status_code == 200
    active_ids = [j["id"] for j in list_active_after.json()["items"]]
    assert irrelevant_job["id"] not in active_ids
    assert temporal_job["id"] not in active_ids

    # 5. Verify they can be viewed via status filter or is_active=false
    list_archived = client.get("/api/v1/jobs?status=archived")
    assert list_archived.status_code == 200
    archived_ids = [j["id"] for j in list_archived.json()["items"]]
    assert temporal_job["id"] in archived_ids

    list_rejected = client.get("/api/v1/jobs?status=rejected")
    assert list_rejected.status_code == 200
    rejected_ids = [j["id"] for j in list_rejected.json()["items"]]
    assert irrelevant_job["id"] in rejected_ids

    list_inactive = client.get("/api/v1/jobs?is_active=false")
    assert list_inactive.status_code == 200
    inactive_ids = [j["id"] for j in list_inactive.json()["items"]]
    assert temporal_job["id"] in inactive_ids
    assert irrelevant_job["id"] in inactive_ids

    # 6. User restores Temporal job
    restore_res = client.post(f"/api/v1/jobs/{temporal_job['id']}/restore")
    assert restore_res.status_code == 200
    restored_data = restore_res.json()
    assert restored_data["is_active"] is True
    assert restored_data["status"] in ["discovered", "analyzed"]

    # Verify Temporal job is back in active list, but IrrelevantCorp remains rejected
    list_active_final = client.get("/api/v1/jobs")
    final_active_ids = [j["id"] for j in list_active_final.json()["items"]]
    assert temporal_job["id"] in final_active_ids
    assert irrelevant_job["id"] not in final_active_ids


def test_rediscovery_preserves_rejected_and_archived_decisions(client: TestClient, db_session: Session):
    # 1. First discovery / ingestion of a job with partial info
    initial_job_payload = {
        "jobs": [
            {
                "title": "Staff Backend Engineer",
                "company": "RediscoveryCo",
                "location": "Bangalore, India",
                "remote_type": "hybrid",
                "url": "https://rediscoveryco.com/jobs/999",
            }
        ],
        "source": "discovery_greenhouse",
    }
    res1 = client.post("/api/v1/jobs/ingest/json", json=initial_job_payload)
    assert res1.status_code == 201
    assert res1.json()["inserted_count"] == 1

    # Get the created job ID
    db_job = db_session.query(Job).filter(Job.company == "RediscoveryCo").first()
    assert db_job is not None
    job_id = db_job.id

    # 2. User marks the job as rejected / Not Relevant
    rej_res = client.post(f"/api/v1/jobs/{job_id}/reject")
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "rejected"
    assert rej_res.json()["is_active"] is False

    # 3. Next day: Discovery runs again and finds the EXACT same job with enriched description & salary
    rediscovered_payload = {
        "jobs": [
            {
                "title": "Staff Backend Engineer",
                "company": "RediscoveryCo",
                "location": "Bangalore, India",
                "remote_type": "hybrid",
                "url": "https://rediscoveryco.com/jobs/999",
                "description_raw": "Updated extended description with more details about platform architecture",
                "salary_min": 160000,
                "salary_max": 210000,
            }
        ],
        "source": "discovery_greenhouse",
    }
    res2 = client.post("/api/v1/jobs/ingest/json", json=rediscovered_payload)
    assert res2.status_code == 201
    batch2 = res2.json()
    assert batch2["inserted_count"] == 0
    assert batch2["duplicate_count"] == 1  # recognized existing job

    # 4. Verify the job REMAINS rejected and NOT active
    db_session.expire_all()
    db_job_updated = db_session.query(Job).filter(Job.id == job_id).first()
    assert db_job_updated is not None
    assert db_job_updated.status == "rejected"
    assert db_job_updated.is_active is False

    # 5. Verify metadata was enriched without overriding user's rejection
    assert db_job_updated.description_raw == "Updated extended description with more details about platform architecture"
    assert db_job_updated.salary_min == 160000

    # 6. Verify default active jobs API still does NOT show this rejected job
    active_res = client.get("/api/v1/jobs")
    active_ids = [j["id"] for j in active_res.json()["items"]]
    assert job_id not in active_ids


def test_delete_protection_for_active_applications(client: TestClient, db_session: Session):
    # 1. Create a job
    job = Job(
        title="Principal Platform Engineer",
        company="SecureCorp",
        location="Remote",
        status="discovered",
        is_active=True,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    # 2. Attach an active application
    app = Application(
        job_id=job.id,
        status="applied",
        portal_type="greenhouse",
    )
    db_session.add(app)
    db_session.commit()

    # 3. Attempt hard delete -> must fail with 400 Bad Request
    del_res = client.delete(f"/api/v1/jobs/{job.id}")
    assert del_res.status_code == 400
    assert "Cannot delete job with active applications" in del_res.json()["error"]["message"]

    # 4. Job can still be safely archived
    arch_res = client.post(f"/api/v1/jobs/{job.id}/archive")
    assert arch_res.status_code == 200
    assert arch_res.json()["status"] == "archived"
    assert arch_res.json()["is_active"] is False


def test_jd_analysis_preserved_on_rejected_job(client: TestClient, db_session: Session):
    # 1. Create and analyze a job
    job = Job(
        title="Senior Security Engineer",
        company="LockBox",
        location="Remote",
        status="analyzed",
        is_active=True,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    analysis = JobAnalysis(
        job_id=job.id,
        fit_score=35.0,
        deterministic_score=40.0,
        semantic_score=30.0,
        recommendation="stretch",
        summary="Low alignment with candidate background.",
        matched_skills=["Python"],
        missing_skills=["Rust", "Cryptography", "Kernel Security"],
    )
    db_session.add(analysis)
    db_session.commit()

    # 2. User reviews low match score (35%) and clicks "Not Relevant / Skip"
    skip_res = client.post(f"/api/v1/jobs/{job.id}/reject")
    assert skip_res.status_code == 200
    assert skip_res.json()["status"] == "rejected"
    assert skip_res.json()["is_active"] is False

    # 3. Verify analysis record is still intact and accessible for audit
    analysis_res = client.get(f"/api/v1/jobs/{job.id}/analysis")
    assert analysis_res.status_code == 200
    analysis_data = analysis_res.json()
    assert analysis_data["fit_score"] == 35.0
    assert analysis_data["recommendation"] == "stretch"
    assert "Rust" in analysis_data["missing_skills"]
