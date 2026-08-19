"""Offline unit tests for the Ollama reasoning client."""

from unittest.mock import MagicMock

import httpx
import pytest
from pydantic import BaseModel

from app.services.gemini_client import (
    GeminiClientError,
    GeminiStructuredOutputError,
    GeminiTimeoutError,
    GeminiTransientError,
)
from app.services.ollama_client import OllamaClient


class SampleOutput(BaseModel):
    label: str
    score: float


def _response(
    payload: dict | None = None,
    *,
    status_code: int = 200,
) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload or {"response": "ok"}
    response.raise_for_status.return_value = None
    return response


def _client(
    side_effect: list[object] | object,
    *,
    sleep: MagicMock | None = None,
    **kwargs: object,
) -> tuple[OllamaClient, MagicMock]:
    http_client = MagicMock()
    if isinstance(side_effect, list):
        http_client.post.side_effect = side_effect
    elif isinstance(side_effect, Exception):
        http_client.post.side_effect = side_effect
    else:
        http_client.post.return_value = side_effect
    client = OllamaClient(
        base_url="http://localhost:11434",
        model_name="llama3.1:8b",
        http_client=http_client,
        sleep_fn=sleep or MagicMock(),
        **kwargs,
    )
    return client, http_client.post


def test_plain_response_succeeds() -> None:
    client, post = _client(_response({"response": "plain text"}))

    assert client.generate("Hello") == "plain text"
    call = post.call_args
    assert call.args[0] == "/api/generate"
    assert call.kwargs["json"]["model"] == "llama3.1:8b"
    assert call.kwargs["json"]["prompt"] == "Hello"
    assert call.kwargs["json"]["stream"] is False


def test_advanced_inference_options_sent() -> None:
    client, post = _client(
        _response({"response": "advanced"}),
        keep_alive="5m",
        options={"temperature": 0.0, "num_ctx": 2048},
    )

    client.generate("Hello")
    call = post.call_args
    assert call.kwargs["json"]["keep_alive"] == "5m"
    assert call.kwargs["json"]["options"]["temperature"] == 0.0
    assert call.kwargs["json"]["options"]["num_ctx"] == 2048


def test_structured_response_returns_validated_model() -> None:
    client, post = _client(_response({"response": '{"label":"fraud","score":0.9}'}))

    result = client.generate("Extract", response_schema=SampleOutput)

    assert isinstance(result, SampleOutput)
    assert result.label == "fraud"
    assert result.score == 0.9
    assert call_format_is_schema(post.call_args.kwargs["json"]["format"])


def test_malformed_json_raises_when_no_correction_budget() -> None:
    client, _ = _client(
        _response({"response": "not json"}),
        structured_correction_retries=0,
    )

    with pytest.raises(GeminiStructuredOutputError, match="Failed to parse Ollama response"):
        client.generate("Extract", response_schema=SampleOutput)


def test_malformed_json_then_correction_succeeds() -> None:
    client, post = _client(
        [
            _response({"response": "not json"}),
            _response({"response": '{"label":"fixed","score":0.8}'}),
        ],
        structured_correction_retries=1,
    )

    result = client.generate("Extract", response_schema=SampleOutput)

    assert isinstance(result, SampleOutput)
    assert result.label == "fixed"
    assert post.call_count == 2
    correction_prompt = post.call_args_list[1].kwargs["json"]["prompt"]
    assert "ONLY valid JSON" in correction_prompt
    assert "Expected Pydantic schema" in correction_prompt


def test_permanently_malformed_structured_output_raises() -> None:
    client, post = _client(
        [
            _response({"response": "bad"}),
            _response({"response": '{"wrong":true}'}),
        ],
        structured_correction_retries=1,
    )

    with pytest.raises(GeminiStructuredOutputError, match="Failed to parse Ollama response"):
        client.generate("Extract", response_schema=SampleOutput)

    assert post.call_count == 2


def test_server_unavailable_raises_clear_exception() -> None:
    client, post = _client(
        httpx.ConnectError("connection refused"),
        max_retries=0,
    )

    with pytest.raises(GeminiTransientError, match="Ollama transient request failed"):
        client.generate("Hello")

    assert post.call_count == 1


def test_timeout_raises_timeout_exception() -> None:
    client, post = _client(
        httpx.ReadTimeout("timed out"),
        max_retries=0,
    )

    with pytest.raises(GeminiTimeoutError, match="Ollama request timed out"):
        client.generate("Hello")

    assert post.call_count == 1


def test_http_500_retries_then_succeeds() -> None:
    sleep = MagicMock()
    response = httpx.Response(500, request=httpx.Request("POST", "http://localhost:11434/api/generate"))
    client, post = _client(
        [
            httpx.HTTPStatusError("server error", request=response.request, response=response),
            _response({"response": "ok"}),
        ],
        sleep=sleep,
        max_retries=1,
        backoff_base_seconds=0.25,
    )

    assert client.generate("retry") == "ok"
    assert post.call_count == 2
    sleep.assert_called_once_with(0.25)


def test_invalid_http_payload_raises_client_error() -> None:
    bad_response = _response({"unexpected": True})
    client, _ = _client(bad_response)

    with pytest.raises(GeminiClientError, match="Ollama returned an empty text response"):
        client.generate("Hello")


def call_format_is_schema(value: object) -> bool:
    return isinstance(value, dict) and value.get("type") == "object"
