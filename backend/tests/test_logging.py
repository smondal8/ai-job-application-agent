import json
import logging
from fastapi.testclient import TestClient
from app.core.logging import JsonFormatter, ConsoleFormatter, RequestIdFilter, request_id_ctx


def test_request_id_in_response_headers(client: TestClient):
    response = client.get("/health")
    assert "x-request-id" in response.headers
    assert response.headers["x-request-id"].startswith("req-")
    assert "x-response-time-ms" in response.headers


def test_custom_request_id_forwarded(client: TestClient):
    custom_id = "test-custom-req-12345"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.headers["x-request-id"] == custom_id


def test_json_log_formatter():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=42,
        msg="Test structured log message",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-test-999"

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert parsed["message"] == "Test structured log message"
    assert parsed["request_id"] == "req-test-999"
    assert "timestamp" in parsed


def test_console_log_formatter():
    formatter = ConsoleFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.WARNING,
        pathname=__file__,
        lineno=10,
        msg="Warning sample message",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-abc-456"

    formatted = formatter.format(record)
    assert "WARNING" in formatted
    assert "req-abc-456" in formatted
    assert "Warning sample message" in formatted
