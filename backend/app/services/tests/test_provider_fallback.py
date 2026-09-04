"""Mocked tests for one-way Gemini -> Groq provider fallback."""

import importlib
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from app.agents.reasoning_agent import HypothesesResponse, reasoning_agent
from app.schemas.investigation_state import CaseInput, Hypothesis, create_initial_state
from app.services.gemini_client import (
    GeminiClientError,
    GeminiRateLimitError,
    GeminiTimeoutError,
    GeminiTransientError,
)
from app.services.groq_client import GroqClient
from app.services.llm_client import FallbackClient


class Output(BaseModel):
    label: str


def _router(primary: MagicMock, fallback: MagicMock) -> FallbackClient:
    return FallbackClient(primary, MagicMock(return_value=fallback))


def test_gemini_success_does_not_call_groq() -> None:
    primary, fallback = MagicMock(), MagicMock()
    primary.generate.return_value = Output(label="gemini")
    router = _router(primary, fallback)

    assert router.generate("safe", response_schema=Output).label == "gemini"
    primary.generate.assert_called_once()
    fallback.generate.assert_not_called()


def test_normal_three_stage_path_uses_exactly_three_primary_calls() -> None:
    primary, fallback = MagicMock(), MagicMock()
    primary.generate.side_effect = [Output(label="reasoning"), Output(label="compliance"), Output(label="decision")]
    router = _router(primary, fallback)

    assert [router.generate("stage", response_schema=Output).label for _ in range(3)] == [
        "reasoning", "compliance", "decision",
    ]
    assert primary.generate.call_count == 3
    fallback.generate.assert_not_called()


@pytest.mark.parametrize("error_type", [GeminiRateLimitError, GeminiTimeoutError, GeminiTransientError])
def test_terminal_gemini_availability_failure_hands_off_once(error_type: type[Exception]) -> None:
    primary, fallback = MagicMock(), MagicMock()
    primary.generate.side_effect = error_type("provider unavailable")
    fallback.generate.return_value = Output(label="groq")
    fallback_factory = MagicMock(return_value=fallback)
    router = FallbackClient(primary, fallback_factory)

    assert router.generate("safe", response_schema=Output).label == "groq"
    primary.generate.assert_called_once()
    fallback_factory.assert_called_once()
    fallback.generate.assert_called_once()


def test_authentication_or_configuration_error_does_not_fallback() -> None:
    primary, fallback = MagicMock(), MagicMock()
    primary.generate.side_effect = GeminiClientError("Gemini API call failed: 401")
    fallback_factory = MagicMock(return_value=fallback)

    with pytest.raises(GeminiClientError, match="401"):
        FallbackClient(primary, fallback_factory).generate("safe", response_schema=Output)
    fallback_factory.assert_not_called()
    fallback.generate.assert_not_called()


def test_groq_malformed_output_is_rejected_by_pydantic_validation() -> None:
    sdk = MagicMock()
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content='{"wrong": true}'))]
    sdk.chat.completions.create.return_value = response
    client = GroqClient(
        api_key="test-secret", model_name="openai/gpt-oss-20b",
        client=sdk, max_retries=0, structured_correction_retries=0,
    )

    with pytest.raises(GeminiClientError, match="Failed to parse Groq response"):
        client.generate("safe", response_schema=Output)
    assert "test-secret" not in str(sdk.mock_calls)


def test_grounding_rejection_does_not_trigger_provider_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    primary, fallback = MagicMock(), MagicMock()
    ungrounded = HypothesesResponse(hypotheses=[Hypothesis(
        hypothesis_id="HYP-1", title="Biometric evidence", description="Biometric scan found fraud.",
        confidence=0.5, supporting_evidence=["Biometric scan"], contradicting_evidence=[],
    )])
    grounded = HypothesesResponse(hypotheses=[Hypothesis(
        hypothesis_id="HYP-2", title="Evidence review", description="Available evidence needs review.",
        confidence=0.5, supporting_evidence=[], contradicting_evidence=[],
    )])
    primary.generate.side_effect = [ungrounded, grounded]
    fallback_factory = MagicMock(return_value=fallback)
    router = FallbackClient(primary, fallback_factory)
    reasoning_module = importlib.import_module("app.agents.reasoning_agent")
    monkeypatch.setattr(reasoning_module, "get_reasoning_client", lambda: router)

    result = reasoning_agent(create_initial_state("CASE-FALLBACK-1", CaseInput()))

    assert result["investigation_reasoning"].status.value == "COMPLETED"
    assert primary.generate.call_count == 2
    fallback_factory.assert_not_called()


def test_groq_invented_evidence_id_is_stripped_by_reasoning_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    primary, fallback = MagicMock(), MagicMock()
    primary.generate.side_effect = GeminiRateLimitError("rate limited")
    fallback.generate.return_value = HypothesesResponse(hypotheses=[Hypothesis(
        hypothesis_id="HYP-3", title="Evidence review", description="Available evidence needs review.",
        confidence=0.5, supporting_evidence=["TXN-INVENTED-99 proves fraud"], contradicting_evidence=[],
    )])
    router = _router(primary, fallback)
    reasoning_module = importlib.import_module("app.agents.reasoning_agent")
    monkeypatch.setattr(reasoning_module, "get_reasoning_client", lambda: router)

    result = reasoning_agent(create_initial_state("CASE-FALLBACK-2", CaseInput()))

    assert result["investigation_reasoning"].hypotheses[0].supporting_evidence == []
    fallback.generate.assert_called_once()


def test_fallback_failure_never_returns_to_gemini() -> None:
    primary, fallback = MagicMock(), MagicMock()
    primary.generate.side_effect = GeminiRateLimitError("rate limited")
    fallback.generate.side_effect = GeminiTransientError("Groq unavailable")
    router = _router(primary, fallback)

    with pytest.raises(GeminiTransientError, match="Groq unavailable"):
        router.generate("safe", response_schema=Output)
    primary.generate.assert_called_once()
    fallback.generate.assert_called_once()


# ── Completion-budget hardening (gpt-oss-20b reasoning truncation) ──────


def _groq_request_kwargs(model_name: str, **client_kwargs) -> dict:
    """Capture the kwargs GroqClient sends to the Groq SDK for one call."""
    sdk = MagicMock()
    sdk.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(finish_reason="stop", message=MagicMock(content='{"label": "ok"}'))],
    )
    GroqClient(
        api_key="test-secret", model_name=model_name, client=sdk,
        max_retries=0, structured_correction_retries=0, **client_kwargs,
    ).generate("safe", response_schema=Output)
    return sdk.chat.completions.create.call_args.kwargs


def test_groq_sends_max_completion_tokens_not_deprecated_max_tokens() -> None:
    kwargs = _groq_request_kwargs("openai/gpt-oss-20b", max_completion_tokens=16384)

    assert kwargs["max_completion_tokens"] == 16384
    assert "max_tokens" not in kwargs


def test_groq_caps_reasoning_effort_on_reasoning_models() -> None:
    """Chain-of-thought is what exhausts the budget, so it is capped at source."""
    assert _groq_request_kwargs("openai/gpt-oss-20b")["reasoning_effort"] == "low"


def test_groq_omits_reasoning_effort_on_non_reasoning_models() -> None:
    """Sending reasoning_effort to a plain chat model is a 400."""
    assert "reasoning_effort" not in _groq_request_kwargs("llama-3.3-70b-versatile")


def test_groq_reasoning_effort_can_be_disabled() -> None:
    assert "reasoning_effort" not in _groq_request_kwargs(
        "openai/gpt-oss-20b", reasoning_effort=None,
    )


def test_groq_uses_schema_constrained_decoding_so_json_cannot_be_malformed() -> None:
    """json_object mode is the only mode that can 400 with json_validate_failed."""
    response_format = _groq_request_kwargs("openai/gpt-oss-20b")["response_format"]

    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["name"] == "Output"
    assert response_format["json_schema"]["schema"] == Output.model_json_schema()


def test_groq_truncated_completion_fails_with_actionable_error() -> None:
    """A budget overrun must not be retried with an even longer correction prompt."""
    sdk = MagicMock()
    sdk.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(finish_reason="length", message=MagicMock(content='{"lab'))],
    )
    client = GroqClient(
        api_key="test-secret", model_name="openai/gpt-oss-20b", client=sdk,
        max_retries=0, structured_correction_retries=1,
    )

    with pytest.raises(GeminiClientError, match="completion-token limit"):
        client.generate("safe", response_schema=Output)
    sdk.chat.completions.create.assert_called_once()
    assert "test-secret" not in str(sdk.mock_calls)
