from app.services.redaction.redaction_service import redaction_service


def test_redaction_service_masks_bearer_tokens_and_api_keys():
    raw_text = (
        "Connecting to portal using Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz123 "
        "and OpenAI key sk-1234567890abcdef1234567890 and GitHub token ghp_123456789012345678901234567890123456."
    )
    redacted = redaction_service.redact_text(raw_text)

    assert "Bearer [REDACTED_TOKEN]" in redacted
    assert "sk-1234567890abcdef1234567890" not in redacted
    assert "[REDACTED_API_KEY]" in redacted
    assert "ghp_123456789012345678901234567890123456" not in redacted
    assert "[REDACTED_GITHUB_TOKEN]" in redacted


def test_redaction_service_masks_passwords_and_private_keys():
    raw_text = 'Database connection string: postgresql://user:password="SecretPass123" and token=abc_secret_123'
    redacted = redaction_service.redact_text(raw_text)

    assert "SecretPass123" not in redacted
    assert "token=[REDACTED]" in redacted


def test_redaction_service_masks_nested_dictionary_structures():
    nested_data = {
        "user_id": 42,
        "credentials": {
            "password": "SuperSecretPassword!",
            "api_key": "sk-99887766554433221100",
            "access_token": "token_value_abc",
        },
        "public_profile": {
            "name": "Jane Doe",
            "bio": "Software Engineer with password in text: password='abc'",
        },
        "tags": ["engineer", "Bearer secret_bearer_token"],
    }

    redacted_data = redaction_service.redact_structure(nested_data)

    assert redacted_data["user_id"] == 42
    assert redacted_data["credentials"]["password"] == "[REDACTED]"
    assert redacted_data["credentials"]["api_key"] == "[REDACTED]"
    assert redacted_data["credentials"]["access_token"] == "[REDACTED]"
    assert redacted_data["public_profile"]["name"] == "Jane Doe"
    assert "SuperSecretPassword!" not in str(redacted_data)
