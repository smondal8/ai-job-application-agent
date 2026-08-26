import json
import re
import time
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.errors import AppError, BadRequestError
from app.core.logging import get_logger

logger = get_logger("app.services.llm.ollama")
settings = get_settings()


class LLMResponse(BaseModel):
    text: str
    model: str
    total_duration_ns: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None
    latency_ms: float


class OllamaLLMService:
    """Local Ollama LLM Provider Service (runs on Apple Silicon GPU).

    Ensures zero cloud leakage, zero paid API keys, and strict local inference.
    The model name is dynamically configurable via application settings.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        temperature: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS
        self.temperature = temperature if temperature is not None else settings.OLLAMA_TEMPERATURE

    async def check_health(self) -> Dict[str, Any]:
        """Check Ollama connectivity, response latency, and available models."""
        start_time = time.time()
        endpoint = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(endpoint)
                latency_ms = round((time.time() - start_time) * 1000, 2)
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    is_active_model_loaded = any(self.model in m for m in models)
                    return {
                        "provider": "ollama",
                        "status": "connected",
                        "base_url": self.base_url,
                        "active_model": self.model,
                        "is_active_model_available": is_active_model_loaded,
                        "available_models": models,
                        "latency_ms": latency_ms,
                        "error": None,
                    }
                else:
                    return {
                        "provider": "ollama",
                        "status": "degraded",
                        "base_url": self.base_url,
                        "active_model": self.model,
                        "is_active_model_available": False,
                        "available_models": [],
                        "latency_ms": latency_ms,
                        "error": f"HTTP {res.status_code}: {res.text[:100]}",
                    }
        except Exception as exc:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            logger.warning("Ollama health check failed: %s", exc)
            return {
                "provider": "ollama",
                "status": "disconnected",
                "base_url": self.base_url,
                "active_model": self.model,
                "is_active_model_available": False,
                "available_models": [],
                "latency_ms": latency_ms,
                "error": str(exc),
            }

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        format_json: bool = False,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        """Generate text completion from local Ollama model."""
        endpoint = f"{self.base_url}/api/generate"
        temp = temperature if temperature is not None else self.temperature

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temp,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt
        if format_json:
            payload["format"] = "json"

        start_time = time.time()
        logger.info(
            "Invoking local Ollama LLM (model=%s, json_format=%s, prompt_len=%d)",
            self.model,
            format_json,
            len(prompt),
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(endpoint, json=payload)
                latency_ms = round((time.time() - start_time) * 1000, 2)

                if res.status_code != 200:
                    error_msg = f"Ollama generation failed with HTTP {res.status_code}: {res.text[:200]}"
                    logger.error(error_msg)
                    raise AppError(error_msg, status_code=502, code="OLLAMA_ERROR")

                data = res.json()
                response_text = data.get("response", "").strip()

                logger.info(
                    "Ollama generation completed in %.2f ms (eval_count=%s)",
                    latency_ms,
                    data.get("eval_count"),
                )

                return LLMResponse(
                    text=response_text,
                    model=data.get("model", self.model),
                    total_duration_ns=data.get("total_duration"),
                    prompt_eval_count=data.get("prompt_eval_count"),
                    eval_count=data.get("eval_count"),
                    latency_ms=latency_ms,
                )
        except httpx.TimeoutException:
            logger.error("Ollama generation timed out after %.1f seconds", self.timeout)
            raise AppError(
                f"Local Ollama model '{self.model}' generation timed out after {self.timeout}s.",
                status_code=504,
                code="OLLAMA_TIMEOUT",
            )
        except httpx.ConnectError:
            logger.error("Failed to connect to Ollama at %s", self.base_url)
            raise AppError(
                f"Could not connect to local Ollama server at {self.base_url}. Ensure 'ollama serve' is running.",
                status_code=503,
                code="OLLAMA_CONNECTION_ERROR",
            )

    async def generate_structured_json(
        self,
        prompt: str,
        system_prompt: str,
        fallback_default: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate and robustly parse structured JSON from local Ollama model."""
        def _try_parse(raw_text: str) -> Optional[Dict[str, Any]]:
            if not raw_text or not raw_text.strip():
                return None
            # Strip think tags if model emitted reasoning tokens
            cleaned = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()

            # 1. Direct JSON parse
            try:
                data = json.loads(cleaned)
                if isinstance(data, dict):
                    # If Ollama returned its internal error envelope (e.g. {"error": "..."}) without schema keys
                    if "error" in data and len(data) == 1:
                        return None
                    return data
            except json.JSONDecodeError:
                pass

            # 2. Extract JSON between ```json ... ``` code blocks
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    if isinstance(data, dict) and not ("error" in data and len(data) == 1):
                        return data
                except json.JSONDecodeError:
                    pass

            # 3. Extract between first { and last }
            first_brace = cleaned.find("{")
            last_brace = cleaned.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                try:
                    data = json.loads(cleaned[first_brace : last_brace + 1])
                    if isinstance(data, dict) and not ("error" in data and len(data) == 1):
                        return data
                except json.JSONDecodeError:
                    pass
            return None

        # Attempt 1: with format_json=True
        try:
            llm_res = await self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                format_json=True,
            )
            parsed = _try_parse(llm_res.text.strip())
            if parsed is not None:
                return parsed
        except Exception as exc:
            logger.warning("Ollama format_json=True generation attempt encountered: %s", exc)

        # Attempt 2: without format_json constraint (allows thinking models to think and emit JSON blocks)
        try:
            retry_prompt = prompt + "\n\nIMPORTANT: Return ONLY a valid JSON object matching the schema inside a ```json { ... } ``` code block."
            retry_res = await self.generate(
                prompt=retry_prompt,
                system_prompt=system_prompt,
                format_json=False,
            )
            parsed = _try_parse(retry_res.text.strip())
            if parsed is not None:
                return parsed
        except Exception as exc:
            logger.warning("Ollama unconstrained generation attempt encountered: %s", exc)

        logger.warning("Failed to parse valid structured JSON from Ollama. Using fallback if available.")
        if fallback_default is not None:
            return fallback_default
        raise AppError(
            "Local LLM returned invalid JSON structure.",
            status_code=502,
            code="LLM_INVALID_JSON",
        )


ollama_service = OllamaLLMService()
