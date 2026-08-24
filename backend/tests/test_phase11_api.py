from fastapi.testclient import TestClient


def test_system_metrics_endpoint(client: TestClient):
    res = client.get("/api/v1/system/metrics")
    assert res.status_code == 200
    data = res.json()

    assert "service" in data
    assert "status" in data
    assert "uptime_seconds" in data
    assert "counters" in data
    assert "database" in data
    assert data["database"]["healthy"] is True


def test_system_recover_stale_endpoint(client: TestClient):
    res = client.post("/api/v1/system/recover-stale?max_age_minutes=15")
    assert res.status_code == 200
    data = res.json()

    assert "reconciled_discovery_runs" in data
    assert "reconciled_preparation_runs" in data
    assert "total_recovered" in data


def test_system_backups_lifecycle_api(client: TestClient):
    # 1. Create backup
    create_res = client.post("/api/v1/system/backups?include_artifacts=false")
    assert create_res.status_code == 201
    backup_data = create_res.json()
    assert "backup_id" in backup_data

    backup_id = backup_data["backup_id"]

    # 2. List backups
    list_res = client.get("/api/v1/system/backups")
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(b["backup_id"] == backup_id for b in items)

    # 3. Verify backup
    verify_res = client.post(f"/api/v1/system/backups/{backup_id}/verify")
    assert verify_res.status_code == 200
    assert verify_res.json()["is_valid"] is True

    # 4. Restore backup
    restore_res = client.post(f"/api/v1/system/backups/{backup_id}/restore")
    assert restore_res.status_code == 200
    assert restore_res.json()["status"] == "restored"


def test_system_redaction_endpoint(client: TestClient):
    payload = {
        "user_email": "candidate@example.com",
        "api_key": "sk-1234567890abcdef1234567890",
        "secret_token": "Bearer my_super_secret_token",
    }
    res = client.post("/api/v1/system/redact", json=payload)
    assert res.status_code == 200
    redacted = res.json()

    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["secret_token"] == "[REDACTED]"
    assert redacted["user_email"] == "candidate@example.com"
