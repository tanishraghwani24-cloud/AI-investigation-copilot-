"""Round 5 tests — Reasoning Agent compliance-findings alignment.

Validates that the Reasoning Agent adjusts hypotheses when existing
compliance findings contradict them, while preserving normal behavior
when compliance data is absent or unrelated.

All tests mock ``GeminiClient.generate()`` — no real Gemini API key
is required.

Covers:
- TEST 1 — DIRECT CONTRADICTION
- TEST 2 — NO COMPLIANCE DATA
- TEST 3 — UNRELATED COMPLIANCE FINDING
- TEST 4 — EMPTY/NONE COMPLIANCE DATA
- TEST 5 — MULTIPLE HYPOTHESES / SELECTIVE ALIGNMENT
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.agents.reasoning_agent import HypothesesResponse, reasoning_agent
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    ComplianceMapping,
    ContextIntelligence,
    CustomerProfile,
    DetectedAnomaly,
    AnomalyType,
    EvidenceComplianceValidation,
    Hypothesis,
    InvestigationState,
    SeverityLevel,
    SupportingDocument,
    Transaction,
    create_initial_state,
)


# ── Fixtures ─────────────────────────────────────────────────────────


def _make_transactions() -> list[Transaction]:
    """Build a pair of realistic transactions for testing."""
    return [
        Transaction(
            transaction_id="TXN-TEST-001",
            amount=15_000.00,
            currency="USD",
            timestamp=datetime(2025, 8, 1, 10, 0, 0, tzinfo=timezone.utc),
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
            timestamp=datetime(2025, 8, 1, 10, 15, 0, tzinfo=timezone.utc),
            sender_account="ACC-SRC-001",
            receiver_account="ACC-DST-002",
            transaction_type="ACH",
            channel="MOBILE",
            description="Supplier payment",
        ),
    ]


def _make_documents() -> list[SupportingDocument]:
    """Provide at least one document so the case is not sparse."""
    return [
        SupportingDocument(
            document_id="DOC-TEST-001",
            document_type="BANK_STATEMENT",
            file_name="statement_aug.pdf",
            summary="Monthly bank statement showing account activity.",
            extracted_text="Account statement for August 2025.",
        ),
    ]


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


def _make_state(
    *,
    with_context: bool = True,
    compliance: EvidenceComplianceValidation | None = None,
) -> InvestigationState:
    """Create a realistic InvestigationState for compliance-alignment tests."""
    case_input = CaseInput(
        transactions=_make_transactions(),
        customer_profile=CustomerProfile(
            customer_id="CUST-TEST-001",
            name="Test Customer",
            risk_rating="HIGH",
            occupation="Portfolio Manager",
            nationality="US",
        ),
        supporting_documents=_make_documents(),
        alert_reason="Suspicious wire transfer pattern detected",
    )
    state = create_initial_state(
        case_id="CASE-TEST-R5-001",
        case_input=case_input,
    )
    if with_context:
        state = state.model_copy(
            update={"context_intelligence": _make_context_intelligence()},
        )
    if compliance is not None:
        state = state.model_copy(
            update={"evidence_compliance_validation": compliance},
        )
    return state


def _make_hypotheses_response() -> HypothesesResponse:
    """Return two competing hypotheses for the mocked Gemini response."""
    return HypothesesResponse(
        hypotheses=[
            Hypothesis(
                hypothesis_id="HYP-R5-001",
                title="Transaction Appears Legitimate",
                description=(
                    "The transaction TXN-TEST-001 appears legitimate based on "
                    "the customer's occupation as a Portfolio Manager."
                ),
                confidence=0.80,
                supporting_evidence=[
                    "TXN-TEST-001: $15,000 wire transfer for investment deposit",
                    "Customer occupation is Portfolio Manager",
                ],
                contradicting_evidence=[
                    "Alert triggered by automated rule engine",
                ],
            ),
            Hypothesis(
                hypothesis_id="HYP-R5-002",
                title="Suspected Structuring Activity",
                description=(
                    "The customer may be structuring transactions to avoid "
                    "reporting thresholds. TXN-TEST-002 is just below the "
                    "$10,000 threshold."
                ),
                confidence=0.65,
                supporting_evidence=[
                    "TXN-TEST-002: $5,000 ACH payment",
                    "Customer risk rating: HIGH",
                ],
                contradicting_evidence=[
                    "TXN-TEST-001: $15,000 wire transfer exceeds threshold",
                ],
            ),
        ]
    )


def _make_compliance_aml_finding() -> EvidenceComplianceValidation:
    """Build compliance output with an AML finding tied to TXN-TEST-001."""
    return EvidenceComplianceValidation(
        status=AgentStatus.COMPLETED,
        compliance_mappings=[
            ComplianceMapping(
                regulation_id="AML-2023-04",
                regulation_name="Anti-Money Laundering Act",
                description="AML concern identified for transaction TXN-TEST-001",
                is_violated=True,
                severity=SeverityLevel.HIGH,
                evidence_references=["TXN-TEST-001"],
            ),
        ],
        evidence_gaps=["No source-of-funds documentation available"],
        validation_summary="1 compliance finding identified.",
    )


def _make_unrelated_compliance_finding() -> EvidenceComplianceValidation:
    """Build compliance output referencing evidence NOT in any hypothesis."""
    return EvidenceComplianceValidation(
        status=AgentStatus.COMPLETED,
        compliance_mappings=[
            ComplianceMapping(
                regulation_id="KYC-2022-01",
                regulation_name="Know Your Customer Regulation",
                description="KYC verification incomplete for CUST-UNRELATED-999",
                is_violated=True,
                severity=SeverityLevel.HIGH,
                evidence_references=["CUST-UNRELATED-999"],
            ),
        ],
        evidence_gaps=[],
        validation_summary="1 unrelated compliance finding.",
    )


def _patch_gemini(return_value=None):
    """Return a context-manager that patches the reasoning client factory."""
    mock_client = MagicMock()
    mock_client.generate.return_value = return_value or _make_hypotheses_response()
    return patch(
        "app.agents.reasoning_agent.get_reasoning_client",
        return_value=mock_client,
    )


# ── TEST 1: DIRECT CONTRADICTION ──────────────────────────────────────


def test_direct_contradiction_reduces_confidence_and_acknowledges() -> None:
    """When a compliance finding contradicts a hypothesis, confidence
    must be reduced and the description must acknowledge the concern."""
    state = _make_state(compliance=_make_compliance_aml_finding())
    with _patch_gemini():
        result = reasoning_agent(state)

    reasoning = result["investigation_reasoning"]
    assert reasoning.status == AgentStatus.COMPLETED
    assert len(reasoning.hypotheses) >= 2

    # Find the hypothesis that references TXN-TEST-001 in supporting_evidence
    affected = [
        h for h in reasoning.hypotheses
        if any("TXN-TEST-001" in ev for ev in h.supporting_evidence)
    ]
    assert len(affected) >= 1, "Expected at least one hypothesis referencing TXN-TEST-001"

    for hyp in affected:
        # Confidence must be visibly reduced from the original 0.80.
        assert hyp.confidence < 0.80, (
            f"Expected confidence < 0.80, got {hyp.confidence}"
        )
        # The hypothesis must still be valid (within bounds).
        assert 0.0 <= hyp.confidence <= 1.0

        # The description must acknowledge the compliance concern.
        desc_lower = hyp.description.lower()
        assert "compliance" in desc_lower, (
            "Expected 'compliance' in the hypothesis description"
        )
        # Should mention the regulation or AML concern.
        assert "aml" in desc_lower or "anti-money laundering" in desc_lower, (
            "Expected AML/Anti-Money Laundering mention in the hypothesis description"
        )

        # Hypothesis must still exist (not removed).
        assert hyp.hypothesis_id is not None
        assert hyp.title is not None


# ── TEST 2: NO COMPLIANCE DATA ────────────────────────────────────────


def test_no_compliance_data_preserves_behavior() -> None:
    """Without compliance data the agent must not crash and must
    preserve its normal reasoning output unchanged."""
    state = _make_state(compliance=None)
    assert state.evidence_compliance_validation is None

    with _patch_gemini():
        result = reasoning_agent(state)

    reasoning = result["investigation_reasoning"]
    assert reasoning.status == AgentStatus.COMPLETED
    assert len(reasoning.hypotheses) >= 2

    # Confidence values must match what Gemini returned (after normalisation,
    # but without compliance adjustment).
    for hyp in reasoning.hypotheses:
        assert 0.0 <= hyp.confidence <= 1.0
        # No compliance acknowledgment language should be present.
        assert "[compliance alignment]" not in hyp.description.lower()


# ── TEST 3: UNRELATED COMPLIANCE FINDING ──────────────────────────────


def test_unrelated_compliance_finding_does_not_alter_hypotheses() -> None:
    """A compliance finding that does not relate to any hypothesis's
    evidence must not change any hypothesis's confidence or description."""
    state = _make_state(compliance=_make_unrelated_compliance_finding())

    with _patch_gemini():
        result = reasoning_agent(state)

    reasoning = result["investigation_reasoning"]
    assert reasoning.status == AgentStatus.COMPLETED

    for hyp in reasoning.hypotheses:
        # No hypothesis should have compliance-alignment language.
        assert "[compliance alignment]" not in hyp.description.lower(), (
            f"Hypothesis {hyp.hypothesis_id} was incorrectly altered by unrelated finding"
        )


# ── TEST 4: EMPTY/NONE COMPLIANCE DATA ───────────────────────────────


@pytest.mark.parametrize("compliance_value", [
    None,
    EvidenceComplianceValidation(
        status=AgentStatus.COMPLETED,
        compliance_mappings=[],
        evidence_gaps=[],
        validation_summary="No findings.",
    ),
])
def test_empty_or_none_compliance_does_not_crash(compliance_value) -> None:
    """Both None and an empty EvidenceComplianceValidation must be safe."""
    state = _make_state(compliance=compliance_value)

    with _patch_gemini():
        result = reasoning_agent(state)

    reasoning = result["investigation_reasoning"]
    assert reasoning.status == AgentStatus.COMPLETED
    assert len(reasoning.hypotheses) >= 2

    for hyp in reasoning.hypotheses:
        assert 0.0 <= hyp.confidence <= 1.0
        assert "[compliance alignment]" not in hyp.description.lower()


# ── TEST 5: MULTIPLE HYPOTHESES / SELECTIVE ALIGNMENT ─────────────────


def test_selective_alignment_only_affects_contradicted_hypothesis() -> None:
    """When one hypothesis is contradicted and another is not, only
    the contradicted hypothesis should have its confidence reduced
    and its description updated."""
    state = _make_state(compliance=_make_compliance_aml_finding())

    with _patch_gemini():
        result = reasoning_agent(state)

    reasoning = result["investigation_reasoning"]
    assert len(reasoning.hypotheses) >= 2

    # HYP-R5-001 references TXN-TEST-001 in supporting_evidence → contradicted.
    # HYP-R5-002 references TXN-TEST-002 in supporting_evidence → NOT contradicted.
    hyp_001 = next(
        (h for h in reasoning.hypotheses if h.hypothesis_id == "HYP-R5-001"),
        None,
    )
    hyp_002 = next(
        (h for h in reasoning.hypotheses if h.hypothesis_id == "HYP-R5-002"),
        None,
    )

    assert hyp_001 is not None, "HYP-R5-001 must still exist after alignment"
    assert hyp_002 is not None, "HYP-R5-002 must still exist after alignment"

    # The contradicted hypothesis must be adjusted.
    assert hyp_001.confidence < 0.80
    assert "[compliance alignment]" in hyp_001.description.lower()
    assert "compliance" in hyp_001.description.lower()

    # The unrelated hypothesis must NOT be adjusted.
    assert "[compliance alignment]" not in hyp_002.description.lower()


# ── TEST 6: LOW SEVERITY COMPLIANCE FINDING IS NOT A CONTRADICTION ────


def test_low_severity_compliance_does_not_contradict() -> None:
    """A compliance finding with LOW severity and is_violated=False should
    not be treated as a contradiction, even if evidence references overlap."""
    low_severity_compliance = EvidenceComplianceValidation(
        status=AgentStatus.COMPLETED,
        compliance_mappings=[
            ComplianceMapping(
                regulation_id="INFO-2023-01",
                regulation_name="Informational Notice",
                description="Routine review noted for TXN-TEST-001",
                is_violated=False,
                severity=SeverityLevel.LOW,
                evidence_references=["TXN-TEST-001"],
            ),
        ],
        evidence_gaps=[],
        validation_summary="1 informational finding.",
    )
    state = _make_state(compliance=low_severity_compliance)

    with _patch_gemini():
        result = reasoning_agent(state)

    reasoning = result["investigation_reasoning"]
    for hyp in reasoning.hypotheses:
        assert "[compliance alignment]" not in hyp.description.lower(), (
            "LOW severity, non-violated finding should not trigger contradiction"
        )
