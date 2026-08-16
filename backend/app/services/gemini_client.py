"""Centralized, hardened Gemini client.

All Gemini access in the application goes through this module.  The client
keeps the existing synchronous public methods while adding bounded retries,
rate-limit handling, SDK timeout configuration, and strict structured-output
validation.
"""

from __future__ import annotations

import email.utils
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
from pydantic import BaseModel, ValidationError

from app.core.config import settings

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE_SECONDS = 0.5
DEFAULT_BACKOFF_MAX_SECONDS = 8.0
DEFAULT_STRUCTURED_CORRECTION_RETRIES = 1
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_ERROR_DETAIL_LENGTH = 500
MAX_CORRECTION_OUTPUT_LENGTH = 4_000


class GeminiClientError(Exception):
    """Base exception for application-facing Gemini failures."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error


class GeminiTransientError(GeminiClientError):
    """Raised after a retryable Gemini failure exhausts its retry budget."""


class GeminiRateLimitError(GeminiTransientError):
    """Raised after rate-limit retries are exhausted."""


class GeminiTimeoutError(GeminiTransientError):
    """Raised after timeout retries are exhausted."""


class GeminiStructuredOutputError(GeminiClientError):
    """Raised when Gemini cannot produce data matching the requested schema."""


def _safe_detail(error: Exception, secret: str | None = None) -> str:
    """Return bounded error text without exposing credentials or huge payloads."""
    detail = str(error).replace("\n", " ").strip()
    if secret:
        detail = detail.replace(secret, "[REDACTED]")
    for marker in ("api_key=", "key=", "x-goog-api-key=", "Authorization:"):
        start = detail.lower().find(marker.lower())
        if start >= 0:
            value_start = start + len(marker)
            value_end = len(detail)
            for delimiter in (" ", "&", "\"", "'", ","):
                delimiter_index = detail.find(delimiter, value_start)
                if delimiter_index >= 0:
                    value_end = min(value_end, delimiter_index)
            detail = f"{detail[:value_start]}[REDACTED]{detail[value_end:]}"
    if len(detail) > MAX_ERROR_DETAIL_LENGTH:
        detail = f"{detail[:MAX_ERROR_DETAIL_LENGTH]}…"
    return detail or error.__class__.__name__


def _numeric_setting(value: object, default: float) -> float:
    return value if isinstance(value, (int, float)) and value >= 0 else default


def _integer_setting(value: object, default: int) -> int:
    return int(value) if isinstance(value, int) and value >= 0 else default


class GeminiClient:
    """Reusable synchronous client for Google Gemini generative AI."""

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
    ) -> None:
        self._api_key = api_key
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds
        self._max_retries = max(0, max_retries)
        self._backoff_base_seconds = max(0.0, backoff_base_seconds)
        self._backoff_max_seconds = max(0.0, backoff_max_seconds)
        self._structured_correction_retries = max(0, structured_correction_retries)
        self._sleep = sleep_fn

        client_kwargs: dict[str, Any] = {"api_key": self._api_key}
        if self._timeout_seconds is not None:
            client_kwargs["http_options"] = genai_types.HttpOptions(
                timeout=max(1, int(self._timeout_seconds * 1000))
            )
        self._client = genai.Client(**client_kwargs)

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
                        "Gemini structured-output correction attempt %d failed for %s",
                        correction_attempt + 1,
                        response_schema.__name__,
                    )

            raise GeminiStructuredOutputError(
                f"Failed to parse Gemini response into {response_schema.__name__} "
                f"after {self._structured_correction_retries} correction attempt(s): "
                f"{_safe_detail(last_error, self._api_key)}",
                original_error=last_error,
            ) from last_error

    def generate_with_image(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/png",
    ) -> str:
        """Generate raw text from a prompt and image using the same retry policy."""
        try:
            image_part = genai_types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type,
            )
        except Exception as exc:
            raise GeminiClientError(
                f"Gemini Vision request could not be prepared: {_safe_detail(exc, self._api_key)}",
                original_error=exc,
            ) from exc
        return self._request([image_part, prompt])

    def _request(
        self,
        contents: Any,
        *,
        response_schema: type[BaseModel] | None = None,
    ) -> str:
        config: Any | None = None
        if response_schema is not None:
            config = genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
            )

        for attempt in range(self._max_retries + 1):
            try:
                kwargs: dict[str, Any] = {
                    "model": self._model_name,
                    "contents": contents,
                }
                if config is not None:
                    kwargs["config"] = config
                response = self._client.models.generate_content(**kwargs)
                raw_text = getattr(response, "text", None)
                if not isinstance(raw_text, str):
                    if response_schema is not None:
                        # Treat a missing structured response as malformed output
                        # so the bounded correction path can repair or reject it.
                        return ""
                    raise GeminiClientError("Gemini returned an empty text response.")
                if not raw_text.strip() and response_schema is None:
                    raise GeminiClientError("Gemini returned an empty text response.")
                return raw_text
            except GeminiClientError:
                raise
            except Exception as exc:
                kind = self._failure_kind(exc)
                is_last_attempt = attempt >= self._max_retries
                if kind == "rate_limit":
                    if is_last_attempt:
                        raise GeminiRateLimitError(
                            f"Gemini rate limit persisted after {self._max_retries} retries: "
                            f"{_safe_detail(exc, self._api_key)}",
                            original_error=exc,
                        ) from exc
                    self._wait(attempt, self._retry_after_seconds(exc))
                    continue
                if kind == "timeout":
                    if is_last_attempt:
                        raise GeminiTimeoutError(
                            f"Gemini request timed out after {self._max_retries} retries: "
                            f"{_safe_detail(exc, self._api_key)}",
                            original_error=exc,
                        ) from exc
                    self._wait(attempt)
                    continue
                if kind == "transient":
                    if is_last_attempt:
                        raise GeminiTransientError(
                            f"Gemini transient request failed after {self._max_retries} retries: "
                            f"{_safe_detail(exc, self._api_key)}",
                            original_error=exc,
                        ) from exc
                    self._wait(attempt)
                    continue
                raise GeminiClientError(
                    f"Gemini API call failed: {_safe_detail(exc, self._api_key)}",
                    original_error=exc,
                ) from exc

        raise GeminiClientError("Gemini request ended without a response.")

    def _wait(self, attempt: int, retry_after: float | None = None) -> None:
        delay = retry_after if retry_after is not None else self._backoff_delay(attempt)
        self._sleep(min(max(0.0, delay), self._backoff_max_seconds))

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
        status_code = GeminiClient._status_code(error)
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
        if isinstance(error, genai_errors.APIError):
            return error.code
        for attribute in ("status_code", "code"):
            value = getattr(error, attribute, None)
            if isinstance(value, int):
                return value
        return None

    @staticmethod
    def _retry_after_seconds(error: Exception) -> float | None:
        response = getattr(error, "response", None)
        headers = getattr(response, "headers", None)
        if headers is None:
            headers = getattr(error, "headers", None)
        if headers is None:
            details = getattr(error, "details", None)
            headers = details.get("headers") if isinstance(details, dict) else None
        if not headers:
            return None

        retry_after = None
        for key, value in headers.items():
            if str(key).lower() == "retry-after":
                retry_after = value
                break
        if retry_after is None:
            return None
        try:
            return max(0.0, float(retry_after))
        except (TypeError, ValueError):
            try:
                retry_date = email.utils.parsedate_to_datetime(str(retry_after))
                if retry_date.tzinfo is None:
                    retry_date = retry_date.replace(tzinfo=timezone.utc)
                return max(0.0, (retry_date - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError, OverflowError):
                return None


def _setting(name: str, default: int | float) -> int | float:
    value = getattr(settings, name, default)
    if isinstance(default, int):
        return _integer_setting(value, int(default))
    return _numeric_setting(value, float(default))


def get_gemini_client() -> GeminiClient:
    """Create a GeminiClient from central application settings."""
    kwargs: dict[str, Any] = {
        "max_retries": int(_setting("GEMINI_MAX_RETRIES", DEFAULT_MAX_RETRIES)),
        "backoff_base_seconds": float(
            _setting("GEMINI_BACKOFF_BASE_SECONDS", DEFAULT_BACKOFF_BASE_SECONDS)
        ),
        "backoff_max_seconds": float(
            _setting("GEMINI_BACKOFF_MAX_SECONDS", DEFAULT_BACKOFF_MAX_SECONDS)
        ),
        "structured_correction_retries": int(
            _setting(
                "GEMINI_STRUCTURED_CORRECTION_RETRIES",
                DEFAULT_STRUCTURED_CORRECTION_RETRIES,
            )
        ),
    }
    timeout = getattr(settings, "GEMINI_TIMEOUT_SECONDS", None)
    if isinstance(timeout, (int, float)):
        kwargs["timeout_seconds"] = float(timeout)

    return GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL,
        **kwargs,
    )
