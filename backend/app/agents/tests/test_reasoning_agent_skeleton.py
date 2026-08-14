"""Tests for the Reasoning Agent skeleton (Mayur — Round 2).

All tests mock ``GeminiClient.generate()`` — no real Gemini API key
is required.

Covers:
- Agent execution without errors
- case_input is used in the prompt
- context_intelligence is used in the prompt
- GeminiClient.generate() is called with response_schema=Hypothesis
- Mocked Gemini response becomes a valid Hypothesis
- Exactly ONE hypothesis is returned
- Required Hypothesis fields are populated
- supporting_evidence is present
- contradicting_evidence is present
- confidence is valid
- reasoning_agent() returns InvestigationReasoning structure
- reasoning_node delegates to reasoning_agent
- Existing state fields are not destroyed
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.agents.reasoning_agent import reasoning_agent, _build_prompt
from app.graph.nodes.reasoning_node import reasoning_node
from app.schemas.investigation_state import (
    AgentStatus,
    ContextIntelligence,
    CaseInput,
    CurrentStage,
    CustomerProfile,
    DetectedAnomaly,
    AnomalyType,
    Hypothesis,
    InvestigationReasoning,
    InvestigationState,
    SeverityLevel,
    Transaction,
    create_initial_state,
)


# ── Fixtures ─────────────────────────────────────────────────────────


MOCK_HYPOTHESIS = Hypothesis(
    hypothesis_id="HYP-GEMINI-001",
    title="Suspected Structuring Activity",
    description=(
        "The customer appears to be structuring transactions to avoid "
        "reporting thresholds.  Multiple rapid wire transfers just below "
        "$10,000 were sent to the same beneficiary within a short window."
    ),
    confidence=0.82,
    supporting_evidence=[
        "TXN-TEST-001: $15,000 wire transfer exceeds threshold",
        "Customer risk rating: HIGH",
        "Alert triggered by automated rule engine",
    ],
    contradicting_evidence=[
        "Customer is a known Portfolio Manager with legitimate high-value activity",
    ],
)
"""A realistic Hypothesis that the mocked Gemini will return."""


def _make_context_intelligence() -> ContextIntelligence:
    """Build a realistic ContextIntelligence for testing."""
    return ContextIntelligence(
        status=AgentStatus.COMPLETED,
        context_summary=(
            "Test Customer has 2 transactions totalling $20,000.00 "
            "under investigation. 1 transaction exceeds the $10,000.00 "
            "threshold. Overall contextual risk: MEDIUM (0.45)."
        ),
        key_indicators=[
            "2 transactions totalling $20,000.00",
            "1 large transaction exceeding $10,000.00",
            "Alert: Suspicious wire transfer pattern detected",
        ],
        anomalies=[
            DetectedAnomaly(
                anomaly_id="ANOM-001",
                anomaly_type=AnomalyType.POINT,
                severity=SeverityLevel.MEDIUM,
                description="Large WIRE transaction of $15,000.00 exceeds threshold.",
                related_transactions=["TXN-TEST-001"],
            ),
        ],
        risk_score=0.45,
    )


def _make_test_state(
    *, with_context: bool = True,
) -> InvestigationState:
    """Create a realistic InvestigationState for testing."""
    transactions = [
        Transaction(
            transaction_id="TXN-TEST-001",
            amount=15_000.00,
            currency="USD",
            timestamp=datetime(2025, 8, 1, 10, 0, 0),
            sender_account="ACC-SRC-001",
            receiver_account="ACC-DST-001",
            transaction_type="WIRE",
            channel="ONLINE",
            description="Investment deposit",
        ),
        Transaction(
            transaction_id="TXN-TEST-002",
            amount=5_000.00,
            currency="USD",
            timestamp=datetime(2025, 8, 1, 10, 15, 0),
            sender_account="ACC-SRC-001",
            receiver_account="ACC-DST-002",
            transaction_type="ACH",
            channel="MOBILE",
            description="Supplier payment",
        ),
    ]
    case_input = CaseInput(
        transactions=transactions,
        customer_profile=CustomerProfile(
            customer_id="CUST-TEST-001",
            name="Test Customer",
            risk_rating="HIGH",
            occupation="Portfolio Manager",
            nationality="US",
        ),
        alert_reason="Suspicious wire transfer pattern detected",
    )
    state = create_initial_state(
        case_id="CASE-TEST-REASONING-001",
        case_input=case_input,
    )

    if with_context:
        state = state.model_copy(
            update={"context_intelligence": _make_context_intelligence()},
        )

    return state


# ── Helper: patch GeminiClient ───────────────────────────────────────


def _patch_gemini(return_value=None):
    """Return a context-manager that patches get_gemini_client."""
    mock_client = MagicMock()
    mock_client.generate.return_value = return_value or MOCK_HYPOTHESIS

    return patch(
        "app.agents.reasoning_agent.get_gemini_client",
        return_value=mock_client,
    )


# ── TEST 1: Agent execution ─────────────────────────────────────────


class TestAgentExecution:
    """reasoning_agent() executes without errors when Gemini is mocked."""

    def test_agent_returns_dict(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        assert isinstance(result, dict)

    def test_result_contains_investigation_reasoning(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        assert "investigation_reasoning" in result

    def test_investigation_reasoning_is_valid_model(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        assert isinstance(
            result["investigation_reasoning"], InvestigationReasoning,
        )

    def test_agent_status_is_completed(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        reasoning = result["investigation_reasoning"]
        assert reasoning.status == AgentStatus.COMPLETED


# ── TEST 2: case_input is used ───────────────────────────────────────


class TestCaseInputUsed:
    """The prompt sent to Gemini contains case input data."""

    def test_prompt_contains_transaction_id(self) -> None:
        state = _make_test_state()
        prompt = _build_prompt(state)
        assert "TXN-TEST-001" in prompt

    def test_prompt_contains_customer_name(self) -> None:
        state = _make_test_state()
        prompt = _build_prompt(state)
        assert "Test Customer" in prompt

    def test_prompt_contains_alert_reason(self) -> None:
        state = _make_test_state()
        prompt = _build_prompt(state)
        assert "Suspicious wire transfer pattern detected" in prompt

    def test_prompt_contains_transaction_amount(self) -> None:
        state = _make_test_state()
        prompt = _build_prompt(state)
        assert "15000.0" in prompt or "15000" in prompt


# ── TEST 3: context_intelligence is used ─────────────────────────────


class TestContextIntelligenceUsed:
    """The prompt sent to Gemini contains context intelligence data."""

    def test_prompt_contains_context_summary(self) -> None:
        state = _make_test_state()
        prompt = _build_prompt(state)
        assert "under investigation" in prompt

    def test_prompt_contains_key_indicator(self) -> None:
        state = _make_test_state()
        prompt = _build_prompt(state)
        assert "large transaction" in prompt.lower()

    def test_prompt_contains_risk_score(self) -> None:
        state = _make_test_state()
        prompt = _build_prompt(state)
        assert "0.45" in prompt

    def test_prompt_handles_missing_context(self) -> None:
        """When context_intelligence is None the prompt still builds."""
        state = _make_test_state(with_context=False)
        prompt = _build_prompt(state)
        # Should not crash, should contain empty context
        assert "CONTEXT INTELLIGENCE" in prompt


# ── TEST 4: GeminiClient.generate() called correctly ─────────────────


class TestGeminiCallSignature:
    """GeminiClient.generate() is called with the expected arguments."""

    def test_generate_called_once(self) -> None:
        state = _make_test_state()
        with _patch_gemini() as mock_factory:
            reasoning_agent(state)
            mock_client = mock_factory.return_value
            mock_client.generate.assert_called_once()

    def test_generate_uses_response_schema_hypothesis(self) -> None:
        state = _make_test_state()
        with _patch_gemini() as mock_factory:
            reasoning_agent(state)
            mock_client = mock_factory.return_value
            call_kwargs = mock_client.generate.call_args
            # response_schema should be Hypothesis
            assert call_kwargs.kwargs.get("response_schema") is Hypothesis or (
                len(call_kwargs.args) >= 2 and call_kwargs.args[1] is Hypothesis
            )

    def test_generate_receives_non_empty_prompt(self) -> None:
        state = _make_test_state()
        with _patch_gemini() as mock_factory:
            reasoning_agent(state)
            mock_client = mock_factory.return_value
            call_args = mock_client.generate.call_args
            prompt_arg = call_args.args[0] if call_args.args else call_args.kwargs.get("prompt")
            assert prompt_arg is not None
            assert len(prompt_arg) > 100  # Non-trivial prompt


# ── TEST 5: Mocked response becomes valid Hypothesis ─────────────────


class TestHypothesisValidation:
    """The mocked Gemini response is correctly wrapped."""

    def test_exactly_one_hypothesis(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        hypotheses = result["investigation_reasoning"].hypotheses
        assert len(hypotheses) == 1

    def test_hypothesis_is_hypothesis_instance(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        hypothesis = result["investigation_reasoning"].hypotheses[0]
        assert isinstance(hypothesis, Hypothesis)

    def test_hypothesis_id_populated(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        hypothesis = result["investigation_reasoning"].hypotheses[0]
        assert hypothesis.hypothesis_id
        assert len(hypothesis.hypothesis_id) > 0

    def test_title_populated(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        hypothesis = result["investigation_reasoning"].hypotheses[0]
        assert hypothesis.title
        assert len(hypothesis.title) > 0

    def test_description_populated(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        hypothesis = result["investigation_reasoning"].hypotheses[0]
        assert hypothesis.description
        assert len(hypothesis.description) > 0

    def test_confidence_valid(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        hypothesis = result["investigation_reasoning"].hypotheses[0]
        assert 0.0 <= hypothesis.confidence <= 1.0

    def test_supporting_evidence_present(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        hypothesis = result["investigation_reasoning"].hypotheses[0]
        assert len(hypothesis.supporting_evidence) > 0

    def test_contradicting_evidence_present(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        hypothesis = result["investigation_reasoning"].hypotheses[0]
        assert len(hypothesis.contradicting_evidence) > 0


# ── TEST 6: InvestigationReasoning structure ─────────────────────────


class TestReasoningStructure:
    """reasoning_agent() returns a proper InvestigationReasoning."""

    def test_reasoning_summary_populated(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        reasoning = result["investigation_reasoning"]
        assert reasoning.reasoning_summary is not None
        assert len(reasoning.reasoning_summary) > 0

    def test_recommended_actions_populated(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        reasoning = result["investigation_reasoning"]
        assert len(reasoning.recommended_actions) > 0

    def test_reasoning_summary_mentions_hypothesis(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        reasoning = result["investigation_reasoning"]
        # Summary should reference the hypothesis title
        assert MOCK_HYPOTHESIS.title in reasoning.reasoning_summary


# ── TEST 7: Reasoning node delegates to agent ────────────────────────


class TestReasoningNodeDelegation:
    """reasoning_node() correctly delegates to reasoning_agent()."""

    def test_node_calls_reasoning_agent(self) -> None:
        state = _make_test_state()
        state_dict = state.model_dump(mode="json")
        with _patch_gemini():
            result = reasoning_node(state_dict)
        assert "investigation_reasoning" in result

    def test_node_sets_reasoning_stage(self) -> None:
        state = _make_test_state()
        state_dict = state.model_dump(mode="json")
        with _patch_gemini():
            result = reasoning_node(state_dict)
        assert result["current_stage"] == CurrentStage.REASONING

    def test_node_returns_dict(self) -> None:
        state = _make_test_state()
        state_dict = state.model_dump(mode="json")
        with _patch_gemini():
            result = reasoning_node(state_dict)
        assert isinstance(result, dict)

    def test_node_hypothesis_matches_agent(self) -> None:
        """Node returns the same hypothesis the agent produces."""
        state = _make_test_state()
        state_dict = state.model_dump(mode="json")
        with _patch_gemini():
            result = reasoning_node(state_dict)
        hypothesis = result["investigation_reasoning"].hypotheses[0]
        assert hypothesis.hypothesis_id == MOCK_HYPOTHESIS.hypothesis_id


# ── TEST 8: Existing state fields not destroyed ──────────────────────


class TestStatePreservation:
    """reasoning_agent() does not destroy unrelated state fields."""

    def test_agent_does_not_return_case_id(self) -> None:
        """Agent should not overwrite case_id."""
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        assert "case_id" not in result

    def test_agent_does_not_return_case_input(self) -> None:
        """Agent should not overwrite case_input."""
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        assert "case_input" not in result

    def test_agent_does_not_return_context_intelligence(self) -> None:
        """Agent should not overwrite context_intelligence."""
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        assert "context_intelligence" not in result

    def test_agent_only_returns_investigation_reasoning(self) -> None:
        """Agent returns exactly one key."""
        state = _make_test_state()
        with _patch_gemini():
            result = reasoning_agent(state)
        assert set(result.keys()) == {"investigation_reasoning"}
