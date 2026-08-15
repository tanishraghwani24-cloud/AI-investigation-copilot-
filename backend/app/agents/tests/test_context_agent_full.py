"""Round 3 tests for the Context & Evidence Intelligence Agent.

Covers:
- TEST 1: No supporting documents — existing Round 2 behaviour
- TEST 2: Document with extracted text — evidence reflected
- TEST 3: Document changes synthesis — summary differs
- TEST 4: Empty/None extracted text — no crash, no fabrication
- TEST 5: Multiple documents — evidence from both reflected
- TEST 6: Determinism — same input produces same output
"""

from datetime import datetime

from app.agents.context_agent import context_agent
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    ContextIntelligence,
    CustomerProfile,
    InvestigationState,
    SupportingDocument,
    Transaction,
    create_initial_state,
)


# ── Helpers ──────────────────────────────────────────────────────────


def _make_base_case_input() -> CaseInput:
    """Create a CaseInput with transactions but no documents."""
    transactions = [
        Transaction(
            transaction_id="TXN-R3-001",
            amount=15_000.00,
            currency="USD",
            timestamp=datetime(2025, 7, 15, 9, 30, 0),
            sender_account="ACC-SRC-R3",
            receiver_account="ACC-DST-R3",
            transaction_type="WIRE",
            channel="ONLINE",
            description="Large wire transfer",
            location="New York, US",
        ),
        Transaction(
            transaction_id="TXN-R3-002",
            amount=3_500.00,
            currency="USD",
            timestamp=datetime(2025, 7, 15, 9, 45, 0),
            sender_account="ACC-SRC-R3",
            receiver_account="ACC-DST-R3-B",
            transaction_type="ACH",
            channel="ONLINE",
            description="Supplier payment",
            location="New York, US",
        ),
        Transaction(
            transaction_id="TXN-R3-003",
            amount=800.00,
            currency="USD",
            timestamp=datetime(2025, 7, 15, 14, 0, 0),
            sender_account="ACC-SRC-R3",
            receiver_account="ACC-DST-R3-C",
            transaction_type="CARD",
            channel="MOBILE",
            description="Equipment purchase",
            location="Chicago, US",
        ),
    ]
    return CaseInput(
        transactions=transactions,
        customer_profile=CustomerProfile(
            customer_id="CUST-R3-001",
            name="Round Three Test Customer",
            risk_rating="MEDIUM",
        ),
        alert_reason="Large wire transfer flagged by rule engine.",
    )


def _make_state_no_docs() -> InvestigationState:
    """State with no supporting documents."""
    return create_initial_state(
        case_id="CASE-R3-NO-DOCS",
        case_input=_make_base_case_input(),
    )


def _make_state_with_doc(
    extracted_text: str | None,
    file_name: str = "statement.pdf",
    document_type: str = "BANK_STATEMENT",
    document_id: str = "DOC-R3-001",
) -> InvestigationState:
    """State with one supporting document."""
    case_input = _make_base_case_input()
    case_input.supporting_documents = [
        SupportingDocument(
            document_id=document_id,
            document_type=document_type,
            file_name=file_name,
            extracted_text=extracted_text,
        ),
    ]
    return create_initial_state(
        case_id="CASE-R3-WITH-DOC",
        case_input=case_input,
    )


# ── TEST 1: No supporting documents ─────────────────────────────────


class TestNoDocument:
    """Context Agent with no supporting documents (Round 2 behaviour)."""

    def test_context_intelligence_exists(self) -> None:
        """Result contains context_intelligence."""
        state = _make_state_no_docs()
        result = context_agent(state)
        assert "context_intelligence" in result
        assert isinstance(result["context_intelligence"], ContextIntelligence)

    def test_status_completed(self) -> None:
        """Status is COMPLETED."""
        state = _make_state_no_docs()
        ci = context_agent(state)["context_intelligence"]
        assert ci.status == AgentStatus.COMPLETED

    def test_context_summary_non_empty(self) -> None:
        """context_summary is non-empty."""
        state = _make_state_no_docs()
        ci = context_agent(state)["context_intelligence"]
        assert ci.context_summary is not None
        assert len(ci.context_summary) > 0

    def test_key_indicators_non_empty(self) -> None:
        """key_indicators list is non-empty."""
        state = _make_state_no_docs()
        ci = context_agent(state)["context_intelligence"]
        assert len(ci.key_indicators) > 0

    def test_risk_score_in_range(self) -> None:
        """Risk score is between 0.0 and 1.0."""
        state = _make_state_no_docs()
        ci = context_agent(state)["context_intelligence"]
        assert ci.risk_score is not None
        assert 0.0 <= ci.risk_score <= 1.0


# ── TEST 2: Document with extracted text ─────────────────────────────


class TestDocumentWithExtractedText:
    """Context Agent incorporates document evidence."""

    _EXTRACTED_TEXT = (
        "Account statement shows an international wire transfer "
        "of USD 25000 on 2026-01-15."
    )

    def test_context_intelligence_exists(self) -> None:
        """Result contains context_intelligence."""
        state = _make_state_with_doc(self._EXTRACTED_TEXT)
        result = context_agent(state)
        assert "context_intelligence" in result

    def test_context_summary_non_empty(self) -> None:
        """context_summary is non-empty."""
        state = _make_state_with_doc(self._EXTRACTED_TEXT)
        ci = context_agent(state)["context_intelligence"]
        assert ci.context_summary is not None
        assert len(ci.context_summary) > 0

    def test_context_summary_reflects_document_evidence(self) -> None:
        """context_summary mentions evidence from the document."""
        state = _make_state_with_doc(self._EXTRACTED_TEXT)
        ci = context_agent(state)["context_intelligence"]
        summary_lower = ci.context_summary.lower()
        # The document mentions an international wire transfer of USD 25000.
        # At least one of these distinctive terms should appear.
        has_transfer = "wire transfer" in summary_lower or "international wire" in summary_lower
        has_amount = "25000" in ci.context_summary or "25,000" in ci.context_summary
        assert has_transfer or has_amount, (
            f"Expected document evidence in summary, got: {ci.context_summary}"
        )

    def test_key_indicator_reflects_document(self) -> None:
        """At least one key indicator reflects document evidence."""
        state = _make_state_with_doc(self._EXTRACTED_TEXT)
        ci = context_agent(state)["context_intelligence"]
        doc_indicators = [
            ind for ind in ci.key_indicators
            if "document" in ind.lower() or "supporting" in ind.lower()
        ]
        assert len(doc_indicators) >= 1, (
            f"Expected document-related indicator, got: {ci.key_indicators}"
        )


# ── TEST 3: Document changes synthesis ───────────────────────────────


class TestDocumentChangesSynthesis:
    """Context summary differs when document evidence is added."""

    _EXTRACTED_TEXT = (
        "Account statement shows an international wire transfer "
        "of USD 25000 on 2026-01-15."
    )

    def test_summary_differs_with_document(self) -> None:
        """Summary is different with vs. without document evidence."""
        state_a = _make_state_no_docs()
        state_b = _make_state_with_doc(self._EXTRACTED_TEXT)

        ci_a = context_agent(state_a)["context_intelligence"]
        ci_b = context_agent(state_b)["context_intelligence"]

        assert ci_a.context_summary != ci_b.context_summary, (
            "Context summary should change when document evidence is added."
        )

    def test_document_evidence_in_b_only(self) -> None:
        """Document-related evidence appears only in the version with docs."""
        state_a = _make_state_no_docs()
        state_b = _make_state_with_doc(self._EXTRACTED_TEXT)

        ci_a = context_agent(state_a)["context_intelligence"]
        ci_b = context_agent(state_b)["context_intelligence"]

        # B should reference document evidence
        summary_b_lower = ci_b.context_summary.lower()
        has_doc_evidence = (
            "supporting document" in summary_b_lower
            or "document evidence" in summary_b_lower
            or "wire transfer" in summary_b_lower
        )
        assert has_doc_evidence, (
            f"Expected document evidence in B summary: {ci_b.context_summary}"
        )


# ── TEST 4: Empty document ───────────────────────────────────────────


class TestEmptyDocument:
    """Documents with None/empty/whitespace extracted_text."""

    def test_none_extracted_text_no_crash(self) -> None:
        """Document with None extracted_text does not crash."""
        state = _make_state_with_doc(extracted_text=None)
        result = context_agent(state)
        ci = result["context_intelligence"]
        assert ci.status == AgentStatus.COMPLETED
        assert ci.context_summary is not None
        assert len(ci.context_summary) > 0

    def test_empty_string_no_crash(self) -> None:
        """Document with empty string extracted_text does not crash."""
        state = _make_state_with_doc(extracted_text="")
        result = context_agent(state)
        ci = result["context_intelligence"]
        assert ci.status == AgentStatus.COMPLETED

    def test_whitespace_only_no_crash(self) -> None:
        """Document with whitespace-only extracted_text does not crash."""
        state = _make_state_with_doc(extracted_text="   \n\t  ")
        result = context_agent(state)
        ci = result["context_intelligence"]
        assert ci.status == AgentStatus.COMPLETED

    def test_no_fabricated_evidence(self) -> None:
        """Empty document does not add fabricated document indicators."""
        state_no_docs = _make_state_no_docs()
        state_empty_doc = _make_state_with_doc(extracted_text=None)

        ci_no = context_agent(state_no_docs)["context_intelligence"]
        ci_empty = context_agent(state_empty_doc)["context_intelligence"]

        # Empty document should not introduce document-related indicators
        doc_indicators = [
            ind for ind in ci_empty.key_indicators
            if "document" in ind.lower() and "supporting" in ind.lower()
        ]
        assert len(doc_indicators) == 0, (
            f"Empty document should not produce document indicators: {doc_indicators}"
        )

        # Summaries should be the same (no document evidence appended)
        assert ci_no.context_summary == ci_empty.context_summary


# ── TEST 5: Multiple documents ───────────────────────────────────────


class TestMultipleDocuments:
    """Multiple documents with different evidence."""

    def test_both_documents_reflected(self) -> None:
        """Evidence from both documents appears in synthesis."""
        case_input = _make_base_case_input()
        case_input.supporting_documents = [
            SupportingDocument(
                document_id="DOC-MULTI-001",
                document_type="BANK_STATEMENT",
                file_name="statement_jan.pdf",
                extracted_text=(
                    "Account statement shows an international wire transfer "
                    "of USD 25000 on 2026-01-15."
                ),
            ),
            SupportingDocument(
                document_id="DOC-MULTI-002",
                document_type="INVOICE",
                file_name="invoice_feb.pdf",
                extracted_text=(
                    "Invoice for consulting services totalling USD 8500 "
                    "dated 2026-02-20. Payment via bank transfer."
                ),
            ),
        ]
        state = create_initial_state(
            case_id="CASE-R3-MULTI",
            case_input=case_input,
        )
        ci = context_agent(state)["context_intelligence"]

        # Both documents should contribute to the summary
        summary = ci.context_summary
        has_25000 = "25000" in summary or "25,000" in summary
        has_8500 = "8500" in summary or "8,500" in summary
        assert has_25000, f"Expected USD 25000 evidence in summary: {summary}"
        assert has_8500, f"Expected USD 8500 evidence in summary: {summary}"

    def test_multiple_document_indicators(self) -> None:
        """Key indicators reflect evidence from multiple documents."""
        case_input = _make_base_case_input()
        case_input.supporting_documents = [
            SupportingDocument(
                document_id="DOC-MULTI-A",
                document_type="BANK_STATEMENT",
                file_name="stmt.pdf",
                extracted_text="Wire transfer of USD 12000 detected.",
            ),
            SupportingDocument(
                document_id="DOC-MULTI-B",
                document_type="INVOICE",
                file_name="inv.pdf",
                extracted_text="Payment of USD 5000 for services.",
            ),
        ]
        state = create_initial_state(
            case_id="CASE-R3-MULTI-IND",
            case_input=case_input,
        )
        ci = context_agent(state)["context_intelligence"]

        # Should have indicator noting 2 supporting documents
        doc_count_indicators = [
            ind for ind in ci.key_indicators
            if "2 supporting document" in ind.lower()
        ]
        assert len(doc_count_indicators) >= 1, (
            f"Expected '2 supporting document' indicator: {ci.key_indicators}"
        )


# ── TEST 6: Determinism ─────────────────────────────────────────────


class TestDeterminism:
    """Same InvestigationState + same documents → same output."""

    _EXTRACTED_TEXT = (
        "Account statement shows an international wire transfer "
        "of USD 25000 on 2026-01-15."
    )

    def test_identical_results_no_docs(self) -> None:
        """Two calls with same state (no docs) produce identical output."""
        state = _make_state_no_docs()
        ci1 = context_agent(state)["context_intelligence"]
        ci2 = context_agent(state)["context_intelligence"]

        assert ci1.context_summary == ci2.context_summary
        assert ci1.key_indicators == ci2.key_indicators
        assert ci1.risk_score == ci2.risk_score
        assert len(ci1.anomalies) == len(ci2.anomalies)

    def test_identical_results_with_docs(self) -> None:
        """Two calls with same state (with docs) produce identical output."""
        state = _make_state_with_doc(self._EXTRACTED_TEXT)
        ci1 = context_agent(state)["context_intelligence"]
        ci2 = context_agent(state)["context_intelligence"]

        assert ci1.context_summary == ci2.context_summary
        assert ci1.key_indicators == ci2.key_indicators
        assert ci1.risk_score == ci2.risk_score
        assert len(ci1.anomalies) == len(ci2.anomalies)
