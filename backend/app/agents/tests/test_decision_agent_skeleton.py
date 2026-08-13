"""Tests for the Decision Agent skeleton (Parth — Round 2).

Covers:
- Agent execution without errors
- At least 2 decision options generated
- Schema validity of every generated option
- All required fields populated
- Distinct options
- Deterministic output
- Graph integration
"""

from datetime import datetime

from app.agents.decision_agent import decision_agent
from app.graph.workflow import run_investigation
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    CurrentStage,
    CustomerProfile,
    DecisionAction,
    DecisionOptimization,
    DecisionOption,
    InvestigationState,
    Transaction,
    create_initial_state,
)


# ── Helper: build a minimal valid InvestigationState ─────────────────


def _make_test_state() -> InvestigationState:
    """Create a minimal InvestigationState for testing."""
    transaction = Transaction(
        transaction_id="TXN-TEST-001",
        amount=5000.00,
        currency="USD",
        timestamp=datetime(2025, 8, 1, 10, 0, 0),
        sender_account="ACC-SRC-001",
        receiver_account="ACC-DST-001",
        transaction_type="WIRE",
        channel="ONLINE",
    )
    case_input = CaseInput(
        transactions=[transaction],
        customer_profile=CustomerProfile(
            customer_id="CUST-TEST-001",
            name="Decision Agent Test Customer",
        ),
        alert_reason="Automated test — Decision Agent skeleton.",
    )
    return create_initial_state(
        case_id="CASE-TEST-DECISION-001",
        case_input=case_input,
    )


# ── VALID DecisionAction values ──────────────────────────────────────

_VALID_ACTIONS = {action.value for action in DecisionAction}


# ── TEST 1: Agent execution ──────────────────────────────────────────


class TestAgentExecution:
    """Decision Agent can be called without errors."""

    def test_agent_returns_dict(self) -> None:
        """decision_agent() returns a dict."""
        state = _make_test_state()
        result = decision_agent(state)
        assert isinstance(result, dict)

    def test_result_contains_decision_optimization(self) -> None:
        """Result dict contains a 'decision_optimization' key."""
        state = _make_test_state()
        result = decision_agent(state)
        assert "decision_optimization" in result

    def test_decision_optimization_is_valid_model(self) -> None:
        """The decision_optimization value is a valid DecisionOptimization."""
        state = _make_test_state()
        result = decision_agent(state)
        decision = result["decision_optimization"]
        assert isinstance(decision, DecisionOptimization)

    def test_agent_status_is_completed(self) -> None:
        """Decision optimization status is COMPLETED."""
        state = _make_test_state()
        result = decision_agent(state)
        decision = result["decision_optimization"]
        assert decision.status == AgentStatus.COMPLETED


# ── TEST 2: At least two options ─────────────────────────────────────


class TestMinimumOptions:
    """Decision Agent generates at least 2 options."""

    def test_at_least_two_options(self) -> None:
        """At least 2 DecisionOption objects are returned."""
        state = _make_test_state()
        result = decision_agent(state)
        options = result["decision_optimization"].decision_options
        assert len(options) >= 2


# ── TEST 3: Schema validity ─────────────────────────────────────────


class TestSchemaValidity:
    """Every generated option is a valid DecisionOption."""

    def test_every_option_is_decision_option(self) -> None:
        """All items in decision_options are DecisionOption instances."""
        state = _make_test_state()
        result = decision_agent(state)
        options = result["decision_optimization"].decision_options
        for opt in options:
            assert isinstance(opt, DecisionOption)

    def test_every_action_is_valid_enum(self) -> None:
        """All actions use valid DecisionAction enum values."""
        state = _make_test_state()
        result = decision_agent(state)
        options = result["decision_optimization"].decision_options
        for opt in options:
            assert opt.action.value in _VALID_ACTIONS

    def test_confidence_in_range(self) -> None:
        """All confidence scores are between 0.0 and 1.0."""
        state = _make_test_state()
        result = decision_agent(state)
        options = result["decision_optimization"].decision_options
        for opt in options:
            assert 0.0 <= opt.confidence <= 1.0

    def test_risk_score_in_range(self) -> None:
        """All risk scores are between 0.0 and 1.0."""
        state = _make_test_state()
        result = decision_agent(state)
        options = result["decision_optimization"].decision_options
        for opt in options:
            assert opt.risk_score is not None
            assert 0.0 <= opt.risk_score <= 1.0


# ── TEST 4: Required fields populated ────────────────────────────────


class TestRequiredFields:
    """Every generated option has all required fields populated."""

    def test_option_id_populated(self) -> None:
        state = _make_test_state()
        result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert opt.option_id is not None
            assert len(opt.option_id) > 0

    def test_action_populated(self) -> None:
        state = _make_test_state()
        result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert opt.action is not None

    def test_rationale_populated(self) -> None:
        state = _make_test_state()
        result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert opt.rationale is not None
            assert len(opt.rationale) > 0

    def test_confidence_populated(self) -> None:
        state = _make_test_state()
        result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert opt.confidence is not None

    def test_risk_score_populated(self) -> None:
        state = _make_test_state()
        result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert opt.risk_score is not None

    def test_pros_populated(self) -> None:
        state = _make_test_state()
        result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert len(opt.pros) > 0

    def test_cons_populated(self) -> None:
        state = _make_test_state()
        result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert len(opt.cons) > 0

    def test_risks_populated(self) -> None:
        state = _make_test_state()
        result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert len(opt.risks) > 0

    def test_mitigation_populated(self) -> None:
        state = _make_test_state()
        result = decision_agent(state)
        for opt in result["decision_optimization"].decision_options:
            assert len(opt.mitigation) > 0


# ── TEST 5: Distinct options ─────────────────────────────────────────


class TestDistinctOptions:
    """Generated options are actually distinct."""

    def test_unique_option_ids(self) -> None:
        """All option_id values are unique."""
        state = _make_test_state()
        result = decision_agent(state)
        options = result["decision_optimization"].decision_options
        ids = [opt.option_id for opt in options]
        assert len(ids) == len(set(ids))

    def test_distinct_actions(self) -> None:
        """Options have different actions."""
        state = _make_test_state()
        result = decision_agent(state)
        options = result["decision_optimization"].decision_options
        actions = [opt.action for opt in options]
        assert len(actions) == len(set(actions))

    def test_distinct_confidence_values(self) -> None:
        """Options have different confidence values."""
        state = _make_test_state()
        result = decision_agent(state)
        options = result["decision_optimization"].decision_options
        confidences = [opt.confidence for opt in options]
        assert len(confidences) == len(set(confidences))


# ── TEST 6: Deterministic output ─────────────────────────────────────


class TestDeterministicOutput:
    """Calling the agent repeatedly produces identical output."""

    def test_deterministic_across_calls(self) -> None:
        """Two calls with the same input produce identical decision options."""
        state = _make_test_state()
        result1 = decision_agent(state)
        result2 = decision_agent(state)

        opts1 = result1["decision_optimization"].decision_options
        opts2 = result2["decision_optimization"].decision_options

        assert len(opts1) == len(opts2)
        for o1, o2 in zip(opts1, opts2):
            assert o1.option_id == o2.option_id
            assert o1.action == o2.action
            assert o1.rationale == o2.rationale
            assert o1.confidence == o2.confidence
            assert o1.risk_score == o2.risk_score
            assert o1.pros == o2.pros
            assert o1.cons == o2.cons
            assert o1.risks == o2.risks
            assert o1.mitigation == o2.mitigation

    def test_recommended_decision_deterministic(self) -> None:
        """Recommended decision is the same across calls."""
        state = _make_test_state()
        r1 = decision_agent(state)["decision_optimization"]
        r2 = decision_agent(state)["decision_optimization"]
        assert r1.recommended_decision == r2.recommended_decision
        assert r1.decision_rationale == r2.decision_rationale


# ── TEST 7: Graph integration ────────────────────────────────────────


class TestGraphIntegration:
    """Decision Agent integrates correctly with the LangGraph pipeline."""

    def test_graph_produces_decision_options(self) -> None:
        """Running the full graph populates decision_options with >= 2 options."""
        state = _make_test_state()
        result = run_investigation(state)

        assert isinstance(result, InvestigationState)
        assert result.decision_optimization is not None
        assert result.decision_optimization.status == AgentStatus.COMPLETED
        assert len(result.decision_optimization.decision_options) >= 2

    def test_graph_reaches_done_stage(self) -> None:
        """Graph still completes through to DONE."""
        state = _make_test_state()
        result = run_investigation(state)
        assert result.current_stage == CurrentStage.DONE

    def test_graph_does_not_break_other_stages(self) -> None:
        """Other agent outputs remain populated after the decision node."""
        state = _make_test_state()
        result = run_investigation(state)

        assert result.context_intelligence is not None
        assert result.investigation_reasoning is not None
        assert result.evidence_compliance_validation is not None
        assert result.investigation_report is not None
