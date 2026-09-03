"""Unit tests for OllamaClient reliability behavior and provider selection.

All HTTP interactions are mocked — no live Ollama server required.
Tests verify the exact existing behavior documented in ollama_client.py:
retry logic, backoff, structured-output correction, exception typing,
and provider selection via get_reasoning_client().
"""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
from pydantic import BaseModel

from app.services.gemini_client import (
    GeminiClientError,
    GeminiRateLimitError,
    GeminiStructuredOutputError,
    GeminiTimeoutError,
    GeminiTransientError,
    get_reasoning_client,
)
from app.services.ollama_client import OllamaClient


# ── Test schema ──────────────────────────────────────────────────────

class SimpleSchema(BaseModel):
    name: str
    value: int


# ── Helpers ──────────────────────────────────────────────────────────

def _ok_response(body: dict) -> httpx.Response:
    """Build a successful httpx.Response with the given JSON body."""
    return httpx.Response(
        status_code=200,
        json=body,
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )


def _error_response(status_code: int) -> httpx.Response:
    """Build an httpx.Response that will raise HTTPStatusError on raise_for_status."""
    resp = httpx.Response(
        status_code=status_code,
        text=f"Error {status_code}",
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )
    return resp


def _make_client(
    mock_http: httpx.Client | MagicMock,
    *,
    max_retries: int = 0,
    backoff_base: float = 0.0,
    backoff_max: float = 0.0,
    correction_retries: int = 1,
) -> OllamaClient:
    """Create an OllamaClient with an injected mock http_client and no-op sleep."""
    return OllamaClient(
        base_url="http://localhost:11434",
        model_name="test-model",
        max_retries=max_retries,
        backoff_base_seconds=backoff_base,
        backoff_max_seconds=backoff_max,
        structured_correction_retries=correction_retries,
        sleep_fn=lambda _: None,  # no-op to keep tests fast
        http_client=mock_http,
    )


# ══════════════════════════════════════════════════════════════════════
# 1. Successful generation
# ══════════════════════════════════════════════════════════════════════


class TestSuccessfulGeneration:
    """Verify normal text and structured-output generation paths."""

    def test_raw_text_generation(self):
        mock = MagicMock(spec=httpx.Client)
        mock.post.return_value = _ok_response({"response": "Hello, world!"})
        client = _make_client(mock)

        result = client.generate("Say hello")

        assert result == "Hello, world!"
        mock.post.assert_called_once()

    def test_structured_output_generation(self):
        valid_json = json.dumps({"name": "test", "value": 42})
        mock = MagicMock(spec=httpx.Client)
        mock.post.return_value = _ok_response({"response": valid_json})
        client = _make_client(mock)

        result = client.generate("Give me data", response_schema=SimpleSchema)

        assert isinstance(result, SimpleSchema)
        assert result.name == "test"
        assert result.value == 42


# ══════════════════════════════════════════════════════════════════════
# 2. Empty response handling
# ══════════════════════════════════════════════════════════════════════


class TestEmptyResponse:
    """Verify behavior when Ollama returns empty or missing text."""

    def test_empty_text_raises_for_raw_generation(self):
        mock = MagicMock(spec=httpx.Client)
        mock.post.return_value = _ok_response({"response": "   "})
        client = _make_client(mock)

        with pytest.raises(GeminiClientError, match="empty text response"):
            client.generate("Say something")

    def test_missing_response_key_raises_for_raw_generation(self):
        mock = MagicMock(spec=httpx.Client)
        mock.post.return_value = _ok_response({"model": "test"})
        client = _make_client(mock)

        with pytest.raises(GeminiClientError, match="empty text response"):
            client.generate("Say something")

    def test_missing_response_key_returns_empty_for_structured(self):
        """When response_schema is set and response key is missing,
        _request returns "" which then fails JSON parsing in generate()."""
        mock = MagicMock(spec=httpx.Client)
        # First call: missing response key -> returns ""
        # Correction call: also returns invalid
        mock.post.return_value = _ok_response({"model": "test"})
        client = _make_client(mock, correction_retries=0)

        with pytest.raises(GeminiStructuredOutputError):
            client.generate("Give data", response_schema=SimpleSchema)


# ══════════════════════════════════════════════════════════════════════
# 3–6. HTTP error classification and retries
# ══════════════════════════════════════════════════════════════════════


class TestHTTPErrorHandling:
    """Verify correct exception types for HTTP status codes."""

    def test_http_429_raises_rate_limit_error(self):
        mock = MagicMock(spec=httpx.Client)
        resp = _error_response(429)
        mock.post.return_value = resp
        client = _make_client(mock)

        with pytest.raises(GeminiRateLimitError):
            client.generate("test")

    def test_http_408_raises_timeout_error(self):
        mock = MagicMock(spec=httpx.Client)
        resp = _error_response(408)
        mock.post.return_value = resp
        client = _make_client(mock)

        with pytest.raises(GeminiTimeoutError):
            client.generate("test")

    def test_http_500_raises_transient_error(self):
        mock = MagicMock(spec=httpx.Client)
        resp = _error_response(500)
        mock.post.return_value = resp
        client = _make_client(mock)

        with pytest.raises(GeminiTransientError):
            client.generate("test")

    def test_http_503_raises_transient_error(self):
        mock = MagicMock(spec=httpx.Client)
        resp = _error_response(503)
        mock.post.return_value = resp
        client = _make_client(mock)

        with pytest.raises(GeminiTransientError):
            client.generate("test")

    def test_http_400_raises_permanent_client_error(self):
        mock = MagicMock(spec=httpx.Client)
        resp = _error_response(400)
        mock.post.return_value = resp
        client = _make_client(mock)

        with pytest.raises(GeminiClientError):
            client.generate("test")


# ══════════════════════════════════════════════════════════════════════
# 7. Connection/network failures
# ══════════════════════════════════════════════════════════════════════


class TestNetworkFailures:
    """Verify that connection and network errors are treated as transient."""

    def test_connection_error_raises_transient(self):
        mock = MagicMock(spec=httpx.Client)
        mock.post.side_effect = httpx.ConnectError("Connection refused")
        client = _make_client(mock)

        with pytest.raises(GeminiTransientError):
            client.generate("test")

    def test_httpx_timeout_exception_raises_timeout_error(self):
        mock = MagicMock(spec=httpx.Client)
        mock.post.side_effect = httpx.ReadTimeout("Read timed out")
        client = _make_client(mock)

        with pytest.raises(GeminiTimeoutError):
            client.generate("test")

    def test_os_error_raises_transient(self):
        mock = MagicMock(spec=httpx.Client)
        mock.post.side_effect = OSError("Network unreachable")
        client = _make_client(mock)

        with pytest.raises(GeminiTransientError):
            client.generate("test")


# ══════════════════════════════════════════════════════════════════════
# 8. Permanent failures
# ══════════════════════════════════════════════════════════════════════


class TestPermanentFailures:
    """Verify that unrecognized errors raise GeminiClientError immediately."""

    def test_unexpected_exception_raises_client_error_immediately(self):
        mock = MagicMock(spec=httpx.Client)
        mock.post.side_effect = RuntimeError("Unexpected")
        client = _make_client(mock, max_retries=2)

        with pytest.raises(GeminiClientError, match="Ollama API call failed"):
            client.generate("test")

        # Permanent errors should NOT retry
        assert mock.post.call_count == 1


# ══════════════════════════════════════════════════════════════════════
# 9. Retry count and retry exhaustion
# ══════════════════════════════════════════════════════════════════════


class TestRetryBehavior:
    """Verify exact retry counts and exhaustion behavior."""

    def test_retries_on_transient_error_then_succeeds(self):
        mock = MagicMock(spec=httpx.Client)
        fail_resp = _error_response(500)
        ok_resp = _ok_response({"response": "recovered"})
        mock.post.side_effect = [fail_resp, ok_resp]
        client = _make_client(mock, max_retries=1)

        result = client.generate("test")

        assert result == "recovered"
        assert mock.post.call_count == 2

    def test_retries_exhausted_on_transient_error(self):
        mock = MagicMock(spec=httpx.Client)
        fail_resp = _error_response(502)
        mock.post.return_value = fail_resp
        client = _make_client(mock, max_retries=2)

        with pytest.raises(GeminiTransientError):
            client.generate("test")

        # initial attempt + 2 retries = 3 total calls
        assert mock.post.call_count == 3

    def test_retries_on_timeout_then_succeeds(self):
        mock = MagicMock(spec=httpx.Client)
        ok_resp = _ok_response({"response": "done"})
        mock.post.side_effect = [httpx.ReadTimeout("timeout"), ok_resp]
        client = _make_client(mock, max_retries=1)

        result = client.generate("test")

        assert result == "done"
        assert mock.post.call_count == 2

    def test_retries_exhausted_on_rate_limit(self):
        mock = MagicMock(spec=httpx.Client)
        fail_resp = _error_response(429)
        mock.post.return_value = fail_resp
        client = _make_client(mock, max_retries=1)

        with pytest.raises(GeminiRateLimitError):
            client.generate("test")

        assert mock.post.call_count == 2

    def test_zero_retries_fails_immediately_on_transient(self):
        mock = MagicMock(spec=httpx.Client)
        fail_resp = _error_response(500)
        mock.post.return_value = fail_resp
        client = _make_client(mock, max_retries=0)

        with pytest.raises(GeminiTransientError):
            client.generate("test")

        assert mock.post.call_count == 1


# ══════════════════════════════════════════════════════════════════════
# 10. Backoff behavior
# ══════════════════════════════════════════════════════════════════════


class TestBackoffBehavior:
    """Verify exponential backoff calculation and capping."""

    def test_backoff_delay_exponential(self):
        mock = MagicMock(spec=httpx.Client)
        client = _make_client(mock, backoff_base=1.0, backoff_max=100.0)

        assert client._backoff_delay(0) == 1.0   # 1.0 * 2^0
        assert client._backoff_delay(1) == 2.0   # 1.0 * 2^1
        assert client._backoff_delay(2) == 4.0   # 1.0 * 2^2
        assert client._backoff_delay(3) == 8.0   # 1.0 * 2^3

    def test_backoff_delay_capped_at_max(self):
        mock = MagicMock(spec=httpx.Client)
        client = _make_client(mock, backoff_base=1.0, backoff_max=5.0)

        assert client._backoff_delay(0) == 1.0
        assert client._backoff_delay(1) == 2.0
        assert client._backoff_delay(2) == 4.0
        assert client._backoff_delay(3) == 5.0  # capped
        assert client._backoff_delay(10) == 5.0  # still capped

    def test_sleep_called_on_retry(self):
        sleep_calls: list[float] = []
        mock = MagicMock(spec=httpx.Client)
        ok_resp = _ok_response({"response": "ok"})
        mock.post.side_effect = [httpx.ReadTimeout("t"), ok_resp]
        client = OllamaClient(
            base_url="http://localhost:11434",
            model_name="test",
            max_retries=1,
            backoff_base_seconds=0.5,
            backoff_max_seconds=8.0,
            sleep_fn=sleep_calls.append,
            http_client=mock,
        )

        client.generate("test")

        assert len(sleep_calls) == 1
        assert sleep_calls[0] == 0.5  # base * 2^0


# ══════════════════════════════════════════════════════════════════════
# 11–13. Structured-output validation and correction
# ══════════════════════════════════════════════════════════════════════


class TestStructuredOutputValidation:
    """Verify JSON parsing, Pydantic validation, and correction retries."""

    def test_invalid_json_triggers_correction(self):
        mock = MagicMock(spec=httpx.Client)
        valid_json = json.dumps({"name": "fixed", "value": 1})
        mock.post.side_effect = [
            _ok_response({"response": "not json at all"}),
            _ok_response({"response": valid_json}),
        ]
        client = _make_client(mock, correction_retries=1)

        result = client.generate("test", response_schema=SimpleSchema)

        assert isinstance(result, SimpleSchema)
        assert result.name == "fixed"
        assert mock.post.call_count == 2

    def test_pydantic_validation_failure_triggers_correction(self):
        mock = MagicMock(spec=httpx.Client)
        bad_json = json.dumps({"name": "test"})  # missing required 'value'
        good_json = json.dumps({"name": "test", "value": 99})
        mock.post.side_effect = [
            _ok_response({"response": bad_json}),
            _ok_response({"response": good_json}),
        ]
        client = _make_client(mock, correction_retries=1)

        result = client.generate("test", response_schema=SimpleSchema)

        assert isinstance(result, SimpleSchema)
        assert result.value == 99

    def test_correction_retries_exhausted_raises_structured_output_error(self):
        mock = MagicMock(spec=httpx.Client)
        mock.post.return_value = _ok_response({"response": "not json"})
        client = _make_client(mock, correction_retries=2)

        with pytest.raises(GeminiStructuredOutputError, match="Failed to parse"):
            client.generate("test", response_schema=SimpleSchema)

        # 1 original + 2 correction attempts = 3 calls
        assert mock.post.call_count == 3

    def test_zero_correction_retries_fails_immediately(self):
        mock = MagicMock(spec=httpx.Client)
        mock.post.return_value = _ok_response({"response": "not json"})
        client = _make_client(mock, correction_retries=0)

        with pytest.raises(GeminiStructuredOutputError):
            client.generate("test", response_schema=SimpleSchema)

        assert mock.post.call_count == 1


# ══════════════════════════════════════════════════════════════════════
# 14. Exception typing and chain
# ══════════════════════════════════════════════════════════════════════


class TestExceptionTyping:
    """Verify exception hierarchy and original_error chaining."""

    def test_rate_limit_is_subclass_of_transient(self):
        assert issubclass(GeminiRateLimitError, GeminiTransientError)

    def test_timeout_is_subclass_of_transient(self):
        assert issubclass(GeminiTimeoutError, GeminiTransientError)

    def test_transient_is_subclass_of_client_error(self):
        assert issubclass(GeminiTransientError, GeminiClientError)

    def test_structured_output_is_subclass_of_client_error(self):
        assert issubclass(GeminiStructuredOutputError, GeminiClientError)

    def test_original_error_preserved_on_timeout(self):
        mock = MagicMock(spec=httpx.Client)
        original = httpx.ReadTimeout("read timed out")
        mock.post.side_effect = original
        client = _make_client(mock)

        with pytest.raises(GeminiTimeoutError) as exc_info:
            client.generate("test")

        assert exc_info.value.original_error is original

    def test_original_error_preserved_on_structured_output_failure(self):
        mock = MagicMock(spec=httpx.Client)
        mock.post.return_value = _ok_response({"response": "not json"})
        client = _make_client(mock, correction_retries=0)

        with pytest.raises(GeminiStructuredOutputError) as exc_info:
            client.generate("test", response_schema=SimpleSchema)

        assert exc_info.value.original_error is not None


# ══════════════════════════════════════════════════════════════════════
# 15. Provider selection
# ══════════════════════════════════════════════════════════════════════


class TestProviderSelection:
    """Verify get_reasoning_client() returns the correct client type."""

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
            mock_settings.LLM_PRIMARY_PROVIDER = "gemini"
            mock_settings.LLM_FALLBACK_PROVIDER = "none"

            client = get_reasoning_client()

        from app.services.gemini_client import GeminiClient
        assert isinstance(client, GeminiClient)

    def test_ollama_provider_returns_ollama_client(self):
        with patch("app.services.gemini_client.settings") as mock_settings:
            mock_settings.REASONING_LLM_PROVIDER = "ollama"
            mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
            mock_settings.OLLAMA_MODEL = "test-model"
            mock_settings.OLLAMA_TIMEOUT_SECONDS = 60.0
            mock_settings.OLLAMA_MAX_RETRIES = 1
            mock_settings.OLLAMA_BACKOFF_BASE_SECONDS = 0.5
            mock_settings.OLLAMA_BACKOFF_MAX_SECONDS = 8.0
            mock_settings.OLLAMA_STRUCTURED_CORRECTION_RETRIES = 1
            mock_settings.OLLAMA_KEEP_ALIVE = "5m"
            mock_settings.OLLAMA_NUM_CTX = 2048
            mock_settings.OLLAMA_NUM_PREDICT = 1024
            mock_settings.OLLAMA_TEMPERATURE = 0.0

            client = get_reasoning_client()

        assert isinstance(client, OllamaClient)

    def test_unsupported_provider_raises_client_error(self):
        with patch("app.services.gemini_client.settings") as mock_settings:
            mock_settings.REASONING_LLM_PROVIDER = "unsupported"

            with pytest.raises(GeminiClientError, match="Unsupported reasoning LLM provider"):
                get_reasoning_client()


# ══════════════════════════════════════════════════════════════════════
# Failure kind classification (static method, fast to test)
# ══════════════════════════════════════════════════════════════════════


class TestFailureKindClassification:
    """Verify _failure_kind correctly classifies different error types."""

    def test_httpx_timeout_is_timeout(self):
        assert OllamaClient._failure_kind(httpx.ReadTimeout("t")) == "timeout"
        assert OllamaClient._failure_kind(httpx.ConnectTimeout("t")) == "timeout"

    def test_python_timeout_error_is_timeout(self):
        assert OllamaClient._failure_kind(TimeoutError("t")) == "timeout"

    def test_connection_error_is_transient(self):
        assert OllamaClient._failure_kind(ConnectionError("c")) == "transient"
        assert OllamaClient._failure_kind(httpx.ConnectError("c")) == "transient"

    def test_os_error_is_transient(self):
        assert OllamaClient._failure_kind(OSError("o")) == "transient"

    def test_runtime_error_is_permanent(self):
        assert OllamaClient._failure_kind(RuntimeError("r")) == "permanent"

    def test_http_status_429_is_rate_limit(self):
        resp = _error_response(429)
        error = httpx.HTTPStatusError("429", request=resp.request, response=resp)
        assert OllamaClient._failure_kind(error) == "rate_limit"

    def test_http_status_408_is_timeout(self):
        resp = _error_response(408)
        error = httpx.HTTPStatusError("408", request=resp.request, response=resp)
        assert OllamaClient._failure_kind(error) == "timeout"

    def test_http_status_500_is_transient(self):
        resp = _error_response(500)
        error = httpx.HTTPStatusError("500", request=resp.request, response=resp)
        assert OllamaClient._failure_kind(error) == "transient"

    def test_http_status_400_is_permanent(self):
        resp = _error_response(400)
        error = httpx.HTTPStatusError("400", request=resp.request, response=resp)
        assert OllamaClient._failure_kind(error) == "permanent"
