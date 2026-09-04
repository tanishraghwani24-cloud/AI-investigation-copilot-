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

# Reasoning models (e.g. openai/gpt-oss-20b) spend part of the completion
# budget on hidden chain-of-thought before the final answer, so the budget has
# to cover CoT *and* the JSON document. openai/gpt-oss-20b accepts up to 65536
# completion tokens (verified against Groq's /models endpoint); 16384 is ample
# headroom for a measured ~1.5-2.3k-token reasoning call without approaching
# that ceiling.
DEFAULT_MAX_COMPLETION_TOKENS = 16384

# Chain-of-thought length is the real consumer of the completion budget, so cap
# it at the source instead of inflating the budget. Hypothesis generation is a
# structured extraction task over facts already supplied in the prompt — it does
# not need deep deliberation, and "low" measurably shortens CoT.
DEFAULT_REASONING_EFFORT = "low"

# Groq accepts `reasoning_effort` only on chain-of-thought models; sending it to
# a non-reasoning model (e.g. a Llama chat model) is a 400. Gate on the families
# that support it so GROQ_MODEL stays freely configurable.
_REASONING_MODEL_MARKERS = ("gpt-oss", "qwen3", "deepseek-r1")


def _supports_reasoning_effort(model_name: str) -> bool:
    """Return whether *model_name* accepts the ``reasoning_effort`` parameter."""
    lowered = model_name.lower()
    return any(marker in lowered for marker in _REASONING_MODEL_MARKERS)


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
        max_completion_tokens: int = DEFAULT_MAX_COMPLETION_TOKENS,
        reasoning_effort: str | None = DEFAULT_REASONING_EFFORT,
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
        self._max_completion_tokens = max(1, max_completion_tokens)
        self._reasoning_effort = (
            reasoning_effort if reasoning_effort and _supports_reasoning_effort(model_name) else None
        )
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
            # `max_completion_tokens` — not the deprecated `max_tokens` — is the
            # parameter reasoning models honour, and it covers CoT plus answer.
            "max_completion_tokens": self._max_completion_tokens,
        }
        if self._reasoning_effort is not None:
            kwargs["reasoning_effort"] = self._reasoning_effort
        if response_schema is not None:
            # Loose "json_object" mode only asks the model to *try* to produce
            # valid JSON by following instructions, so it plans the document
            # inside its chain-of-thought — measurably ~60% more completion
            # tokens on an identical prompt. Worse, it is the only mode that can
            # fail server-side: when the budget runs out mid-document Groq
            # rejects the whole response with 400 json_validate_failed
            # ("max completion tokens reached before generating a valid
            # document") and returns no content at all. Schema-constrained
            # decoding makes invalid JSON syntax unreachable, so that failure
            # class cannot occur and a budget overrun degrades to an
            # inspectable finish_reason="length" instead. Pydantic validation
            # below remains the actual source of truth.
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_schema.__name__,
                    "schema": response_schema.model_json_schema(),
                },
            }
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.chat.completions.create(**kwargs)
                choice = response.choices[0]
                if getattr(choice, "finish_reason", None) == "length":
                    # Truncated mid-document: a correction round-trip would only
                    # send a longer prompt, so fail with an actionable message.
                    raise GeminiStructuredOutputError(
                        "Groq response hit the completion-token limit "
                        f"({self._max_completion_tokens}) before finishing; "
                        "raise GROQ_MAX_COMPLETION_TOKENS or reduce the prompt."
                    )
                raw_text = choice.message.content
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
