"""Unit tests for GeminiClient reliability behavior.

All Gemini SDK interactions are mocked at the ``google.genai.Client`` boundary
— no real Gemini API or Ollama server is ever contacted.  Tests verify the
exact existing behavior documented in gemini_client.py: retry logic, backoff,
rate-limit handling with Retry-After, timeout, structured-output correction,
exception typing / chaining, provider selection, credential redaction, and
Gemini-specific response parsing.
"""

import json
import time
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, PropertyMock, patch

import httpx
import pytest
from google.genai import errors as genai_errors
from pydantic import BaseModel

from app.services.gemini_client import (
    DEFAULT_BACKOFF_BASE_SECONDS,
    DEFAULT_BACKOFF_MAX_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_STRUCTURED_CORRECTION_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    MAX_CORRECTION_OUTPUT_LENGTH,
    MAX_ERROR_DETAIL_LENGTH,
    GeminiClient,
    GeminiClientError,
    GeminiRateLimitError,
    GeminiStructuredOutputError,
    GeminiTimeoutError,
    GeminiTransientError,
    _safe_detail,
    get_gemini_client,
    get_reasoning_client,
)


# ---------------------------------------------------------------------------
# Test schema
# ---------------------------------------------------------------------------

class SimpleSchema(BaseModel):
    name: str
    value: int


class NestedSchema(BaseModel):
    label: str
    items: list[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_genai_response(text: str | None) -> MagicMock:
    """Build a mock genai response with the given .text attribute."""
    resp = MagicMock()
    resp.text = text
    return resp


def _make_client(
    mock_genai_client: MagicMock | None = None,
    *,
    max_retries: int = 0,
    backoff_base: float = 0.0,
    backoff_max: float = 0.0,
    correction_retries: int = 1,
    timeout_seconds: float | None = None,
) -> GeminiClient:
    """Create a GeminiClient with an injected mock SDK client and no-op sleep."""
    if mock_genai_client is None:
        mock_genai_client = MagicMock()

    with patch("app.services.gemini_client.genai.Client", return_value=mock_genai_client):
        client = GeminiClient(
            api_key="fake-api-key",
            model_name="gemini-test",
            max_retries=max_retries,
            backoff_base_seconds=backoff_base,
            backoff_max_seconds=backoff_max,
            structured_correction_retries=correction_retries,
            timeout_seconds=timeout_seconds,
            sleep_fn=lambda _: None,
        )

    return client


def _make_api_error(code: int, message: str = "error") -> genai_errors.APIError:
    """Build a google.genai APIError with a given status code."""
    return genai_errors.APIError(code=code, response_json={"error": {"message": message}})


# ---------------------------------------------------------------------------
# 1. Successful plain-text generation
# ---------------------------------------------------------------------------

class TestPlainTextGeneration:
    """Verify normal text generation via the Gemini SDK."""

    def test_returns_text_from_sdk_response(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response(
            "Hello, world!"
        )
        client = _make_client(mock_sdk)

        result = client.generate("Say hello")

        assert result == "Hello, world!"
        mock_sdk.models.generate_content.assert_called_once()

    def test_preserves_whitespace_in_text_response(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response(
            "  spaced text  "
        )
        client = _make_client(mock_sdk)

        result = client.generate("test")

        assert result == "  spaced text  "

    def test_no_config_passed_for_plain_text(self):
        """Plain-text generation must NOT pass a response_schema config."""
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response("ok")
        client = _make_client(mock_sdk)

        client.generate("test")

        call_kwargs = mock_sdk.models.generate_content.call_args
        assert "config" not in call_kwargs.kwargs


# ---------------------------------------------------------------------------
# 2. Successful structured / Pydantic generation
# ---------------------------------------------------------------------------

class TestStructuredGeneration:
    """Verify structured-output generation and Pydantic validation."""

    def test_returns_validated_pydantic_model(self):
        valid_json = json.dumps({"name": "test", "value": 42})
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response(
            valid_json
        )
        client = _make_client(mock_sdk)

        result = client.generate("Give data", response_schema=SimpleSchema)

        assert isinstance(result, SimpleSchema)
        assert result.name == "test"
        assert result.value == 42

    def test_structured_request_passes_json_config(self):
        """Structured generation must configure response_mime_type and schema."""
        valid_json = json.dumps({"name": "x", "value": 1})
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response(
            valid_json
        )
        client = _make_client(mock_sdk)

        client.generate("test", response_schema=SimpleSchema)

        call_kwargs = mock_sdk.models.generate_content.call_args
        assert "config" in call_kwargs.kwargs

    def test_nested_schema_validates_correctly(self):
        valid_json = json.dumps({"label": "group", "items": ["a", "b"]})
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response(
            valid_json
        )
        client = _make_client(mock_sdk)

        result = client.generate("test", response_schema=NestedSchema)

        assert isinstance(result, NestedSchema)
        assert result.label == "group"
        assert result.items == ["a", "b"]


# ---------------------------------------------------------------------------
# 3. Empty / missing model responses
# ---------------------------------------------------------------------------

class TestEmptyResponses:
    """Verify behavior when Gemini returns empty or missing text."""

    def test_none_text_raises_for_plain_generation(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response(None)
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiClientError, match="empty text response"):
            client.generate("test")

    def test_whitespace_only_text_raises_for_plain_generation(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response("   ")
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiClientError, match="empty text response"):
            client.generate("test")

    def test_none_text_returns_empty_string_for_structured(self):
        """When response_schema is set and .text is None, _request returns ""
        which then fails JSON parsing and enters the correction path."""
        mock_sdk = MagicMock()
        # All calls return None text -> "" -> JSONDecodeError
        mock_sdk.models.generate_content.return_value = _make_genai_response(None)
        client = _make_client(mock_sdk, correction_retries=0)

        with pytest.raises(GeminiStructuredOutputError):
            client.generate("test", response_schema=SimpleSchema)

    def test_missing_text_attribute_returns_empty_for_structured(self):
        """If the response object has no .text attribute at all."""
        mock_sdk = MagicMock()
        resp = MagicMock(spec=[])  # no attributes
        mock_sdk.models.generate_content.return_value = resp
        client = _make_client(mock_sdk, correction_retries=0)

        with pytest.raises(GeminiStructuredOutputError):
            client.generate("test", response_schema=SimpleSchema)

    def test_empty_string_text_raises_for_plain_generation(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response("")
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiClientError, match="empty text response"):
            client.generate("test")


# ---------------------------------------------------------------------------
# 4. Malformed structured output
# ---------------------------------------------------------------------------

class TestMalformedStructuredOutput:
    """Verify behavior when the SDK returns unparseable structured output."""

    def test_invalid_json_with_zero_corrections_raises(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response(
            "not json at all"
        )
        client = _make_client(mock_sdk, correction_retries=0)

        with pytest.raises(GeminiStructuredOutputError, match="Failed to parse"):
            client.generate("test", response_schema=SimpleSchema)

    def test_valid_json_wrong_schema_with_zero_corrections_raises(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response(
            json.dumps({"wrong_field": "data"})
        )
        client = _make_client(mock_sdk, correction_retries=0)

        with pytest.raises(GeminiStructuredOutputError):
            client.generate("test", response_schema=SimpleSchema)

    def test_markdown_wrapped_json_fails_parsing(self):
        """JSON wrapped in markdown code fences must fail (not silently pass)."""
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response(
            '```json\n{"name": "x", "value": 1}\n```'
        )
        client = _make_client(mock_sdk, correction_retries=0)

        with pytest.raises(GeminiStructuredOutputError):
            client.generate("test", response_schema=SimpleSchema)


# ---------------------------------------------------------------------------
# 5. Structured-output correction / retry behavior
# ---------------------------------------------------------------------------

class TestStructuredOutputCorrection:
    """Verify the bounded correction retry loop for malformed output."""

    def test_correction_succeeds_on_second_attempt(self):
        valid_json = json.dumps({"name": "fixed", "value": 1})
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = [
            _make_genai_response("not json"),
            _make_genai_response(valid_json),
        ]
        client = _make_client(mock_sdk, correction_retries=1)

        result = client.generate("test", response_schema=SimpleSchema)

        assert isinstance(result, SimpleSchema)
        assert result.name == "fixed"
        assert mock_sdk.models.generate_content.call_count == 2

    def test_pydantic_validation_failure_triggers_correction(self):
        bad_json = json.dumps({"name": "test"})  # missing 'value'
        good_json = json.dumps({"name": "test", "value": 99})
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = [
            _make_genai_response(bad_json),
            _make_genai_response(good_json),
        ]
        client = _make_client(mock_sdk, correction_retries=1)

        result = client.generate("test", response_schema=SimpleSchema)

        assert isinstance(result, SimpleSchema)
        assert result.value == 99

    def test_all_correction_retries_exhausted_raises(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response(
            "not json"
        )
        client = _make_client(mock_sdk, correction_retries=2)

        with pytest.raises(GeminiStructuredOutputError, match="2 correction attempt"):
            client.generate("test", response_schema=SimpleSchema)

        # 1 original + 2 correction = 3
        assert mock_sdk.models.generate_content.call_count == 3

    def test_zero_correction_retries_fails_immediately(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response(
            "not json"
        )
        client = _make_client(mock_sdk, correction_retries=0)

        with pytest.raises(GeminiStructuredOutputError):
            client.generate("test", response_schema=SimpleSchema)

        assert mock_sdk.models.generate_content.call_count == 1

    def test_correction_prompt_includes_schema_and_error(self):
        """Verify the correction prompt is well-formed."""
        prompt = GeminiClient._build_correction_prompt(
            "original prompt",
            SimpleSchema,
            '{"bad": true}',
            ValueError("missing field"),
        )
        assert "original prompt" in prompt
        assert "structured-output validation" in prompt
        assert "missing field" in prompt
        assert "SimpleSchema" in prompt or "name" in prompt

    def test_correction_prompt_truncates_long_output(self):
        long_output = "x" * (MAX_CORRECTION_OUTPUT_LENGTH + 1000)
        prompt = GeminiClient._build_correction_prompt(
            "prompt", SimpleSchema, long_output, ValueError("err"),
        )
        # The previous output excerpt should be truncated
        assert len(prompt) < len(long_output) + 5000


# ---------------------------------------------------------------------------
# 6. Retry count and retry exhaustion
# ---------------------------------------------------------------------------

class TestRetryCountAndExhaustion:
    """Verify exact retry counts for transient / timeout / rate-limit errors."""

    def test_transient_retry_then_succeed(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = [
            _make_api_error(500, "server error"),
            _make_genai_response("recovered"),
        ]
        client = _make_client(mock_sdk, max_retries=1)

        result = client.generate("test")

        assert result == "recovered"
        assert mock_sdk.models.generate_content.call_count == 2

    def test_transient_retries_exhausted(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = _make_api_error(
            502, "bad gateway"
        )
        client = _make_client(mock_sdk, max_retries=2)

        with pytest.raises(GeminiTransientError):
            client.generate("test")

        # initial + 2 retries = 3
        assert mock_sdk.models.generate_content.call_count == 3

    def test_zero_retries_fails_immediately_on_transient(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = _make_api_error(503)
        client = _make_client(mock_sdk, max_retries=0)

        with pytest.raises(GeminiTransientError):
            client.generate("test")

        assert mock_sdk.models.generate_content.call_count == 1

    def test_timeout_retries_exhausted(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = TimeoutError("timed out")
        client = _make_client(mock_sdk, max_retries=1)

        with pytest.raises(GeminiTimeoutError):
            client.generate("test")

        assert mock_sdk.models.generate_content.call_count == 2

    def test_rate_limit_retries_exhausted(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = _make_api_error(429)
        client = _make_client(mock_sdk, max_retries=1)

        with pytest.raises(GeminiRateLimitError):
            client.generate("test")

        assert mock_sdk.models.generate_content.call_count == 2


# ---------------------------------------------------------------------------
# 7. Timeout handling
# ---------------------------------------------------------------------------

class TestTimeoutHandling:
    """Verify timeout errors from various sources are correctly classified."""

    def test_python_timeout_error_raises_gemini_timeout(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = TimeoutError("timed out")
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiTimeoutError):
            client.generate("test")

    def test_httpx_read_timeout_raises_gemini_timeout(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = httpx.ReadTimeout(
            "read timed out"
        )
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiTimeoutError):
            client.generate("test")

    def test_httpx_connect_timeout_raises_gemini_timeout(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = httpx.ConnectTimeout(
            "connect timed out"
        )
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiTimeoutError):
            client.generate("test")

    def test_http_408_raises_gemini_timeout(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = _make_api_error(408)
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiTimeoutError):
            client.generate("test")

    def test_timeout_seconds_passed_to_sdk(self):
        """Verify that timeout_seconds is forwarded to the SDK HttpOptions."""
        mock_genai_cls = MagicMock()
        with patch("app.services.gemini_client.genai.Client", mock_genai_cls):
            GeminiClient(
                api_key="key",
                model_name="model",
                timeout_seconds=45.0,
                sleep_fn=lambda _: None,
            )

        call_kwargs = mock_genai_cls.call_args.kwargs
        assert "http_options" in call_kwargs


# ---------------------------------------------------------------------------
# 8. Transient / API failures
# ---------------------------------------------------------------------------

class TestTransientFailures:
    """Verify transient error classification and retry behavior."""

    def test_http_500_raises_transient(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = _make_api_error(500)
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiTransientError):
            client.generate("test")

    def test_http_503_raises_transient(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = _make_api_error(503)
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiTransientError):
            client.generate("test")

    def test_connection_error_raises_transient(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = ConnectionError(
            "connection refused"
        )
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiTransientError):
            client.generate("test")

    def test_os_error_raises_transient(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = OSError("network unreachable")
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiTransientError):
            client.generate("test")

    def test_httpx_connect_error_raises_transient(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = httpx.ConnectError(
            "connection refused"
        )
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiTransientError):
            client.generate("test")

    def test_transient_recovery_on_retry(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = [
            ConnectionError("refused"),
            _make_genai_response("recovered"),
        ]
        client = _make_client(mock_sdk, max_retries=1)

        result = client.generate("test")
        assert result == "recovered"


# ---------------------------------------------------------------------------
# 9. Rate-limit handling
# ---------------------------------------------------------------------------

class TestRateLimitHandling:
    """Verify rate-limit detection and Retry-After header parsing."""

    def test_http_429_raises_rate_limit_error(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = _make_api_error(429)
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiRateLimitError):
            client.generate("test")

    def test_rate_limit_retry_then_succeed(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = [
            _make_api_error(429),
            _make_genai_response("ok after rate limit"),
        ]
        client = _make_client(mock_sdk, max_retries=1)

        result = client.generate("test")
        assert result == "ok after rate limit"

    def test_retry_after_numeric_header_parsed(self):
        """Verify _retry_after_seconds parses a numeric Retry-After header."""
        err = _make_api_error(429)
        err.response = MagicMock()
        err.response.headers = {"Retry-After": "5"}

        result = GeminiClient._retry_after_seconds(err)

        assert result == 5.0

    def test_retry_after_zero_returns_zero(self):
        err = _make_api_error(429)
        err.response = MagicMock()
        err.response.headers = {"Retry-After": "0"}

        result = GeminiClient._retry_after_seconds(err)

        assert result == 0.0

    def test_retry_after_missing_returns_none(self):
        err = _make_api_error(429)
        # No response attribute
        result = GeminiClient._retry_after_seconds(err)
        assert result is None

    def test_retry_after_from_error_headers(self):
        """Some errors expose headers directly on the error object."""
        err = _make_api_error(429)
        err.headers = {"Retry-After": "3"}

        result = GeminiClient._retry_after_seconds(err)

        assert result == 3.0

    def test_retry_after_from_details_dict(self):
        """Some errors expose headers in a details dict."""
        err = _make_api_error(429)
        err.details = {"headers": {"Retry-After": "7"}}

        result = GeminiClient._retry_after_seconds(err)

        assert result == 7.0

    def test_retry_after_invalid_string_returns_none(self):
        err = _make_api_error(429)
        err.response = MagicMock()
        err.response.headers = {"Retry-After": "not-a-number-or-date"}

        result = GeminiClient._retry_after_seconds(err)

        assert result is None

    def test_retry_after_http_date_parsed(self):
        """Verify Retry-After with an HTTP-date value is parsed."""
        from datetime import timedelta

        # Use a large offset to avoid timing sensitivity
        future = datetime.now(timezone.utc) + timedelta(seconds=120)
        http_date = future.strftime("%a, %d %b %Y %H:%M:%S GMT")

        err = _make_api_error(429)
        err.response = MagicMock()
        err.response.headers = {"Retry-After": http_date}

        result = GeminiClient._retry_after_seconds(err)

        # Should be approximately 120 seconds (generous tolerance for test execution time)
        assert result is not None
        assert 110.0 <= result <= 130.0

    def test_rate_limit_wait_uses_retry_after(self):
        """Verify _wait uses retry_after when provided for rate limits."""
        sleep_calls: list[float] = []
        mock_sdk = MagicMock()

        err = _make_api_error(429)
        err.response = MagicMock()
        err.response.headers = {"Retry-After": "2"}

        mock_sdk.models.generate_content.side_effect = [
            err,
            _make_genai_response("ok"),
        ]

        with patch("app.services.gemini_client.genai.Client", return_value=mock_sdk):
            client = GeminiClient(
                api_key="key",
                model_name="model",
                max_retries=1,
                backoff_base_seconds=0.5,
                backoff_max_seconds=8.0,
                sleep_fn=sleep_calls.append,
            )

        client.generate("test")

        assert len(sleep_calls) == 1
        assert sleep_calls[0] == 2.0  # Should use Retry-After, not backoff


# ---------------------------------------------------------------------------
# 10. Permanent / non-retryable failures
# ---------------------------------------------------------------------------

class TestPermanentFailures:
    """Verify non-retryable errors raise GeminiClientError immediately."""

    def test_unexpected_exception_no_retry(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = RuntimeError("unexpected")
        client = _make_client(mock_sdk, max_retries=3)

        with pytest.raises(GeminiClientError, match="Gemini API call failed"):
            client.generate("test")

        # Permanent errors must NOT retry
        assert mock_sdk.models.generate_content.call_count == 1

    def test_http_400_raises_permanent_error(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = _make_api_error(
            400, "bad request"
        )
        client = _make_client(mock_sdk, max_retries=3)

        with pytest.raises(GeminiClientError):
            client.generate("test")

        assert mock_sdk.models.generate_content.call_count == 1

    def test_http_401_raises_permanent_error(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = _make_api_error(
            401, "unauthorized"
        )
        client = _make_client(mock_sdk, max_retries=3)

        with pytest.raises(GeminiClientError):
            client.generate("test")

        assert mock_sdk.models.generate_content.call_count == 1

    def test_http_403_raises_permanent_error(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = _make_api_error(
            403, "forbidden"
        )
        client = _make_client(mock_sdk, max_retries=3)

        with pytest.raises(GeminiClientError):
            client.generate("test")

        assert mock_sdk.models.generate_content.call_count == 1

    def test_gemini_client_error_reraises_without_retry(self):
        """GeminiClientError raised internally (e.g., empty response) must not retry."""
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response("   ")
        client = _make_client(mock_sdk, max_retries=3)

        with pytest.raises(GeminiClientError, match="empty text response"):
            client.generate("test")

        assert mock_sdk.models.generate_content.call_count == 1


# ---------------------------------------------------------------------------
# 11. Exception typing and original-error chaining
# ---------------------------------------------------------------------------

class TestExceptionTypingAndChaining:
    """Verify exception hierarchy and original_error preservation."""

    def test_rate_limit_is_subclass_of_transient(self):
        assert issubclass(GeminiRateLimitError, GeminiTransientError)

    def test_timeout_is_subclass_of_transient(self):
        assert issubclass(GeminiTimeoutError, GeminiTransientError)

    def test_transient_is_subclass_of_client_error(self):
        assert issubclass(GeminiTransientError, GeminiClientError)

    def test_structured_output_is_subclass_of_client_error(self):
        assert issubclass(GeminiStructuredOutputError, GeminiClientError)

    def test_structured_output_is_not_subclass_of_transient(self):
        assert not issubclass(GeminiStructuredOutputError, GeminiTransientError)

    def test_original_error_preserved_on_timeout(self):
        original = TimeoutError("timed out")
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = original
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiTimeoutError) as exc_info:
            client.generate("test")

        assert exc_info.value.original_error is original

    def test_original_error_preserved_on_transient(self):
        original = ConnectionError("refused")
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = original
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiTransientError) as exc_info:
            client.generate("test")

        assert exc_info.value.original_error is original

    def test_original_error_preserved_on_rate_limit(self):
        original = _make_api_error(429, "rate limited")
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = original
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiRateLimitError) as exc_info:
            client.generate("test")

        assert exc_info.value.original_error is original

    def test_original_error_preserved_on_structured_output(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response(
            "not json"
        )
        client = _make_client(mock_sdk, correction_retries=0)

        with pytest.raises(GeminiStructuredOutputError) as exc_info:
            client.generate("test", response_schema=SimpleSchema)

        assert exc_info.value.original_error is not None

    def test_original_error_preserved_on_permanent(self):
        original = RuntimeError("kaboom")
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = original
        client = _make_client(mock_sdk)

        with pytest.raises(GeminiClientError) as exc_info:
            client.generate("test")

        assert exc_info.value.original_error is original

    def test_gemini_client_error_constructor(self):
        err = GeminiClientError("message", original_error=ValueError("inner"))
        assert str(err) == "message"
        assert isinstance(err.original_error, ValueError)

    def test_gemini_client_error_no_original(self):
        err = GeminiClientError("message")
        assert err.original_error is None


# ---------------------------------------------------------------------------
# 12. Backoff behavior
# ---------------------------------------------------------------------------

class TestBackoffBehavior:
    """Verify exponential backoff calculation and capping."""

    def test_backoff_delay_exponential(self):
        mock_sdk = MagicMock()
        client = _make_client(mock_sdk, backoff_base=1.0, backoff_max=100.0)

        assert client._backoff_delay(0) == 1.0   # 1.0 * 2^0
        assert client._backoff_delay(1) == 2.0   # 1.0 * 2^1
        assert client._backoff_delay(2) == 4.0   # 1.0 * 2^2
        assert client._backoff_delay(3) == 8.0   # 1.0 * 2^3

    def test_backoff_delay_capped_at_max(self):
        mock_sdk = MagicMock()
        client = _make_client(mock_sdk, backoff_base=1.0, backoff_max=5.0)

        assert client._backoff_delay(0) == 1.0
        assert client._backoff_delay(1) == 2.0
        assert client._backoff_delay(2) == 4.0
        assert client._backoff_delay(3) == 5.0   # capped
        assert client._backoff_delay(10) == 5.0  # still capped

    def test_sleep_called_on_transient_retry(self):
        sleep_calls: list[float] = []
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = [
            ConnectionError("refused"),
            _make_genai_response("ok"),
        ]

        with patch("app.services.gemini_client.genai.Client", return_value=mock_sdk):
            client = GeminiClient(
                api_key="key",
                model_name="model",
                max_retries=1,
                backoff_base_seconds=0.5,
                backoff_max_seconds=8.0,
                sleep_fn=sleep_calls.append,
            )

        client.generate("test")

        assert len(sleep_calls) == 1
        assert sleep_calls[0] == 0.5  # base * 2^0

    def test_sleep_increases_on_multiple_retries(self):
        sleep_calls: list[float] = []
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.side_effect = [
            ConnectionError("1"),
            ConnectionError("2"),
            _make_genai_response("ok"),
        ]

        with patch("app.services.gemini_client.genai.Client", return_value=mock_sdk):
            client = GeminiClient(
                api_key="key",
                model_name="model",
                max_retries=2,
                backoff_base_seconds=1.0,
                backoff_max_seconds=100.0,
                sleep_fn=sleep_calls.append,
            )

        client.generate("test")

        assert len(sleep_calls) == 2
        assert sleep_calls[0] == 1.0  # 1.0 * 2^0
        assert sleep_calls[1] == 2.0  # 1.0 * 2^1

    def test_wait_caps_retry_after_at_backoff_max(self):
        """_wait must cap the delay at _backoff_max_seconds even with retry_after."""
        sleep_calls: list[float] = []
        mock_sdk = MagicMock()

        with patch("app.services.gemini_client.genai.Client", return_value=mock_sdk):
            client = GeminiClient(
                api_key="key",
                model_name="model",
                max_retries=0,
                backoff_base_seconds=0.5,
                backoff_max_seconds=5.0,
                sleep_fn=sleep_calls.append,
            )

        client._wait(0, retry_after=100.0)

        assert len(sleep_calls) == 1
        assert sleep_calls[0] == 5.0  # capped at max

    def test_negative_retry_after_clamped_to_zero(self):
        sleep_calls: list[float] = []
        mock_sdk = MagicMock()

        with patch("app.services.gemini_client.genai.Client", return_value=mock_sdk):
            client = GeminiClient(
                api_key="key",
                model_name="model",
                backoff_max_seconds=10.0,
                sleep_fn=sleep_calls.append,
            )

        client._wait(0, retry_after=-5.0)

        assert sleep_calls[0] == 0.0


# ---------------------------------------------------------------------------
# 13. Provider selection for Gemini
# ---------------------------------------------------------------------------

class TestProviderSelection:
    """Verify get_reasoning_client() and get_gemini_client() factory functions."""

    def test_gemini_provider_returns_gemini_client(self):
        with patch("app.services.gemini_client.settings") as mock_settings:
            mock_settings.REASONING_LLM_PROVIDER = "gemini"
            mock_settings.GEMINI_API_KEY = "fake-key"
            mock_settings.GEMINI_MODEL = "gemini-test"
            mock_settings.GEMINI_TIMEOUT_SECONDS = 10.0
            mock_settings.GEMINI_MAX_RETRIES = 1
            mock_settings.GEMINI_BACKOFF_BASE_SECONDS = 0.5
            mock_settings.GEMINI_BACKOFF_MAX_SECONDS = 8.0
            mock_settings.GEMINI_STRUCTURED_CORRECTION_RETRIES = 1

            client = get_reasoning_client()

        assert isinstance(client, GeminiClient)

    def test_gemini_provider_case_insensitive(self):
        with patch("app.services.gemini_client.settings") as mock_settings:
            mock_settings.REASONING_LLM_PROVIDER = "  GEMINI  "
            mock_settings.GEMINI_API_KEY = "fake-key"
            mock_settings.GEMINI_MODEL = "gemini-test"
            mock_settings.GEMINI_TIMEOUT_SECONDS = 10.0
            mock_settings.GEMINI_MAX_RETRIES = 1
            mock_settings.GEMINI_BACKOFF_BASE_SECONDS = 0.5
            mock_settings.GEMINI_BACKOFF_MAX_SECONDS = 8.0
            mock_settings.GEMINI_STRUCTURED_CORRECTION_RETRIES = 1

            client = get_reasoning_client()

        assert isinstance(client, GeminiClient)

    def test_get_gemini_client_factory(self):
        with patch("app.services.gemini_client.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "fake-key"
            mock_settings.GEMINI_MODEL = "gemini-test"
            mock_settings.GEMINI_TIMEOUT_SECONDS = 30.0
            mock_settings.GEMINI_MAX_RETRIES = 3
            mock_settings.GEMINI_BACKOFF_BASE_SECONDS = 0.5
            mock_settings.GEMINI_BACKOFF_MAX_SECONDS = 8.0
            mock_settings.GEMINI_STRUCTURED_CORRECTION_RETRIES = 1

            client = get_gemini_client()

        assert isinstance(client, GeminiClient)


# ---------------------------------------------------------------------------
# 14. Unsupported provider handling
# ---------------------------------------------------------------------------

class TestUnsupportedProvider:
    """Verify unsupported provider raises clear error."""

    def test_unsupported_provider_raises(self):
        with patch("app.services.gemini_client.settings") as mock_settings:
            mock_settings.REASONING_LLM_PROVIDER = "unsupported"

            with pytest.raises(
                GeminiClientError, match="Unsupported reasoning LLM provider"
            ):
                get_reasoning_client()

    def test_empty_provider_raises(self):
        with patch("app.services.gemini_client.settings") as mock_settings:
            mock_settings.REASONING_LLM_PROVIDER = ""

            with pytest.raises(GeminiClientError, match="Unsupported"):
                get_reasoning_client()


# ---------------------------------------------------------------------------
# 15. Gemini-specific response parsing and error handling
# ---------------------------------------------------------------------------

class TestGeminiSpecificBehavior:
    """Verify Gemini-SDK-specific parsing, error handling, and credential redaction."""

    # -- _failure_kind classification --

    def test_genai_api_error_500_is_transient(self):
        assert GeminiClient._failure_kind(_make_api_error(500)) == "transient"

    def test_genai_api_error_429_is_rate_limit(self):
        assert GeminiClient._failure_kind(_make_api_error(429)) == "rate_limit"

    def test_genai_api_error_408_is_timeout(self):
        assert GeminiClient._failure_kind(_make_api_error(408)) == "timeout"

    def test_genai_api_error_400_is_permanent(self):
        assert GeminiClient._failure_kind(_make_api_error(400)) == "permanent"

    def test_genai_api_error_599_is_transient(self):
        assert GeminiClient._failure_kind(_make_api_error(599)) == "transient"

    def test_runtime_error_is_permanent(self):
        assert GeminiClient._failure_kind(RuntimeError("x")) == "permanent"

    # -- _status_code extraction --

    def test_status_code_from_genai_api_error(self):
        err = _make_api_error(429)
        assert GeminiClient._status_code(err) == 429

    def test_status_code_from_generic_attribute(self):
        err = Exception("test")
        err.status_code = 503
        assert GeminiClient._status_code(err) == 503

    def test_status_code_none_for_plain_exception(self):
        assert GeminiClient._status_code(ValueError("test")) is None

    # -- _safe_detail credential redaction --

    def test_safe_detail_redacts_api_key_parameter(self):
        err = Exception("Error api_key=sk-12345 happened")
        detail = _safe_detail(err, secret="sk-12345")
        assert "sk-12345" not in detail
        assert "[REDACTED]" in detail

    def test_safe_detail_redacts_key_marker(self):
        err = Exception("key=my_secret_key other text")
        detail = _safe_detail(err)
        assert "my_secret_key" not in detail
        assert "[REDACTED]" in detail

    def test_safe_detail_redacts_authorization_header(self):
        """_safe_detail redacts the value between the Authorization: marker and
        the next delimiter.  With 'Authorization: Bearer sk-abcdef', the space
        after ':' is the delimiter so ' Bearer' is redacted."""
        err = Exception('Authorization: Bearer sk-abcdef more text')
        detail = _safe_detail(err)
        assert "Bearer" not in detail or "[REDACTED]" in detail

    def test_safe_detail_truncates_long_messages(self):
        long_msg = "x" * (MAX_ERROR_DETAIL_LENGTH + 500)
        err = Exception(long_msg)
        detail = _safe_detail(err)
        assert len(detail) <= MAX_ERROR_DETAIL_LENGTH + 5  # +5 for ellipsis char

    def test_safe_detail_returns_class_name_for_empty_str(self):
        err = Exception("")
        detail = _safe_detail(err)
        assert detail == "Exception"

    def test_safe_detail_secret_parameter_redaction(self):
        err = Exception("Something with my-secret-key in it")
        detail = _safe_detail(err, secret="my-secret-key")
        assert "my-secret-key" not in detail
        assert "[REDACTED]" in detail

    # -- generate_with_image --

    def test_generate_with_image_returns_text(self):
        mock_sdk = MagicMock()
        mock_sdk.models.generate_content.return_value = _make_genai_response(
            "Image shows a cat"
        )
        client = _make_client(mock_sdk)

        result = client.generate_with_image("Describe this image", b"\x89PNG\r\n")

        assert result == "Image shows a cat"

    def test_generate_with_image_invalid_bytes_raises(self):
        """If genai_types.Part.from_bytes fails, a GeminiClientError is raised."""
        mock_sdk = MagicMock()
        client = _make_client(mock_sdk)

        with patch(
            "app.services.gemini_client.genai_types.Part.from_bytes",
            side_effect=ValueError("invalid bytes"),
        ):
            with pytest.raises(
                GeminiClientError, match="could not be prepared"
            ):
                client.generate_with_image("test", b"bad")

    # -- Constructor defaults --

    def test_negative_max_retries_clamped_to_zero(self):
        mock_sdk = MagicMock()
        client = _make_client(mock_sdk, max_retries=-5)
        assert client._max_retries == 0

    def test_negative_backoff_clamped_to_zero(self):
        mock_sdk = MagicMock()
        client = _make_client(mock_sdk, backoff_base=-1.0, backoff_max=-2.0)
        assert client._backoff_base_seconds == 0.0
        assert client._backoff_max_seconds == 0.0

    def test_negative_correction_retries_clamped_to_zero(self):
        mock_sdk = MagicMock()
        client = _make_client(mock_sdk, correction_retries=-3)
        assert client._structured_correction_retries == 0

    # -- _validate_structured_output static method --

    def test_validate_structured_output_valid_json(self):
        result = GeminiClient._validate_structured_output(
            '{"name": "test", "value": 42}', SimpleSchema
        )
        assert isinstance(result, SimpleSchema)
        assert result.name == "test"

    def test_validate_structured_output_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            GeminiClient._validate_structured_output("not json", SimpleSchema)

    def test_validate_structured_output_wrong_schema_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            GeminiClient._validate_structured_output(
                '{"wrong": "fields"}', SimpleSchema
            )
