"""Tests for the Decision Agent — Round 3 Gemini-powered options.

All tests mock ``GeminiClient.generate()`` — no real Gemini API key
is required.

Covers:
- Agent execution
- Exactly 4 options returned
- All 4 DecisionAction values present (ALLOW, HOLD, BLOCK, ESCALATE)
- No duplicate actions
- Schema validity of every option
- Non-empty rationale
- Valid risk_score and confidence
- pros / cons / risks / mitigation populated
- GeminiClient is called
- Prompt contains case data, context intelligence, investigation reasoning
- No hardcoded placeholder text remains
- recommended_decision is not set (Round 4 boundary)
- Decision node integration
- State preservation
- Validation rejects malformed Gemini output
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.agents.decision_agent import (
    _DecisionOptionsResponse,
    _build_prompt,
    _validate_options,
    decision_agent,
)
from app.graph.nodes.decision_node import decision_node
from app.schemas.investigation_state import (
    AgentStatus,
    AnomalyType,
    CaseInput,
    ContextIntelligence,
    CurrentStage,
    CustomerProfile,
    DecisionAction,
    DecisionOptimization,
    DecisionOption,
    DetectedAnomaly,
    Hypothesis,
    InvestigationReasoning,
    InvestigationState,
    SeverityLevel,
    Transaction,
    create_initial_state,
)
from app.services.gemini_client import GeminiClientError


# ── Fixtures ─────────────────────────────────────────────────────────


MOCK_OPTIONS = [
    DecisionOption(
        option_id="OPT-ALLOW",
        action=DecisionAction.ALLOW,
        rationale=(
            "Allowing the transaction preserves the relationship with "
            "customer CUST-TEST-001 whose $15,000 WIRE transfer may be "
            "legitimate given their Portfolio Manager occupation."
        ),
        confidence=0.20,
        risk_score=0.78,
        pros=["Preserves customer relationship"],
        cons=["Regulatory exposure if transaction is illicit"],
        risks=["Potential AML violation"],
        mitigation=["Post-transaction monitoring for 30 days"],
    ),
    DecisionOption(
        option_id="OPT-HOLD",
        action=DecisionAction.HOLD,
        rationale=(
            "Holding the $15,000 WIRE transfer allows time to verify "
            "the alert triggered by suspicious wire transfer pattern "
            "while the contextual risk score of 0.45 is investigated."
        ),
        confidence=0.65,
        risk_score=0.40,
        pros=["Prevents fund movement during investigation"],
        cons=["Customer inconvenience during hold period"],
        risks=["Customer complaint if transaction is legitimate"],
        mitigation=["Proactive customer outreach to expedite verification"],
    ),
    DecisionOption(
        option_id="OPT-BLOCK",
        action=DecisionAction.BLOCK,
        rationale=(
            "Blocking the transaction eliminates risk of fund loss "
            "given the POINT anomaly detected on TXN-TEST-001 and the "
            "HIGH risk rating of customer CUST-TEST-001."
        ),
        confidence=0.35,
        risk_score=0.15,
        pros=["Eliminates risk of fund loss"],
        cons=["High customer friction"],
        risks=["Customer attrition"],
        mitigation=["Offer alternative transfer channel after KYC clearance"],
    ),
    DecisionOption(
        option_id="OPT-ESCALATE",
        action=DecisionAction.ESCALATE,
        rationale=(
            "Escalation to senior analysts is warranted given the "
            "hypothesis of Suspected Structuring Activity with 82% "
            "confidence and the converging risk signals from context "
            "intelligence."
        ),
        confidence=0.50,
        risk_score=0.45,
        pros=["Multi-disciplinary review for complex case"],
        cons=["Longer resolution time"],
        risks=["Delayed resolution may frustrate customer"],
        mitigation=["Assign to high-priority queue for same-day review"],
    ),
]

MOCK_RESPONSE = _DecisionOptionsResponse(
    options=MOCK_OPTIONS,
    recommended_decision=DecisionAction.BLOCK,
    decision_rationale="Blocking is the safest approach given the detected anomalies and high contextual risk score."
)


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


def _make_investigation_reasoning() -> InvestigationReasoning:
    """Build a realistic InvestigationReasoning for testing."""
    return InvestigationReasoning(
        status=AgentStatus.COMPLETED,
        hypotheses=[
            Hypothesis(
                hypothesis_id="HYP-001",
                title="Suspected Structuring Activity",
                description=(
                    "The customer appears to be structuring transactions "
                    "to avoid reporting thresholds."
                ),
                confidence=0.82,
                supporting_evidence=[
                    "TXN-TEST-001: $15,000 wire transfer",
                    "Customer risk rating: HIGH",
                ],
                contradicting_evidence=[
                    "Customer is a Portfolio Manager with legitimate activity",
                ],
            ),
        ],
        reasoning_summary=(
            "Generated hypothesis 'Suspected Structuring Activity' with "
            "82% confidence based on case data and context intelligence."
        ),
        recommended_actions=[
            "Review the hypothesis against available evidence",
            "Verify flagged transactions and entities",
        ],
    )


def _make_test_state() -> InvestigationState:
    """Create a realistic InvestigationState with context + reasoning."""
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
        case_id="CASE-TEST-DECISION-R3-001",
        case_input=case_input,
    )
    state = state.model_copy(
        update={
            "context_intelligence": _make_context_intelligence(),
            "investigation_reasoning": _make_investigation_reasoning(),
        },
    )
    return state


# ── Helper: patch GeminiClient ───────────────────────────────────────


def _patch_gemini(return_value=None):
    """Return a context-manager that patches get_gemini_client."""
    mock_client = MagicMock()
    mock_client.generate.return_value = return_value or MOCK_RESPONSE
    return patch(
        "app.agents.decision_agent.get_gemini_client",
        return_value=mock_client,
    )


# ── TEST 1: Agent execution ─────────────────────────────────────────


class TestAgentExecution:
    """decision_agent() executes successfully with mocked Gemini."""

    def test_agent_returns_dict(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        assert isinstance(result, dict)

    def test_result_contains_decision_optimization(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        assert "decision_optimization" in result

    def test_decision_optimization_is_valid_model(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        assert isinstance(
            result["decision_optimization"], DecisionOptimization,
        )

    def test_agent_status_is_completed(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        assert result["decision_optimization"].status == AgentStatus.COMPLETED


# ── TEST 2: Exactly 4 options ────────────────────────────────────────


class TestOptionCount:
    """Decision Agent returns exactly 4 options."""

    def test_exactly_four_options(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        options = result["decision_optimization"].decision_options
        assert len(options) == 4


# ── TEST 3: All 4 actions present ────────────────────────────────────


class TestAllActionsPresent:
    """All four DecisionAction values are present."""

    def test_allow_present(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        actions = {o.action for o in result["decision_optimization"].decision_options}
        assert DecisionAction.ALLOW in actions

    def test_hold_present(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        actions = {o.action for o in result["decision_optimization"].decision_options}
        assert DecisionAction.HOLD in actions

    def test_block_present(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        actions = {o.action for o in result["decision_optimization"].decision_options}
        assert DecisionAction.BLOCK in actions

    def test_escalate_present(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        actions = {o.action for o in result["decision_optimization"].decision_options}
        assert DecisionAction.ESCALATE in actions

    def test_no_duplicate_actions(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        options = result["decision_optimization"].decision_options
        actions = [o.action for o in options]
        assert len(actions) == len(set(actions))


# ── TEST 4: Schema validity ─────────────────────────────────────────


class TestSchemaValidity:
    """Every option passes schema validation."""

    def test_every_option_is_decision_option(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert isinstance(opt, DecisionOption)

    def test_every_confidence_in_range(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert 0.0 <= opt.confidence <= 1.0

    def test_every_risk_score_valid(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert opt.risk_score is not None
            assert 0.0 <= opt.risk_score <= 1.0


# ── TEST 5: Required fields populated ────────────────────────────────


class TestRequiredFields:
    """Every option has all required fields populated."""

    def test_option_id_populated(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert opt.option_id and len(opt.option_id) > 0

    def test_rationale_populated(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert opt.rationale and len(opt.rationale) > 0

    def test_pros_populated(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert len(opt.pros) >= 1

    def test_cons_populated(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert len(opt.cons) >= 1

    def test_risks_populated(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert len(opt.risks) >= 1

    def test_mitigation_populated(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert len(opt.mitigation) >= 1


# ── TEST 6: GeminiClient integration ────────────────────────────────


class TestGeminiIntegration:
    """GeminiClient is called correctly."""

    def test_generate_called_once(self) -> None:
        state = _make_test_state()
        with _patch_gemini() as mock_factory:
            decision_agent(state)
            mock_client = mock_factory.return_value
            mock_client.generate.assert_called_once()

    def test_generate_receives_non_empty_prompt(self) -> None:
        state = _make_test_state()
        with _patch_gemini() as mock_factory:
            decision_agent(state)
            mock_client = mock_factory.return_value
            call_args = mock_client.generate.call_args
            prompt_arg = call_args.args[0] if call_args.args else call_args.kwargs.get("prompt")
            assert prompt_arg is not None
            assert len(prompt_arg) > 100

    def test_generate_uses_response_schema(self) -> None:
        state = _make_test_state()
        with _patch_gemini() as mock_factory:
            decision_agent(state)
            mock_client = mock_factory.return_value
            call_kwargs = mock_client.generate.call_args
            schema = call_kwargs.kwargs.get("response_schema") or (
                call_kwargs.args[1] if len(call_kwargs.args) >= 2 else None
            )
            assert schema is _DecisionOptionsResponse


# ── TEST 7: Prompt contains investigation data ──────────────────────


class TestPromptContent:
    """The prompt includes case, context, and reasoning data."""

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

    def test_prompt_contains_context_summary(self) -> None:
        state = _make_test_state()
        prompt = _build_prompt(state)
        assert "under investigation" in prompt

    def test_prompt_contains_risk_score(self) -> None:
        state = _make_test_state()
        prompt = _build_prompt(state)
        assert "0.45" in prompt

    def test_prompt_contains_hypothesis(self) -> None:
        state = _make_test_state()
        prompt = _build_prompt(state)
        assert "Suspected Structuring Activity" in prompt

    def test_prompt_contains_reasoning_summary(self) -> None:
        state = _make_test_state()
        prompt = _build_prompt(state)
        assert "82%" in prompt or "0.82" in prompt

    def test_prompt_handles_missing_context(self) -> None:
        """Prompt builds without error when context_intelligence is None."""
        state = _make_test_state()
        state = state.model_copy(update={"context_intelligence": None})
        prompt = _build_prompt(state)
        assert "CONTEXT INTELLIGENCE" in prompt

    def test_prompt_handles_missing_reasoning(self) -> None:
        """Prompt builds without error when investigation_reasoning is None."""
        state = _make_test_state()
        state = state.model_copy(update={"investigation_reasoning": None})
        prompt = _build_prompt(state)
        assert "INVESTIGATION REASONING" in prompt


# ── TEST 8: No hardcoded placeholder text ────────────────────────────


class TestNoPlaceholders:
    """Old Round 2 hardcoded text is not present in the new output."""

    def test_no_old_allow_rationale(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert "AML EDD has not been completed" not in opt.rationale

    def test_no_old_hold_rationale(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert "48-hour regulatory hold window" not in opt.rationale


# ── TEST 9: Round 4 boundary ────────────────────────────────────────


class TestRound4Boundary:
    """Round 4 selects and records a recommended decision."""

    def test_recommended_decision_is_populated(self) -> None:
        """recommended_decision and decision_rationale are set."""
        state = _make_test_state()
        with patch("app.agents.decision_agent.get_gemini_client") as mock:
            mock.return_value.generate.return_value = MOCK_RESPONSE
            result = decision_agent(state)

        assert result["decision_optimization"].recommended_decision == DecisionAction.BLOCK
        assert result["decision_optimization"].decision_rationale is not None

    def test_decision_rationale_is_populated(self) -> None:
        state = _make_test_state()
        with patch("app.agents.decision_agent.get_gemini_client") as mock:
            mock.return_value.generate.return_value = MOCK_RESPONSE
            result = decision_agent(state)
        assert result["decision_optimization"].decision_rationale is not None


# ── TEST 10: Decision node delegation ────────────────────────────────


class TestDecisionNodeDelegation:
    """decision_node() correctly delegates to decision_agent()."""

    def test_node_calls_decision_agent(self) -> None:
        state = _make_test_state()
        state_dict = state.model_dump(mode="json")
        with _patch_gemini():
            result = decision_node(state_dict)
        assert "decision_optimization" in result

    def test_node_sets_decision_stage(self) -> None:
        state = _make_test_state()
        state_dict = state.model_dump(mode="json")
        with _patch_gemini():
            result = decision_node(state_dict)
        assert result["current_stage"] == CurrentStage.DECISION

    def test_node_returns_dict(self) -> None:
        state = _make_test_state()
        state_dict = state.model_dump(mode="json")
        with _patch_gemini():
            result = decision_node(state_dict)
        assert isinstance(result, dict)


# ── TEST 11: State preservation ──────────────────────────────────────


class TestStatePreservation:
    """decision_agent() does not overwrite unrelated state fields."""

    def test_only_returns_decision_optimization(self) -> None:
        state = _make_test_state()
        with _patch_gemini():
            result = decision_agent(state)
        assert set(result.keys()) == {"decision_optimization"}


# ── TEST 12: Validation rejects malformed output ─────────────────────


class TestValidationRejectsMalformed:
    """_validate_options raises on malformed Gemini output."""

    def test_rejects_wrong_count(self) -> None:
        """Only 3 options -> GeminiClientError."""
        with pytest.raises(GeminiClientError, match="Expected exactly 4"):
            _validate_options(MOCK_OPTIONS[:3])

    def test_rejects_duplicate_actions(self) -> None:
        """Two ALLOW options -> GeminiClientError."""
        duplicate = list(MOCK_OPTIONS)
        duplicate[1] = duplicate[0].model_copy(
            update={"option_id": "OPT-DUP", "action": DecisionAction.ALLOW}
        )
        with pytest.raises(GeminiClientError, match="wrong actions"):
            _validate_options(duplicate)

    def test_rejects_empty_list(self) -> None:
        """Empty list -> GeminiClientError."""
        with pytest.raises(GeminiClientError, match="Expected exactly 4"):
            _validate_options([])

    def test_agent_raises_on_bad_gemini_output(self) -> None:
        """Agent propagates GeminiClientError from validation."""
        bad_response = _DecisionOptionsResponse(
            options=MOCK_OPTIONS[:2],
            recommended_decision=DecisionAction.BLOCK,
            decision_rationale="Test"
        )
        state = _make_test_state()
        with _patch_gemini(return_value=bad_response):
            with pytest.raises(GeminiClientError):
                decision_agent(state)
