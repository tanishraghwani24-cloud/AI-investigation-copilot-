"""Tests for the Context & Evidence Intelligence Agent.

Covers:
- Context intelligence is created with COMPLETED status
- Summary is populated
- Key indicators are populated
- Anomalies are generated for suspicious transactions
- Risk score is between 0.0 and 1.0
- Deterministic behaviour
- Graph integration (pipeline still reaches DONE)
"""

from datetime import datetime

from app.agents.context_agent import context_agent
from app.graph.workflow import run_investigation
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    ContextIntelligence,
    CurrentStage,
    CustomerProfile,
    InvestigationState,
    Transaction,
    create_initial_state,
)


# ── Helper ───────────────────────────────────────────────────────────


def _make_test_state() -> InvestigationState:
    """Create a test InvestigationState with realistic transaction data."""
    transactions = [
        Transaction(
            transaction_id="TXN-CTX-001",
            amount=15_000.00,
            currency="USD",
            timestamp=datetime(2025, 7, 15, 9, 30, 0),
            sender_account="ACC-SRC-001",
            receiver_account="ACC-DST-001",
            transaction_type="WIRE",
            channel="ONLINE",
            description="Large wire transfer",
            location="New York, US",
        ),
        Transaction(
            transaction_id="TXN-CTX-002",
            amount=3_500.00,
            currency="USD",
            timestamp=datetime(2025, 7, 15, 9, 45, 0),
            sender_account="ACC-SRC-001",
            receiver_account="ACC-DST-002",
            transaction_type="ACH",
            channel="ONLINE",
            description="Supplier payment",
            location="New York, US",
        ),
        Transaction(
            transaction_id="TXN-CTX-003",
            amount=800.00,
            currency="USD",
            timestamp=datetime(2025, 7, 15, 14, 0, 0),
            sender_account="ACC-SRC-001",
            receiver_account="ACC-DST-003",
            transaction_type="CARD",
            channel="MOBILE",
            description="Equipment purchase",
            location="Chicago, US",
        ),
    ]
    case_input = CaseInput(
        transactions=transactions,
        customer_profile=CustomerProfile(
            customer_id="CUST-CTX-001",
            name="Context Agent Test Customer",
            risk_rating="MEDIUM",
        ),
        alert_reason="Large wire transfer flagged by rule engine.",
    )
    return create_initial_state(
        case_id="CASE-CTX-001",
        case_input=case_input,
    )


def _make_empty_state() -> InvestigationState:
    """Create a test state with no transactions."""
    case_input = CaseInput(
        transactions=[],
        customer_profile=CustomerProfile(
            customer_id="CUST-CTX-EMPTY",
            name="Empty Transaction Customer",
        ),
        alert_reason="Test alert — no transactions.",
    )
    return create_initial_state(
        case_id="CASE-CTX-EMPTY",
        case_input=case_input,
    )


# ── TEST 1: Context intelligence creation ────────────────────────────


class TestContextIntelligenceCreation:
    """Context Agent produces a valid ContextIntelligence."""

    def test_returns_dict(self) -> None:
        """context_agent() returns a dict."""
        state = _make_test_state()
        result = context_agent(state)
        assert isinstance(result, dict)

    def test_contains_context_intelligence(self) -> None:
        """Result dict contains 'context_intelligence'."""
        state = _make_test_state()
        result = context_agent(state)
        assert "context_intelligence" in result

    def test_is_valid_model(self) -> None:
        """context_intelligence is a valid ContextIntelligence."""
        state = _make_test_state()
        result = context_agent(state)
        ci = result["context_intelligence"]
        assert isinstance(ci, ContextIntelligence)


# ── TEST 2: Status is COMPLETED ──────────────────────────────────────


class TestCompletedStatus:
    """Context Agent sets status to COMPLETED."""

    def test_status_completed(self) -> None:
        """Status is COMPLETED."""
        state = _make_test_state()
        result = context_agent(state)
        assert result["context_intelligence"].status == AgentStatus.COMPLETED

    def test_status_completed_empty(self) -> None:
        """Status is COMPLETED even with no transactions."""
        state = _make_empty_state()
        result = context_agent(state)
        assert result["context_intelligence"].status == AgentStatus.COMPLETED


# ── TEST 3: Summary is populated ─────────────────────────────────────


class TestSummaryPopulated:
    """Context Agent produces a non-empty summary."""

    def test_summary_is_string(self) -> None:
        """context_summary is a string."""
        state = _make_test_state()
        ci = context_agent(state)["context_intelligence"]
        assert isinstance(ci.context_summary, str)

    def test_summary_is_non_empty(self) -> None:
        """context_summary is non-empty."""
        state = _make_test_state()
        ci = context_agent(state)["context_intelligence"]
        assert len(ci.context_summary) > 0

    def test_summary_mentions_customer(self) -> None:
        """Summary references the customer name."""
        state = _make_test_state()
        ci = context_agent(state)["context_intelligence"]
        assert "Context Agent Test Customer" in ci.context_summary


# ── TEST 4: Key indicators populated ─────────────────────────────────


class TestKeyIndicators:
    """Context Agent produces key indicators."""

    def test_indicators_non_empty(self) -> None:
        """key_indicators list is non-empty."""
        state = _make_test_state()
        ci = context_agent(state)["context_intelligence"]
        assert len(ci.key_indicators) > 0

    def test_indicators_are_strings(self) -> None:
        """All key indicators are strings."""
        state = _make_test_state()
        ci = context_agent(state)["context_intelligence"]
        for indicator in ci.key_indicators:
            assert isinstance(indicator, str)
            assert len(indicator) > 0


# ── TEST 5: Anomalies generated ──────────────────────────────────────


class TestAnomalies:
    """Context Agent detects anomalies in transaction data."""

    def test_anomalies_for_large_transactions(self) -> None:
        """Large transactions generate anomalies."""
        state = _make_test_state()
        ci = context_agent(state)["context_intelligence"]
        # Test state has a $15,000 transaction → should produce anomaly
        assert len(ci.anomalies) >= 1

    def test_anomaly_fields_populated(self) -> None:
        """Each anomaly has all required fields populated."""
        state = _make_test_state()
        ci = context_agent(state)["context_intelligence"]
        for anomaly in ci.anomalies:
            assert len(anomaly.anomaly_id) > 0
            assert anomaly.anomaly_type is not None
            assert anomaly.severity is not None
            assert len(anomaly.description) > 0
            assert len(anomaly.related_transactions) > 0

    def test_no_anomalies_for_small_transactions(self) -> None:
        """No POINT anomalies when all transactions are small."""
        transactions = [
            Transaction(
                transaction_id="TXN-SMALL-001",
                amount=500.00,
                currency="USD",
                timestamp=datetime(2025, 7, 15, 9, 0, 0),
                sender_account="ACC-SRC",
                receiver_account="ACC-DST",
                transaction_type="CARD",
                channel="ONLINE",
            ),
        ]
        case_input = CaseInput(
            transactions=transactions,
            customer_profile=CustomerProfile(
                customer_id="CUST-SMALL",
                name="Small Transaction Customer",
            ),
        )
        state = create_initial_state("CASE-SMALL", case_input)
        ci = context_agent(state)["context_intelligence"]
        # Only small transactions → no POINT anomalies
        point_anomalies = [
            a for a in ci.anomalies if a.anomaly_type.value == "POINT"
        ]
        assert len(point_anomalies) == 0


# ── TEST 6: Risk score range ────────────────────────────────────────


class TestRiskScore:
    """Risk score is within valid bounds."""

    def test_risk_score_in_range(self) -> None:
        """Risk score is between 0.0 and 1.0."""
        state = _make_test_state()
        ci = context_agent(state)["context_intelligence"]
        assert ci.risk_score is not None
        assert 0.0 <= ci.risk_score <= 1.0

    def test_risk_score_in_range_empty(self) -> None:
        """Risk score is valid even with empty transactions."""
        state = _make_empty_state()
        ci = context_agent(state)["context_intelligence"]
        assert ci.risk_score is not None
        assert 0.0 <= ci.risk_score <= 1.0


# ── TEST 7: Deterministic behaviour ─────────────────────────────────


class TestDeterministicBehaviour:
    """Same input → same output."""

    def test_identical_results(self) -> None:
        """Two calls with the same state produce identical results."""
        state = _make_test_state()
        r1 = context_agent(state)
        r2 = context_agent(state)

        ci1 = r1["context_intelligence"]
        ci2 = r2["context_intelligence"]

        assert ci1.context_summary == ci2.context_summary
        assert ci1.key_indicators == ci2.key_indicators
        assert ci1.risk_score == ci2.risk_score
        assert len(ci1.anomalies) == len(ci2.anomalies)
        for a1, a2 in zip(ci1.anomalies, ci2.anomalies):
            assert a1.anomaly_id == a2.anomaly_id
            assert a1.description == a2.description


# ── TEST 8: Graph integration ────────────────────────────────────────


class TestGraphIntegration:
    """Context Agent integrates correctly with the LangGraph pipeline."""

    def test_graph_populates_context_intelligence(self) -> None:
        """Running the full graph populates context_intelligence."""
        state = _make_test_state()
        result = run_investigation(state)

        assert isinstance(result, InvestigationState)
        assert result.context_intelligence is not None
        assert result.context_intelligence.status == AgentStatus.COMPLETED
        assert len(result.context_intelligence.context_summary) > 0

    def test_graph_reaches_done_stage(self) -> None:
        """Graph still completes through to DONE."""
        state = _make_test_state()
        result = run_investigation(state)
        assert result.current_stage == CurrentStage.DONE

    def test_graph_does_not_break_other_stages(self) -> None:
        """Other agent outputs remain populated after the context node."""
        state = _make_test_state()
        result = run_investigation(state)

        assert result.investigation_reasoning is not None
        assert result.evidence_compliance_validation is not None
        assert result.decision_optimization is not None
        assert result.investigation_report is not None
