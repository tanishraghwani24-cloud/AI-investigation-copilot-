"""Round 4 edge-case tests for sparse and malformed reasoning inputs."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.agents.reasoning_agent import HypothesesResponse, reasoning_agent
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    Hypothesis,
    InvestigationState,
    Transaction,
    create_initial_state,
)


def _state(*, transactions: list[Transaction] | None = None) -> InvestigationState:
    return create_initial_state(
        "CASE-REASONING-EDGE",
        CaseInput(transactions=transactions or []),
    )


def _hypotheses(*, supporting: list[str] | None = None) -> HypothesesResponse:
    evidence = supporting or []
    return HypothesesResponse(
        hypotheses=[
            Hypothesis(
                hypothesis_id="HYP-EDGE-1",
                title="Potentially unusual activity",
                description="The available information may warrant further review.",
                confidence=0.85,
                supporting_evidence=evidence,
                contradicting_evidence=evidence,
            ),
            Hypothesis(
                hypothesis_id="HYP-EDGE-2",
                title="Potentially legitimate activity",
                description="The available information may have an ordinary explanation.",
                confidence=0.7,
                supporting_evidence=evidence,
                contradicting_evidence=evidence,
            ),
        ]
    )


def _run_with_response(state: InvestigationState, response: object):
    client = MagicMock()
    client.generate.return_value = response
    with patch("app.agents.reasoning_agent.get_gemini_client", return_value=client):
        return reasoning_agent(state), client


def test_zero_documents_returns_conservative_valid_hypotheses() -> None:
    transaction = Transaction(
        transaction_id="TXN-EDGE-1", amount=100.0,
        timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
        sender_account="ACC-SOURCE", receiver_account="ACC-DESTINATION",
        transaction_type="WIRE",
    )
    result, _ = _run_with_response(
        _state(transactions=[transaction]),
        _hypotheses(supporting=["TXN-EDGE-1 was submitted for review"]),
    )

    reasoning = result["investigation_reasoning"]
    assert reasoning.status == AgentStatus.COMPLETED
    assert len(reasoning.hypotheses) == 2
    assert all(hypothesis.confidence <= 0.5 for hypothesis in reasoning.hypotheses)
    assert all("investigative possibility" in hypothesis.description.lower()
               for hypothesis in reasoning.hypotheses)


def test_minimal_case_input_does_not_crash() -> None:
    result, _ = _run_with_response(_state(), _hypotheses())

    reasoning = result["investigation_reasoning"]
    assert reasoning.status == AgentStatus.COMPLETED
    assert len(reasoning.hypotheses) == 2
    assert all(hypothesis.supporting_evidence == [] for hypothesis in reasoning.hypotheses)


def test_missing_context_does_not_allow_fabricated_evidence() -> None:
    state = _state()
    assert state.context_intelligence is None
    result, _ = _run_with_response(
        state,
        _hypotheses(supporting=["DOC-INVENTED-9 confirms illicit activity"]),
    )

    reasoning = result["investigation_reasoning"]
    assert all(hypothesis.supporting_evidence == [] for hypothesis in reasoning.hypotheses)
    assert all(hypothesis.contradicting_evidence == [] for hypothesis in reasoning.hypotheses)


def test_malformed_first_response_retries_once_and_accepts_valid_response() -> None:
    malformed = {"hypotheses": [{"hypothesis_id": "HYP-BAD"}]}
    client = MagicMock()
    client.generate.side_effect = [malformed, _hypotheses()]
    with patch("app.agents.reasoning_agent.get_gemini_client", return_value=client):
        result = reasoning_agent(_state())

    assert result["investigation_reasoning"].status == AgentStatus.COMPLETED
    assert len(result["investigation_reasoning"].hypotheses) == 2
    assert client.generate.call_count == 2


def test_malformed_both_responses_fails_safely() -> None:
    client = MagicMock()
    client.generate.side_effect = ["not valid structured output", {"hypotheses": [{}]}]
    with patch("app.agents.reasoning_agent.get_gemini_client", return_value=client):
        result = reasoning_agent(_state())

    reasoning = result["investigation_reasoning"]
    assert reasoning.status == AgentStatus.FAILED
    assert reasoning.hypotheses == []
    assert client.generate.call_count == 2


def test_sparse_evidence_rejects_unknown_references() -> None:
    transaction = Transaction(
        transaction_id="TXN-REAL-1", amount=100.0,
        timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
        sender_account="ACC-REAL", receiver_account="ACC-DESTINATION",
        transaction_type="WIRE",
    )
    result, _ = _run_with_response(
        _state(transactions=[transaction]),
        _hypotheses(supporting=["TXN-REAL-1 and DOC-NOT-REAL-1 prove fraud"]),
    )

    reasoning = result["investigation_reasoning"]
    assert all(hypothesis.supporting_evidence == [] for hypothesis in reasoning.hypotheses)


def test_round_three_multi_hypothesis_behavior_remains_for_normal_input() -> None:
    transaction = Transaction(
        transaction_id="TXN-RICH-1", amount=20_000.0,
        timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
        sender_account="ACC-RICH", receiver_account="ACC-DESTINATION",
        transaction_type="WIRE",
    )
    result, _ = _run_with_response(
        _state(transactions=[transaction]),
        _hypotheses(supporting=["TXN-RICH-1 was flagged"]),
    )

    hypotheses = result["investigation_reasoning"].hypotheses
    assert len(hypotheses) >= 2
    assert {hypothesis.title for hypothesis in hypotheses} == {
        "Potentially unusual activity", "Potentially legitimate activity",
    }
