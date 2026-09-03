"""Groq-backed LLM client with the same contract as ``GeminiClient``.

The client intentionally preserves local Pydantic validation.  Groq JSON mode
helps produce JSON, but application schemas remain the source of truth.
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


class GroqClient:
    """Synchronous Groq client compatible with the investigation agents."""

    def __init__(
        self,
        api_key: str,
        model_name: str,
        *,
        timeout_seconds: float | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base_seconds: float = DEFAULT_BACKOFF_BASE_SECONDS,
        backoff_max_seconds: float = DEFAULT_BACKOFF_MAX_SECONDS,
        structured_correction_retries: int = DEFAULT_STRUCTURED_CORRECTION_RETRIES,
        sleep_fn: Callable[[float], None] = time.sleep,
        client: Any | None = None,
    ) -> None:
        if not api_key:
            raise GeminiClientError("Groq API key is not configured.")
        self._api_key = api_key
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds or DEFAULT_TIMEOUT_SECONDS
        self._max_retries = max(0, max_retries)
        self._backoff_base_seconds = max(0.0, backoff_base_seconds)
        self._backoff_max_seconds = max(0.0, backoff_max_seconds)
        self._structured_correction_retries = max(0, structured_correction_retries)
        self._sleep = sleep_fn
        if client is None:
            try:
                from groq import Groq
            except ImportError as exc:  # pragma: no cover - exercised in deployment config
                raise GeminiClientError(
                    "Groq SDK is not installed; add the 'groq' package to the environment."
                ) from exc
            client = Groq(api_key=api_key, timeout=self._timeout_seconds)
        self._client = client

    def generate(self, prompt: str, response_schema: type[T] | None = None) -> str | T:
        raw_text = self._request(prompt, response_schema=response_schema)
        if response_schema is None:
            return raw_text
        try:
            return self._validate_structured_output(raw_text, response_schema)
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as first_error:
            last_error: Exception = first_error
            correction_prompt = self._build_correction_prompt(
                prompt, response_schema, raw_text, first_error
            )
            for attempt in range(self._structured_correction_retries):
                try:
                    corrected_text = self._request(correction_prompt, response_schema=response_schema)
                    return self._validate_structured_output(corrected_text, response_schema)
                except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as error:
                    last_error = error
                    correction_prompt = self._build_correction_prompt(
                        prompt, response_schema, corrected_text, error
                    )
                    logger.warning(
                        "provider=groq structured-output correction attempt=%d schema=%s",
                        attempt + 1, response_schema.__name__,
                    )
            raise GeminiStructuredOutputError(
                f"Failed to parse Groq response into {response_schema.__name__} "
                f"after {self._structured_correction_retries} correction attempt(s): "
                f"{_safe_detail(last_error, self._api_key)}",
                original_error=last_error,
            ) from last_error

    def _request(self, prompt: str, *, response_schema: type[BaseModel] | None = None) -> str:
        kwargs: dict[str, Any] = {
            "model": self._model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }
        if response_schema is not None:
            kwargs["response_format"] = {"type": "json_object"}
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.chat.completions.create(**kwargs)
                raw_text = response.choices[0].message.content
                if not isinstance(raw_text, str):
                    if response_schema is not None:
                        return ""
                    raise GeminiClientError("Groq returned an empty text response.")
                if not raw_text.strip() and response_schema is None:
                    raise GeminiClientError("Groq returned an empty text response.")
                return raw_text
            except GeminiClientError:
                raise
            except Exception as exc:
                kind = self._failure_kind(exc)
                if attempt >= self._max_retries:
                    error_type = {
                        "rate_limit": GeminiRateLimitError,
                        "timeout": GeminiTimeoutError,
                        "transient": GeminiTransientError,
                    }.get(kind)
                    if error_type:
                        raise error_type(
                            f"Groq {kind} request failed after {self._max_retries} retries: "
                            f"{_safe_detail(exc, self._api_key)}",
                            original_error=exc,
                        ) from exc
                    raise GeminiClientError(
                        f"Groq API call failed: {_safe_detail(exc, self._api_key)}",
                        original_error=exc,
                    ) from exc
                if kind not in {"rate_limit", "timeout", "transient"}:
                    raise GeminiClientError(
                        f"Groq API call failed: {_safe_detail(exc, self._api_key)}",
                        original_error=exc,
                    ) from exc
                self._sleep(min(self._backoff_base_seconds * (2**attempt), self._backoff_max_seconds))
        raise GeminiClientError("Groq request ended without a response.")

    @staticmethod
    def _validate_structured_output(raw_text: str, response_schema: type[T]) -> T:
        return response_schema.model_validate(json.loads(raw_text))

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
            f"{original_prompt}\n\nYour previous response failed structured-output validation. "
            "Return ONLY valid JSON matching the requested schema.\n"
            f"Validation failure: {_safe_detail(validation_error)}\n"
            f"Expected Pydantic schema: {schema_text[:MAX_CORRECTION_OUTPUT_LENGTH]}\n"
            f"Previous output excerpt:\n{previous_output[:MAX_CORRECTION_OUTPUT_LENGTH]}"
        )

    @staticmethod
    def _failure_kind(error: Exception) -> str:
        status_code = getattr(error, "status_code", None)
        if not isinstance(status_code, int):
            status_code = getattr(error, "code", None)
        if status_code == 429:
            return "rate_limit"
        if status_code == 408:
            return "timeout"
        if isinstance(status_code, int) and 500 <= status_code <= 599:
            return "transient"
        if isinstance(error, (TimeoutError, httpx.TimeoutException)):
            return "timeout"
        if isinstance(error, (ConnectionError, OSError, httpx.NetworkError)):
            return "transient"
        return "permanent"
