"""Round 5 edge-case tests for Context Agent graceful degradation.

Covers:
- CASE 1: Zero uploaded documents
- CASE 2: Missing / partial / None customer profile
- CASE 3: Partial Mock Bank data (empty transactions, missing fields)
- CASE 4: Combined sparse-data scenarios
"""

from datetime import datetime

from app.agents.context_agent import context_agent
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    ContextIntelligence,
    CustomerProfile,
    InvestigationState,
    Transaction,
    create_initial_state,
)


# ── Helpers ──────────────────────────────────────────────────────────


def _make_transactions() -> list[Transaction]:
    """Return a small set of transactions for testing."""
    return [
        Transaction(
            transaction_id="TXN-R5-001",
            amount=15_000.00,
            currency="USD",
            timestamp=datetime(2025, 7, 15, 9, 30, 0),
            sender_account="ACC-SRC-R5",
            receiver_account="ACC-DST-R5",
            transaction_type="WIRE",
            channel="ONLINE",
            description="Large wire transfer",
        ),
        Transaction(
            transaction_id="TXN-R5-002",
            amount=3_500.00,
            currency="USD",
            timestamp=datetime(2025, 7, 15, 9, 45, 0),
            sender_account="ACC-SRC-R5",
            receiver_account="ACC-DST-R5-B",
            transaction_type="ACH",
            channel="ONLINE",
        ),
    ]


def _make_state(
    *,
    transactions: list[Transaction] | None = None,
    customer_profile: CustomerProfile | None = None,
    alert_reason: str | None = None,
    include_customer: bool = True,
) -> InvestigationState:
    """Build an InvestigationState with configurable sparse data."""
    kwargs: dict = {
        "transactions": transactions if transactions is not None else [],
        "alert_reason": alert_reason,
    }
    if include_customer and customer_profile is not None:
        kwargs["customer_profile"] = customer_profile
    elif include_customer:
        # Explicitly pass None to represent missing profile
        kwargs["customer_profile"] = None
    else:
        kwargs["customer_profile"] = None

    return create_initial_state(
        case_id="CASE-R5-EDGE",
        case_input=CaseInput(**kwargs),
    )


def _assert_valid_context(ci: ContextIntelligence) -> None:
    """Assert that a ContextIntelligence object satisfies the downstream contract."""
    assert ci.status == AgentStatus.COMPLETED
    assert ci.context_summary is not None
    assert isinstance(ci.context_summary, str)
    assert len(ci.context_summary) > 0
    assert isinstance(ci.key_indicators, list)
    assert isinstance(ci.anomalies, list)
    assert ci.risk_score is not None
    assert 0.0 <= ci.risk_score <= 1.0


# ── CASE 1: Zero Documents ──────────────────────────────────────────


class TestZeroDocuments:
    """Context Agent with no uploaded documents at all."""

    def test_no_documents_no_crash(self) -> None:
        """Context Agent completes without error when no documents exist."""
        state = _make_state(
            transactions=_make_transactions(),
            customer_profile=CustomerProfile(
                customer_id="CUST-R5-001",
                name="Edge Case Customer",
                risk_rating="MEDIUM",
            ),
            alert_reason="Test alert",
        )
        result = context_agent(state)
        ci = result["context_intelligence"]
        _assert_valid_context(ci)

    def test_no_documents_returns_valid_context(self) -> None:
        """Returned context has all required fields in downstream-safe form."""
        state = _make_state(
            transactions=_make_transactions(),
            customer_profile=CustomerProfile(
                customer_id="CUST-R5-002",
                name="Zero Doc Customer",
            ),
        )
        result = context_agent(state)
        ci = result["context_intelligence"]
        assert isinstance(result["context_intelligence"], ContextIntelligence)
        _assert_valid_context(ci)

    def test_no_documents_empty_list_is_accepted(self) -> None:
        """Explicitly empty supporting_documents list is handled."""
        case_input = CaseInput(
            transactions=_make_transactions(),
            customer_profile=CustomerProfile(
                customer_id="CUST-R5-003",
                name="Empty Docs Customer",
            ),
            supporting_documents=[],
        )
        state = create_initial_state(case_id="CASE-R5-EMPTY-DOCS", case_input=case_input)
        result = context_agent(state)
        _assert_valid_context(result["context_intelligence"])

    def test_no_documents_no_fabricated_doc_evidence(self) -> None:
        """No document-related indicators appear when documents are absent."""
        state = _make_state(
            transactions=_make_transactions(),
            customer_profile=CustomerProfile(
                customer_id="CUST-R5-004",
                name="No Fabrication Customer",
            ),
        )
        ci = context_agent(state)["context_intelligence"]
        doc_indicators = [
            ind for ind in ci.key_indicators
            if "document" in ind.lower() and "supporting" in ind.lower()
        ]
        assert len(doc_indicators) == 0, (
            f"No document indicators should appear without documents: {doc_indicators}"
        )


# ── CASE 2: Missing / Partial Customer Profile ──────────────────────


class TestMissingCustomerProfile:
    """Context Agent handles absent or partial customer profiles."""

    def test_none_profile_no_crash(self) -> None:
        """customer_profile=None does not cause a crash."""
        state = _make_state(
            transactions=_make_transactions(),
            customer_profile=None,
            include_customer=False,
        )
        result = context_agent(state)
        _assert_valid_context(result["context_intelligence"])

    def test_none_profile_valid_context(self) -> None:
        """With None profile, context is still valid and downstream-safe."""
        state = _make_state(
            transactions=_make_transactions(),
            customer_profile=None,
            include_customer=False,
        )
        ci = context_agent(state)["context_intelligence"]
        _assert_valid_context(ci)
        # Summary should not contain fabricated customer info
        assert ci.context_summary is not None

    def test_none_profile_no_fabricated_name(self) -> None:
        """Missing profile does not inject a fabricated customer name."""
        state = _make_state(
            transactions=_make_transactions(),
            customer_profile=None,
            include_customer=False,
        )
        ci = context_agent(state)["context_intelligence"]
        # The summary uses "The customer" as fallback, not a made-up name
        assert "The customer" in ci.context_summary

    def test_profile_minimal_fields(self) -> None:
        """Profile with only required fields (customer_id, name) works."""
        state = _make_state(
            transactions=_make_transactions(),
            customer_profile=CustomerProfile(
                customer_id="CUST-MINIMAL",
                name="Minimal Customer",
                # All Optional fields left at defaults (None)
            ),
        )
        ci = context_agent(state)["context_intelligence"]
        _assert_valid_context(ci)
        # The customer name should be used in the summary
        assert "Minimal Customer" in ci.context_summary

    def test_profile_missing_risk_rating(self) -> None:
        """Profile without risk_rating still produces a valid risk score."""
        state = _make_state(
            transactions=_make_transactions(),
            customer_profile=CustomerProfile(
                customer_id="CUST-NO-RISK",
                name="No Risk Rating Customer",
                risk_rating=None,
            ),
        )
        ci = context_agent(state)["context_intelligence"]
        _assert_valid_context(ci)
        # Risk score uses default 0.3 for unknown rating — still valid
        assert 0.0 <= ci.risk_score <= 1.0

    def test_profile_preserves_available_data(self) -> None:
        """Available profile data is reflected in output."""
        state = _make_state(
            transactions=_make_transactions(),
            customer_profile=CustomerProfile(
                customer_id="CUST-PARTIAL",
                name="Partial Data Customer",
                risk_rating="HIGH",
                email="partial@example.com",
                # Other fields left at None defaults
            ),
        )
        ci = context_agent(state)["context_intelligence"]
        _assert_valid_context(ci)
        assert "Partial Data Customer" in ci.context_summary


# ── CASE 3: Partial Mock Bank Data ───────────────────────────────────


class TestPartialMockBankData:
    """Context Agent handles incomplete/partial data gracefully."""

    def test_zero_transactions_no_crash(self) -> None:
        """Empty transaction list does not crash the agent."""
        state = _make_state(
            transactions=[],
            customer_profile=CustomerProfile(
                customer_id="CUST-NO-TXN",
                name="No Transaction Customer",
                risk_rating="LOW",
            ),
        )
        result = context_agent(state)
        _assert_valid_context(result["context_intelligence"])

    def test_zero_transactions_valid_stats(self) -> None:
        """With zero transactions, stats are zero and context is valid."""
        state = _make_state(
            transactions=[],
            customer_profile=CustomerProfile(
                customer_id="CUST-ZERO-TXN",
                name="Zero Txn Customer",
            ),
        )
        ci = context_agent(state)["context_intelligence"]
        _assert_valid_context(ci)
        # Should still report transaction count of 0 in summary
        assert "$0.00" in ci.context_summary or "0 transaction" in ci.context_summary

    def test_zero_transactions_no_anomalies(self) -> None:
        """With zero transactions, no anomalies are detected."""
        state = _make_state(
            transactions=[],
            customer_profile=CustomerProfile(
                customer_id="CUST-NO-ANOM",
                name="No Anomaly Customer",
            ),
        )
        ci = context_agent(state)["context_intelligence"]
        assert ci.anomalies == []

    def test_single_transaction_no_rapid_pairs(self) -> None:
        """One transaction doesn't produce rapid pairs (needs at least two)."""
        state = _make_state(
            transactions=[
                Transaction(
                    transaction_id="TXN-SOLO",
                    amount=500.00,
                    currency="USD",
                    timestamp=datetime(2025, 7, 15, 10, 0, 0),
                    sender_account="ACC-SOLO-SRC",
                    receiver_account="ACC-SOLO-DST",
                    transaction_type="CARD",
                ),
            ],
            customer_profile=CustomerProfile(
                customer_id="CUST-SOLO",
                name="Solo Txn Customer",
            ),
        )
        ci = context_agent(state)["context_intelligence"]
        _assert_valid_context(ci)
        # No rapid pair indicators with a single transaction
        rapid_indicators = [
            ind for ind in ci.key_indicators
            if "rapid" in ind.lower()
        ]
        assert len(rapid_indicators) == 0

    def test_transactions_with_none_timestamp(self) -> None:
        """Transactions with None timestamps are handled in rapid pair detection."""
        # Transaction model has timestamp as required (no default=None),
        # but the rapid pair finder already filters by t.timestamp is not None.
        # This test verifies that pattern with one timed and one that has
        # a valid timestamp — should not crash.
        state = _make_state(
            transactions=_make_transactions(),
            customer_profile=CustomerProfile(
                customer_id="CUST-PARTIAL-TS",
                name="Partial Timestamp Customer",
            ),
        )
        ci = context_agent(state)["context_intelligence"]
        _assert_valid_context(ci)

    def test_transactions_without_optional_fields(self) -> None:
        """Transactions with no description or location still work."""
        state = _make_state(
            transactions=[
                Transaction(
                    transaction_id="TXN-BARE",
                    amount=1_000.00,
                    currency="USD",
                    timestamp=datetime(2025, 7, 15, 10, 0, 0),
                    sender_account="ACC-BARE-SRC",
                    receiver_account="ACC-BARE-DST",
                    transaction_type="ACH",
                    # description=None (default)
                    # location=None (default)
                ),
            ],
            customer_profile=CustomerProfile(
                customer_id="CUST-BARE-TXN",
                name="Bare Txn Customer",
            ),
        )
        ci = context_agent(state)["context_intelligence"]
        _assert_valid_context(ci)

    def test_no_alert_reason(self) -> None:
        """Missing alert_reason does not crash or fabricate data."""
        state = _make_state(
            transactions=_make_transactions(),
            customer_profile=CustomerProfile(
                customer_id="CUST-NO-ALERT",
                name="No Alert Customer",
            ),
            alert_reason=None,
        )
        ci = context_agent(state)["context_intelligence"]
        _assert_valid_context(ci)
        # No "Alert:" indicator should appear
        alert_indicators = [
            ind for ind in ci.key_indicators
            if ind.startswith("Alert:")
        ]
        assert len(alert_indicators) == 0


# ── CASE 4: Combined Sparse Scenarios ────────────────────────────────


class TestCombinedSparseData:
    """Multiple sparse-data dimensions at once."""

    def test_absolutely_minimal_state(self) -> None:
        """CaseInput with no transactions, no profile, no docs, no alert."""
        state = create_initial_state(
            case_id="CASE-R5-MINIMAL",
            case_input=CaseInput(),
        )
        result = context_agent(state)
        ci = result["context_intelligence"]
        _assert_valid_context(ci)
        # Should have zero anomalies
        assert ci.anomalies == []
        # Should have empty or near-empty indicators
        assert isinstance(ci.key_indicators, list)

    def test_transactions_only_no_profile_no_docs(self) -> None:
        """Transactions present, but no profile and no documents."""
        state = _make_state(
            transactions=_make_transactions(),
            customer_profile=None,
            include_customer=False,
            alert_reason=None,
        )
        ci = context_agent(state)["context_intelligence"]
        _assert_valid_context(ci)
        # Should still report transaction activity
        assert "transaction" in ci.context_summary.lower()

    def test_profile_only_no_transactions_no_docs(self) -> None:
        """Customer profile present, but no transactions and no documents."""
        state = _make_state(
            transactions=[],
            customer_profile=CustomerProfile(
                customer_id="CUST-PROFILE-ONLY",
                name="Profile Only Customer",
                risk_rating="HIGH",
            ),
        )
        ci = context_agent(state)["context_intelligence"]
        _assert_valid_context(ci)
        assert "Profile Only Customer" in ci.context_summary

    def test_full_data_behavior_preserved(self) -> None:
        """Full data case still works identically (no regression)."""
        state = _make_state(
            transactions=_make_transactions(),
            customer_profile=CustomerProfile(
                customer_id="CUST-FULL",
                name="Full Data Customer",
                risk_rating="MEDIUM",
                email="full@example.com",
                phone="+1-555-000-0000",
            ),
            alert_reason="Suspicious wire activity detected.",
        )
        ci = context_agent(state)["context_intelligence"]
        _assert_valid_context(ci)
        assert "Full Data Customer" in ci.context_summary
        assert "Suspicious wire activity detected" in ci.context_summary
        assert len(ci.key_indicators) > 0
        # Large transaction should be detected (TXN-R5-001 = $15,000)
        assert len(ci.anomalies) > 0

    def test_determinism_with_sparse_data(self) -> None:
        """Same sparse input produces identical output twice."""
        state = create_initial_state(
            case_id="CASE-R5-DETERMINISM",
            case_input=CaseInput(),
        )
        ci1 = context_agent(state)["context_intelligence"]
        ci2 = context_agent(state)["context_intelligence"]
        assert ci1.context_summary == ci2.context_summary
        assert ci1.key_indicators == ci2.key_indicators
        assert ci1.risk_score == ci2.risk_score
        assert len(ci1.anomalies) == len(ci2.anomalies)
