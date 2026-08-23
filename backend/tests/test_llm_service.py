import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.core.errors import AppError
from app.services.llm.ollama_service import OllamaLLMService


@pytest.mark.asyncio
async def test_ollama_service_init_and_config():
    service = OllamaLLMService(
        base_url="http://127.0.0.1:11434",
        model="qwen3:8b",
        timeout=60.0,
        temperature=0.1,
    )
    assert service.base_url == "http://127.0.0.1:11434"
    assert service.model == "qwen3:8b"
    assert service.timeout == 60.0
    assert service.temperature == 0.1


@pytest.mark.asyncio
async def test_ollama_check_health_connected():
    service = OllamaLLMService()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [{"name": "qwen3:8b"}, {"name": "llama3.2:3b"}]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        health = await service.check_health()
        assert health["status"] == "connected"
        assert health["is_active_model_available"] is True
        assert "qwen3:8b" in health["available_models"]
        assert health["provider"] == "ollama"


@pytest.mark.asyncio
async def test_ollama_generate_success():
    service = OllamaLLMService(model="qwen3:8b")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "model": "qwen3:8b",
        "response": "Here is the tailored summary for the candidate.",
        "eval_count": 42,
        "total_duration": 1500000000,
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        result = await service.generate(
            prompt="Write a 2-sentence summary for a Staff Backend Engineer.",
            system_prompt="You are an expert technical resume writer.",
        )

        assert result.text == "Here is the tailored summary for the candidate."
        assert result.model == "qwen3:8b"
        assert result.eval_count == 42


@pytest.mark.asyncio
async def test_ollama_generate_structured_json():
    service = OllamaLLMService()

    mock_json_content = '{"fit_score": 92.5, "fit_level": "high", "summary": "Great match for the role."}'
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "model": "qwen3:8b",
        "response": f"```json\n{mock_json_content}\n```",
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        parsed = await service.generate_structured_json(
            prompt="Analyze candidate fit.",
            system_prompt="Return valid JSON.",
        )

        assert parsed["fit_score"] == 92.5
        assert parsed["fit_level"] == "high"
        assert parsed["summary"] == "Great match for the role."


@pytest.mark.asyncio
async def test_ollama_error_handling_timeout():
    service = OllamaLLMService(timeout=1.0)

    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Read timed out")):
        with pytest.raises(AppError) as exc_info:
            await service.generate("Test prompt")

        assert exc_info.value.status_code == 504
        assert "timed out" in exc_info.value.message
