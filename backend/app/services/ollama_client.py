"""Provider-specific Ollama client for structured reasoning evaluation.

This client mirrors the synchronous ``generate()`` behavior used by the
Reasoning Agent while preserving local JSON parsing, Pydantic validation,
bounded structured-output correction, and clear timeout/network failures.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.services.gemini_client import (
    DEFAULT_BACKOFF_BASE_SECONDS,
    DEFAULT_BACKOFF_MAX_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_STRUCTURED_CORRECTION_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    GeminiClientError,
    GeminiRateLimitError,
    GeminiStructuredOutputError,
    GeminiTimeoutError,
    GeminiTransientError,
    MAX_CORRECTION_OUTPUT_LENGTH,
    _safe_detail,
)

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class OllamaClient:
    """Reusable synchronous client for a local Ollama model."""

    def __init__(
        self,
        base_url: str,
        model_name: str,
        *,
        timeout_seconds: float | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base_seconds: float = DEFAULT_BACKOFF_BASE_SECONDS,
        backoff_max_seconds: float = DEFAULT_BACKOFF_MAX_SECONDS,
        structured_correction_retries: int = DEFAULT_STRUCTURED_CORRECTION_RETRIES,
        sleep_fn: Callable[[float], None] = time.sleep,
        http_client: httpx.Client | None = None,
        keep_alive: str | int | None = None,
        options: dict[str, Any] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds
        self._max_retries = max(0, max_retries)
        self._backoff_base_seconds = max(0.0, backoff_base_seconds)
        self._backoff_max_seconds = max(0.0, backoff_max_seconds)
        self._structured_correction_retries = max(0, structured_correction_retries)
        self._sleep = sleep_fn
        self._owns_client = http_client is None
        self._keep_alive = keep_alive
        self._options = options or {}
        self._client = http_client or httpx.Client(
            base_url=self._base_url,
            timeout=timeout_seconds or DEFAULT_TIMEOUT_SECONDS,
        )

    def generate(
        self,
        prompt: str,
        response_schema: type[T] | None = None,
    ) -> str | T:
        """Generate raw text or a validated Pydantic model."""
        raw_text = self._request(prompt, response_schema=response_schema)
        if response_schema is None:
            return raw_text

        try:
            return self._validate_structured_output(raw_text, response_schema)
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as first_error:
            last_error: Exception = first_error
            correction_prompt = self._build_correction_prompt(
                prompt,
                response_schema,
                raw_text,
                first_error,
            )
            for correction_attempt in range(self._structured_correction_retries):
                try:
                    corrected_text = self._request(
                        correction_prompt,
                        response_schema=response_schema,
                    )
                    return self._validate_structured_output(
                        corrected_text,
                        response_schema,
                    )
                except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as error:
                    last_error = error
                    correction_prompt = self._build_correction_prompt(
                        prompt,
                        response_schema,
                        corrected_text,
                        error,
                    )
                    logger.warning(
                        "Ollama structured-output correction attempt %d failed for %s",
                        correction_attempt + 1,
                        response_schema.__name__,
                    )

            raise GeminiStructuredOutputError(
                f"Failed to parse Ollama response into {response_schema.__name__} "
                f"after {self._structured_correction_retries} correction attempt(s): "
                f"{_safe_detail(last_error)}",
                original_error=last_error,
            ) from last_error

    def _request(
        self,
        prompt: str,
        *,
        response_schema: type[BaseModel] | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self._model_name,
            "prompt": prompt,
            "stream": False,
        }
        if self._keep_alive is not None:
            payload["keep_alive"] = self._keep_alive
        if self._options:
            payload["options"] = self._options
            
        if response_schema is not None:
            payload["format"] = response_schema.model_json_schema()

        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.post("/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
                raw_text = data.get("response")
                if not isinstance(raw_text, str):
                    if response_schema is not None:
                        return ""
                    raise GeminiClientError("Ollama returned an empty text response.")
                if not raw_text.strip() and response_schema is None:
                    raise GeminiClientError("Ollama returned an empty text response.")
                return raw_text
            except GeminiClientError:
                raise
            except Exception as exc:
                kind = self._failure_kind(exc)
                is_last_attempt = attempt >= self._max_retries
                if kind == "rate_limit":
                    if is_last_attempt:
                        raise GeminiRateLimitError(
                            f"Ollama rate limit persisted after {self._max_retries} retries: "
                            f"{_safe_detail(exc)}",
                            original_error=exc,
                        ) from exc
                    self._wait(attempt)
                    continue
                if kind == "timeout":
                    if is_last_attempt:
                        raise GeminiTimeoutError(
                            f"Ollama request timed out after {self._max_retries} retries: "
                            f"{_safe_detail(exc)}",
                            original_error=exc,
                        ) from exc
                    self._wait(attempt)
                    continue
                if kind == "transient":
                    if is_last_attempt:
                        raise GeminiTransientError(
                            f"Ollama transient request failed after {self._max_retries} retries: "
                            f"{_safe_detail(exc)}",
                            original_error=exc,
                        ) from exc
                    self._wait(attempt)
                    continue
                raise GeminiClientError(
                    f"Ollama API call failed: {_safe_detail(exc)}",
                    original_error=exc,
                ) from exc

        raise GeminiClientError("Ollama request ended without a response.")

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _wait(self, attempt: int) -> None:
        self._sleep(self._backoff_delay(attempt))

    def _backoff_delay(self, attempt: int) -> float:
        return min(
            self._backoff_base_seconds * (2**attempt),
            self._backoff_max_seconds,
        )

    @staticmethod
    def _validate_structured_output(
        raw_text: str,
        response_schema: type[T],
    ) -> T:
        parsed_data = json.loads(raw_text)
        return response_schema.model_validate(parsed_data)

    @staticmethod
    def _build_correction_prompt(
        original_prompt: str,
        response_schema: type[BaseModel],
        previous_output: str,
        validation_error: Exception,
    ) -> str:
        try:
            schema_text = json.dumps(response_schema.model_json_schema())
        except Exception:
            schema_text = response_schema.__name__
        return (
            f"{original_prompt}\n\n"
            "Your previous response failed structured-output validation. "
            "Return ONLY valid JSON matching the requested schema. Do not include "
            "markdown, commentary, or code fences.\n"
            f"Validation failure: {_safe_detail(validation_error)}\n"
            f"Expected Pydantic schema: {schema_text[:MAX_CORRECTION_OUTPUT_LENGTH]}\n"
            "Previous output excerpt:\n"
            f"{previous_output[:MAX_CORRECTION_OUTPUT_LENGTH]}"
        )

    @staticmethod
    def _failure_kind(error: Exception) -> str:
        status_code = OllamaClient._status_code(error)
        if status_code == 429:
            return "rate_limit"
        if status_code == 408:
            return "timeout"
        if status_code is not None and 500 <= status_code <= 599:
            return "transient"
        if isinstance(error, (TimeoutError, httpx.TimeoutException)):
            return "timeout"
        if isinstance(error, (ConnectionError, OSError, httpx.NetworkError)):
            return "transient"
        return "permanent"

    @staticmethod
    def _status_code(error: Exception) -> int | None:
        if isinstance(error, httpx.HTTPStatusError):
            return error.response.status_code
        for attribute in ("status_code", "code"):
            value = getattr(error, attribute, None)
            if isinstance(value, int):
                return value
        return None
