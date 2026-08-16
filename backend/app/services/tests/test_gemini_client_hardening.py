"""Deterministic unit tests for GeminiClient hardening."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from google.genai.errors import ClientError, ServerError
from pydantic import BaseModel

from app.services.gemini_client import (
    GeminiClient,
    GeminiRateLimitError,
    GeminiStructuredOutputError,
    GeminiTimeoutError,
    GeminiTransientError,
)


class SampleOutput(BaseModel):
    label: str
    score: float


def _response(text: str) -> SimpleNamespace:
    return SimpleNamespace(text=text)


def _client(
    responses: list[object],
    *,
    sleep: MagicMock | None = None,
    **kwargs: object,
) -> tuple[GeminiClient, MagicMock]:
    with patch("app.services.gemini_client.genai") as mock_genai:
        sdk_client = mock_genai.Client.return_value
        sdk_client.models.generate_content.side_effect = responses
        client = GeminiClient(
            api_key="test-secret",
            model_name="test-model",
            sleep_fn=sleep or MagicMock(),
            **kwargs,
        )
    return client, sdk_client.models.generate_content


def test_raw_text_generation_remains_compatible() -> None:
    client, generate_content = _client([_response("hello")])

    assert client.generate("Say hello") == "hello"
    generate_content.assert_called_once_with(model="test-model", contents="Say hello")


def test_structured_generation_returns_validated_model() -> None:
    client, _ = _client([_response('{"label":"fraud","score":0.9}')])

    result = client.generate("Extract", response_schema=SampleOutput)

    assert isinstance(result, SampleOutput)
    assert result.label == "fraud"
    assert result.score == 0.9


def test_transient_500_retries_then_succeeds() -> None:
    sleep = MagicMock()
    client, generate_content = _client(
        [ServerError(500, {"message": "temporary"}), _response("ok")],
        sleep=sleep,
        max_retries=2,
        backoff_base_seconds=0.25,
    )

    assert client.generate("retry") == "ok"
    assert generate_content.call_count == 2
    sleep.assert_called_once_with(0.25)


def test_multiple_transient_failures_use_exponential_backoff() -> None:
    sleep = MagicMock()
    client, _ = _client(
        [
            ServerError(502, {"message": "temporary"}),
            ServerError(503, {"message": "temporary"}),
            _response("ok"),
        ],
        sleep=sleep,
        max_retries=2,
        backoff_base_seconds=0.25,
    )

    assert client.generate("retry") == "ok"
    assert sleep.call_args_list == [((0.25,),), ((0.5,),)]


def test_timeout_retries_then_succeeds() -> None:
    sleep = MagicMock()
    client, _ = _client(
        [TimeoutError("timed out"), _response("ok")],
        sleep=sleep,
        max_retries=1,
        backoff_base_seconds=0.1,
    )

    assert client.generate("timeout") == "ok"
    sleep.assert_called_once_with(0.1)


def test_http_408_retries_as_timeout() -> None:
    sleep = MagicMock()
    client, generate_content = _client(
        [ClientError(408, {"message": "request timed out"}), _response("ok")],
        sleep=sleep,
        max_retries=1,
        backoff_base_seconds=0.1,
    )

    assert client.generate("timeout") == "ok"
    assert generate_content.call_count == 2
    sleep.assert_called_once_with(0.1)


def test_exhausted_transient_retries_raise_clear_exception() -> None:
    client, generate_content = _client(
        [ServerError(504, {"message": "temporary"})] * 3,
        max_retries=2,
        backoff_base_seconds=0,
    )

    with pytest.raises(GeminiTransientError, match="after 2 retries"):
        client.generate("retry")
    assert generate_content.call_count == 3


def test_rate_limit_honors_retry_after_header() -> None:
    sleep = MagicMock()
    response = MagicMock(headers={"Retry-After": "2"})
    rate_limit = ClientError(429, {"message": "slow down"}, response=response)
    client, _ = _client(
        [rate_limit, _response("ok")],
        sleep=sleep,
        max_retries=1,
        backoff_max_seconds=5,
    )

    assert client.generate("rate limit") == "ok"
    sleep.assert_called_once_with(2.0)


def test_rate_limit_without_retry_after_uses_backoff() -> None:
    sleep = MagicMock()
    client, _ = _client(
        [ClientError(429, {"message": "slow down"}), _response("ok")],
        sleep=sleep,
        max_retries=1,
        backoff_base_seconds=0.4,
    )

    assert client.generate("rate limit") == "ok"
    sleep.assert_called_once_with(0.4)


def test_exhausted_rate_limits_raise_rate_limit_exception() -> None:
    client, _ = _client(
        [ClientError(429, {"message": "slow down"})] * 3,
        max_retries=2,
        backoff_base_seconds=0,
    )

    with pytest.raises(GeminiRateLimitError, match="rate limit"):
        client.generate("rate limit")


def test_malformed_structured_output_gets_bounded_correction_retry() -> None:
    client, generate_content = _client(
        [_response("not json"), _response('{"label":"fixed","score":0.8}')],
        structured_correction_retries=1,
    )

    result = client.generate("Extract", response_schema=SampleOutput)

    assert isinstance(result, SampleOutput)
    assert result.label == "fixed"
    correction_prompt = generate_content.call_args_list[1].kwargs["contents"]
    assert "previous response failed" in correction_prompt
    assert "ONLY valid JSON" in correction_prompt
    assert "Expected Pydantic schema" in correction_prompt


def test_missing_structured_response_uses_correction_retry() -> None:
    client, generate_content = _client(
        [SimpleNamespace(), _response('{"label":"fixed","score":0.8}')],
        structured_correction_retries=1,
    )

    result = client.generate("Extract", response_schema=SampleOutput)

    assert isinstance(result, SampleOutput)
    assert result.label == "fixed"
    assert generate_content.call_count == 2


def test_structured_output_that_stays_invalid_raises_dedicated_error() -> None:
    client, generate_content = _client(
        [_response("bad"), _response('{"wrong":true}')],
        structured_correction_retries=1,
    )

    with pytest.raises(GeminiStructuredOutputError, match="Failed to parse") as info:
        client.generate("Extract", response_schema=SampleOutput)

    assert generate_content.call_count == 2
    assert "test-secret" not in str(info.value)


def test_permanent_error_is_not_retried() -> None:
    client, generate_content = _client(
        [ClientError(400, {"message": "invalid request"})],
        max_retries=5,
    )

    with pytest.raises(Exception, match="Gemini API call failed"):
        client.generate("bad request")
    assert generate_content.call_count == 1


def test_timeout_exhaustion_uses_gemini_timeout_exception() -> None:
    client, _ = _client(
        [TimeoutError("network timeout")] * 2,
        max_retries=1,
        backoff_base_seconds=0,
    )

    with pytest.raises(GeminiTimeoutError, match="timed out"):
        client.generate("timeout")


def test_error_messages_redact_api_key() -> None:
    client, _ = _client(
        [ClientError(400, {"message": "api_key=test-secret invalid"})],
        max_retries=0,
    )

    with pytest.raises(Exception) as info:
        client.generate("bad request")
    assert "test-secret" not in str(info.value)


def test_backoff_is_bounded() -> None:
    sleep = MagicMock()
    client, _ = _client(
        [ServerError(500, {"message": "temporary"}), _response("ok")],
        sleep=sleep,
        max_retries=1,
        backoff_base_seconds=100,
        backoff_max_seconds=2,
    )

    assert client.generate("bounded") == "ok"
    sleep.assert_called_once_with(2)


def test_timeout_configuration_is_passed_to_google_client() -> None:
    with patch("app.services.gemini_client.genai") as mock_genai:
        GeminiClient(api_key="key", model_name="model", timeout_seconds=4.5)

    kwargs = mock_genai.Client.call_args.kwargs
    assert kwargs["http_options"].timeout == 4500
