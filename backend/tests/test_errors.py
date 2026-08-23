from fastapi.testclient import TestClient


def test_404_error_contract(client: TestClient):
    response = client.get("/api/v1/non_existent_route")
    assert response.status_code == 404
    data = response.json()

    assert "error" in data
    err = data["error"]
    assert err["code"] == "NOT_FOUND"
    assert "message" in err
    assert "timestamp" in err
    assert "request_id" in err


def test_422_validation_error_contract(client: TestClient):
    # Post invalid body to /api/v1/jobs (missing required 'title' and 'company')
    response = client.post("/api/v1/jobs", json={"invalid_field": "test"})
    assert response.status_code == 422
    data = response.json()

    assert "error" in data
    err = data["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert "details" in err
    assert isinstance(err["details"], list)
    assert len(err["details"]) > 0
    assert "location" in err["details"][0]
    assert "request_id" in err


def test_app_exception_custom_error_contract(client: TestClient):
    response = client.get("/api/v1/test-error?error_type=not_found")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "TestJob" in str(data["error"]["details"])


def test_pipeline_disabled_error_contract(client: TestClient):
    response = client.get("/api/v1/test-error?error_type=pipeline_disabled")
    assert response.status_code == 501
    data = response.json()
    assert data["error"]["code"] == "PIPELINE_STAGE_NOT_ACTIVE"
    assert data["error"]["details"]["planned_phase"] == "Phase 4"


def test_bad_request_error_contract(client: TestClient):
    response = client.get("/api/v1/test-error?error_type=bad_request")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "BAD_REQUEST"


def test_database_error_contract(client: TestClient):
    response = client.get("/api/v1/test-error?error_type=database_error")
    assert response.status_code == 500
    data = response.json()
    assert data["error"]["code"] == "DATABASE_ERROR"


def test_unhandled_exception_contract(client: TestClient):
    # Should catch ZeroDivisionError and return safe 500 without leaking stack trace
    response = client.get("/api/v1/test-error?error_type=unhandled")
    assert response.status_code == 500
    data = response.json()
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert data["error"]["message"] == "An unexpected internal server error occurred."
    assert "request_id" in data["error"]
