"""Round 5 tests — Compliance Agent evidence traceability.

Validates that EVERY ComplianceMapping produced by the Compliance Agent
satisfies one of two conditions:

1. Non-empty ``evidence_references`` with IDs that exist in the state.
2. Explicit "insufficient evidence" labelling in the description.

All tests mock ``GeminiClient.generate()`` — no real Gemini API key
is required.

Covers:
- TEST 1 — Supported finding has real evidence
- TEST 2 — Unsupported finding is explicitly labelled
- TEST 3 — Invalid/fabricated evidence references are rejected
- TEST 4 — Multiple mappings are independently traceable
- TEST 5 — Empty compliance mappings remain safe
- TEST 6 — Existing Round 4 behavior is preserved
- TEST 7 — Reasoning hypothesis cross-reference where available
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.agents.compliance_agent import compliance_agent
from app.schemas.investigation_state import (
    AgentStatus,
    AnomalyType,
    CaseInput,
    ComplianceMapping,
    ContextIntelligence,
    CustomerProfile,
    DetectedAnomaly,
    EvidenceComplianceValidation,
    Hypothesis,
    InvestigationReasoning,
    SeverityLevel,
    SupportingDocument,
    Transaction,
    create_initial_state,
)


# ── Helpers ──────────────────────────────────────────────────────────


def _make_state(
    *,
    transactions: list[Transaction] | None = None,
    documents: list[SupportingDocument] | None = None,
    customer: CustomerProfile | None = None,
    context: ContextIntelligence | None = None,
    reasoning: InvestigationReasoning | None = None,
):
    """Build a configurable InvestigationState for testing."""
    txns = transactions or [
        Transaction(
            transaction_id="TXN-TEST-001",
            amount=25_000,
            currency="USD",
            timestamp=datetime(2026, 1, 15, 10, tzinfo=timezone.utc),
            sender_account="SRC-1",
            receiver_account="DST-1",
            transaction_type="WIRE",
        ),
    ]
    docs = documents if documents is not None else [
        SupportingDocument(
            document_id="DOC-TEST-001",
            document_type="BANK_STATEMENT",
            summary="Statement records the reviewed wire transfer.",
            extracted_transactions=["TXN-TEST-001"],
            evidence_references=["EVID-TEST-001"],
        ),
    ]
    cust = customer or CustomerProfile(
        customer_id="CUST-TEST-001",
        name="Test Customer",
        risk_rating="HIGH",
    )
    case_input = CaseInput(
        transactions=txns,
        customer_profile=cust,
        supporting_documents=docs,
        alert_reason="Large wire transfer review",
    )
    state = create_initial_state("CASE-R5-TRACE-001", case_input)
    if context is not None:
        state = state.model_copy(update={"context_intelligence": context})
    else:
        state = state.model_copy(update={"context_intelligence": ContextIntelligence(
            status=AgentStatus.COMPLETED,
            context_summary="Large wire detected.",
            anomalies=[DetectedAnomaly(
                anomaly_id="ANOM-TEST-001",
                anomaly_type=AnomalyType.POINT,
                severity=SeverityLevel.HIGH,
                description="Large wire",
                related_transactions=["TXN-TEST-001"],
            )],
            risk_score=0.8,
        )})
    if reasoning is not None:
        state = state.model_copy(update={"investigation_reasoning": reasoning})
    else:
        state = state.model_copy(update={"investigation_reasoning": InvestigationReasoning(
            status=AgentStatus.COMPLETED,
            hypotheses=[Hypothesis(
                hypothesis_id="HYP-TEST-001",
                title="Suspicious activity review",
                description="The large wire warrants review.",
                confidence=0.7,
                supporting_evidence=["TXN-TEST-001"],
                contradicting_evidence=[],
            )],
        )})
    return state


def _gemini_response(
    mappings: list[ComplianceMapping],
    *,
    gaps: list[str] | None = None,
    summary: str | None = None,
) -> EvidenceComplianceValidation:
    """Build a mock Gemini response."""
    return EvidenceComplianceValidation(
        status=AgentStatus.COMPLETED,
        compliance_mappings=mappings,
        evidence_gaps=gaps or [],
        validation_summary=summary or "Compliance review completed.",
    )


def _patch_gemini(response: EvidenceComplianceValidation):
    """Return a context-manager that patches get_reasoning_client."""
    client = MagicMock()
    client.generate.return_value = response
    return patch("app.agents.compliance_agent.get_reasoning_client", return_value=client)


def _assert_traceable(mapping: ComplianceMapping, available_ids: set[str]) -> None:
    """Assert a single mapping satisfies the Round 5 traceability invariant."""
    if mapping.evidence_references:
        for ref in mapping.evidence_references:
            assert ref in available_ids, (
                f"Evidence reference '{ref}' is not in available IDs: {available_ids}"
            )
    else:
        assert "insufficient evidence" in mapping.description.lower(), (
            f"Mapping '{mapping.regulation_id}' has no evidence references and "
            f"does not contain 'insufficient evidence' in description: "
            f"{mapping.description!r}"
        )


# Known available IDs in the default test state.
_DEFAULT_AVAILABLE_IDS = {
    "TXN-TEST-001",
    "DOC-TEST-001",
    "EVID-TEST-001",
    "CUST-TEST-001",
    "ANOM-TEST-001",
}


# ── TEST 1: Supported finding has real evidence ──────────────────────


def test_supported_finding_has_real_evidence() -> None:
    """A compliance finding with real evidence references retains them
    and does not need an insufficient-evidence label."""
    state = _make_state()
    response = _gemini_response([ComplianceMapping(
        regulation_id="AML-ACTIVITY-001",
        regulation_name="Suspicious Transaction Review",
        description="The wire transfer TXN-TEST-001 warrants review.",
        is_violated=True,
        severity=SeverityLevel.HIGH,
        evidence_references=["TXN-TEST-001", "DOC-TEST-001"],
    )])

    with _patch_gemini(response):
        result = compliance_agent(state)

    validation = result["evidence_compliance_validation"]
    assert validation.status == AgentStatus.COMPLETED
    assert len(validation.compliance_mappings) == 1

    mapping = validation.compliance_mappings[0]
    assert mapping.evidence_references, "Expected non-empty evidence_references"
    assert "TXN-TEST-001" in mapping.evidence_references
    assert "DOC-TEST-001" in mapping.evidence_references
    # All references must be real.
    for ref in mapping.evidence_references:
        assert ref in _DEFAULT_AVAILABLE_IDS
    # No insufficient-evidence label needed.
    assert "insufficient evidence" not in (mapping.description or "").lower()


# ── TEST 2: Unsupported finding is explicitly labelled ───────────────


def test_unsupported_finding_is_explicitly_labelled() -> None:
    """A compliance finding that cannot be tied to any real evidence must
    be explicitly labelled as having insufficient evidence."""
    state = _make_state()
    response = _gemini_response([ComplianceMapping(
        regulation_id="SANCTIONS-CHECK-001",
        regulation_name="Sanctions Screening",
        description="Generic sanctions concern with no supporting data.",
        is_violated=True,
        severity=SeverityLevel.HIGH,
        evidence_references=[],  # No evidence provided.
    )])

    with _patch_gemini(response):
        result = compliance_agent(state)

    validation = result["evidence_compliance_validation"]
    mapping = validation.compliance_mappings[0]

    # Must not fabricate evidence.
    for ref in mapping.evidence_references:
        assert ref in _DEFAULT_AVAILABLE_IDS, f"Fabricated reference: {ref}"

    # If no valid evidence, must have insufficient-evidence label.
    if not mapping.evidence_references:
        assert "insufficient evidence" in mapping.description.lower()
        assert not mapping.is_violated, (
            "Unsupported finding should not be marked as violated"
        )


# ── TEST 3: Invalid/fabricated evidence references are rejected ──────


def test_invalid_fabricated_evidence_references_rejected() -> None:
    """Compliance mappings containing fake evidence IDs must not silently
    accept them. The final result either replaces with real IDs or
    labels as insufficient evidence."""
    state = _make_state()
    response = _gemini_response([ComplianceMapping(
        regulation_id="AML-FAKE-001",
        regulation_name="Fabrication Test",
        description="Generic compliance concern.",
        is_violated=True,
        severity=SeverityLevel.MEDIUM,
        evidence_references=["TXN-INVENTED-999", "DOC-FAKE-123"],
    )])

    with _patch_gemini(response):
        result = compliance_agent(state)

    mapping = result["evidence_compliance_validation"].compliance_mappings[0]

    # No fabricated IDs should survive.
    assert "TXN-INVENTED-999" not in mapping.evidence_references
    assert "DOC-FAKE-123" not in mapping.evidence_references

    # Must satisfy traceability invariant.
    _assert_traceable(mapping, _DEFAULT_AVAILABLE_IDS)


# ── TEST 4: Multiple mappings are independently traceable ────────────


def test_multiple_mappings_independently_traceable() -> None:
    """Multiple compliance mappings — some supported, some not — must
    each independently satisfy the traceability invariant."""
    state = _make_state()
    response = _gemini_response([
        # Mapping 1: supported by transaction evidence.
        ComplianceMapping(
            regulation_id="AML-ACTIVITY-001",
            regulation_name="Transaction Review",
            description="TXN-TEST-001 is flagged for large-value review.",
            is_violated=True,
            severity=SeverityLevel.HIGH,
            evidence_references=["TXN-TEST-001"],
        ),
        # Mapping 2: supported by document/customer evidence.
        ComplianceMapping(
            regulation_id="KYC-CHECK-001",
            regulation_name="KYC Verification",
            description="Customer CUST-TEST-001 KYC check completed.",
            is_violated=False,
            severity=SeverityLevel.LOW,
            evidence_references=["CUST-TEST-001", "DOC-TEST-001"],
        ),
        # Mapping 3: unsupported — no real evidence available.
        ComplianceMapping(
            regulation_id="SANCTIONS-001",
            regulation_name="Sanctions Screening",
            description="General sanctions screening concern.",
            is_violated=True,
            severity=SeverityLevel.MEDIUM,
            evidence_references=[],
        ),
    ])

    with _patch_gemini(response):
        result = compliance_agent(state)

    validation = result["evidence_compliance_validation"]
    assert len(validation.compliance_mappings) == 3

    # Check each mapping independently.
    for mapping in validation.compliance_mappings:
        _assert_traceable(mapping, _DEFAULT_AVAILABLE_IDS)

    # Specifically verify: mapping 1 has real evidence.
    m1 = validation.compliance_mappings[0]
    assert "TXN-TEST-001" in m1.evidence_references

    # Mapping 2 has real evidence.
    m2 = validation.compliance_mappings[1]
    assert m2.evidence_references  # non-empty
    for ref in m2.evidence_references:
        assert ref in _DEFAULT_AVAILABLE_IDS

    # Mapping 3: either derived evidence or insufficient-evidence label.
    m3 = validation.compliance_mappings[2]
    _assert_traceable(m3, _DEFAULT_AVAILABLE_IDS)


# ── TEST 5: Empty compliance mappings remain safe ────────────────────


def test_empty_compliance_mappings_remain_safe() -> None:
    """An empty compliance result must not crash and must remain
    schema-valid."""
    state = _make_state()
    response = _gemini_response(
        [],
        gaps=[],
        summary="No compliance concerns identified.",
    )

    with _patch_gemini(response):
        result = compliance_agent(state)

    validation = result["evidence_compliance_validation"]
    assert validation.status == AgentStatus.COMPLETED
    assert validation.compliance_mappings == []
    # Should still have evidence gaps from _missing_evidence_gaps.
    assert isinstance(validation.evidence_gaps, list)
    assert isinstance(validation.validation_summary, str)


# ── TEST 6: Existing Round 4 behavior is preserved ───────────────────


def test_existing_round4_behavior_preserved() -> None:
    """A realistic Round 4-style compliance scenario must continue
    producing correct output with valid evidence references, proper
    status, and evidence gaps."""
    state = _make_state()
    response = _gemini_response(
        [
            ComplianceMapping(
                regulation_id="AML-ACTIVITY-REVIEW",
                regulation_name="Suspicious transaction review",
                description="The reviewed transfer is unusually large for this case.",
                is_violated=True,
                severity=SeverityLevel.HIGH,
                evidence_references=["TXN-TEST-001", "DOC-TEST-001"],
            ),
        ],
        gaps=["No source-of-funds documentation available."],
        summary="Evidence-backed compliance review completed.",
    )

    with _patch_gemini(response):
        result = compliance_agent(state)

    validation = result["evidence_compliance_validation"]
    assert validation.status == AgentStatus.COMPLETED
    assert len(validation.compliance_mappings) >= 1

    # Valid evidence references are preserved.
    mapping = validation.compliance_mappings[0]
    assert "TXN-TEST-001" in mapping.evidence_references
    assert "DOC-TEST-001" in mapping.evidence_references

    # Evidence gaps are present.
    assert len(validation.evidence_gaps) >= 1

    # Validation summary is present.
    assert validation.validation_summary


def test_round4_fabricated_ref_still_filtered() -> None:
    """Round 4 behavior: fabricated references are filtered while valid
    ones are preserved — this must not regress."""
    state = _make_state()
    response = _gemini_response([ComplianceMapping(
        regulation_id="AML-ACTIVITY-REVIEW",
        regulation_name="Suspicious transaction review",
        description="The reviewed transfer is unusually large for this case.",
        is_violated=True,
        severity=SeverityLevel.HIGH,
        evidence_references=["DOC-TEST-001", "TXN-INVENTED-999"],
    )])

    with _patch_gemini(response):
        mapping = compliance_agent(state)["evidence_compliance_validation"].compliance_mappings[0]

    assert mapping.evidence_references == ["DOC-TEST-001"]


def test_round4_unsupported_finding_becomes_not_violated() -> None:
    """Round 4 behavior: a finding with only fabricated references is
    downgraded to not-violated with LOW severity."""
    state = _make_state()
    response = _gemini_response([ComplianceMapping(
        regulation_id="AML-ACTIVITY-REVIEW",
        regulation_name="Suspicious transaction review",
        description="Generic concern with no supporting data.",
        is_violated=True,
        severity=SeverityLevel.HIGH,
        evidence_references=["DOC-NOT-REAL"],
    )])

    with _patch_gemini(response):
        mapping = compliance_agent(state)["evidence_compliance_validation"].compliance_mappings[0]

    assert mapping.evidence_references == []
    assert not mapping.is_violated
    assert mapping.severity == SeverityLevel.LOW
    assert "insufficient evidence" in mapping.description.lower()


# ── TEST 7: Reasoning hypothesis cross-reference ─────────────────────


def test_reasoning_hypothesis_cross_reference() -> None:
    """When a reasoning hypothesis references a real evidence ID and a
    compliance mapping concerns that same evidence (mentioned in
    description), the mapping must use a real evidence reference instead
    of becoming an unsupported generic claim."""
    reasoning = InvestigationReasoning(
        status=AgentStatus.COMPLETED,
        hypotheses=[Hypothesis(
            hypothesis_id="HYP-TEST-001",
            title="Suspicious wire",
            description="Transaction TXN-TEST-001 is suspicious.",
            confidence=0.75,
            supporting_evidence=["TXN-TEST-001"],
            contradicting_evidence=[],
        )],
    )
    state = _make_state(reasoning=reasoning)

    # The Gemini response has NO evidence_references, but the description
    # mentions TXN-TEST-001 — which is a real ID in the state AND is
    # referenced by the hypothesis.
    response = _gemini_response([ComplianceMapping(
        regulation_id="AML-WIRE-001",
        regulation_name="Wire Transfer Review",
        description="AML concern for transaction TXN-TEST-001 — large wire transfer.",
        is_violated=True,
        severity=SeverityLevel.HIGH,
        evidence_references=[],  # No direct references from Gemini.
    )])

    with _patch_gemini(response):
        result = compliance_agent(state)

    mapping = result["evidence_compliance_validation"].compliance_mappings[0]

    # The mapping should have derived TXN-TEST-001 from the description
    # cross-referenced with the hypothesis supporting_evidence.
    assert mapping.evidence_references, (
        "Expected non-empty evidence_references derived from hypothesis cross-reference"
    )
    assert "TXN-TEST-001" in mapping.evidence_references
    # Must be a real ID.
    assert "TXN-TEST-001" in _DEFAULT_AVAILABLE_IDS


def test_reasoning_hypothesis_no_match_still_labels_insufficient() -> None:
    """When reasoning hypotheses exist but don't share evidence with the
    compliance mapping, the mapping must still be labelled as
    insufficient evidence."""
    reasoning = InvestigationReasoning(
        status=AgentStatus.COMPLETED,
        hypotheses=[Hypothesis(
            hypothesis_id="HYP-TEST-001",
            title="Unrelated hypothesis",
            description="Completely unrelated analysis.",
            confidence=0.6,
            supporting_evidence=["TXN-TEST-001"],
            contradicting_evidence=[],
        )],
    )
    state = _make_state(reasoning=reasoning)

    # Description mentions nothing that matches available IDs.
    response = _gemini_response([ComplianceMapping(
        regulation_id="SANCTIONS-001",
        regulation_name="Sanctions Screening",
        description="General sanctions concern with no specific evidence.",
        is_violated=True,
        severity=SeverityLevel.HIGH,
        evidence_references=[],
    )])

    with _patch_gemini(response):
        result = compliance_agent(state)

    mapping = result["evidence_compliance_validation"].compliance_mappings[0]

    # No derivation should produce evidence for this generic description.
    if not mapping.evidence_references:
        assert "insufficient evidence" in mapping.description.lower()
    else:
        # If any evidence was derived, it must be real.
        for ref in mapping.evidence_references:
            assert ref in _DEFAULT_AVAILABLE_IDS


def test_hypothesis_ids_and_unverified_anomaly_links_are_not_evidence() -> None:
    """Generated reasoning IDs and anomaly links cannot establish a finding.

    A hypothesis is analysis, not source evidence. Likewise, an anomaly's
    related transaction string cannot create a transaction that is absent from
    the case input or document evidence.
    """
    state = _make_state()
    anomaly = state.context_intelligence.anomalies[0].model_copy(update={
        "related_transactions": ["TXN-NOT-IN-CASE-001"],
    })
    state = state.model_copy(update={
        "context_intelligence": state.context_intelligence.model_copy(
            update={"anomalies": [anomaly]},
        ),
    })
    response = _gemini_response([ComplianceMapping(
        regulation_id="AML-TRACEABILITY-001",
        regulation_name="Traceability Review",
        description="Claim based only on generated analysis.",
        is_violated=True,
        severity=SeverityLevel.HIGH,
        evidence_references=["HYP-TEST-001", "TXN-NOT-IN-CASE-001"],
    )])

    with _patch_gemini(response):
        mapping = compliance_agent(state)["evidence_compliance_validation"].compliance_mappings[0]

    assert mapping.evidence_references == []
    assert not mapping.is_violated
    assert mapping.severity == SeverityLevel.LOW
    assert "insufficient evidence" in mapping.description.lower()


def test_reasoning_absent_does_not_crash() -> None:
    """When investigation_reasoning is None, the compliance agent must
    still function correctly without crashing."""
    state = _make_state(reasoning=None)
    # Remove reasoning from state.
    state = state.model_copy(update={"investigation_reasoning": None})

    response = _gemini_response([ComplianceMapping(
        regulation_id="AML-ACTIVITY-001",
        regulation_name="Transaction Review",
        description="Generic concern.",
        is_violated=False,
        severity=SeverityLevel.LOW,
        evidence_references=[],
    )])

    with _patch_gemini(response):
        result = compliance_agent(state)

    validation = result["evidence_compliance_validation"]
    assert validation.status == AgentStatus.COMPLETED
    # The mapping must still satisfy traceability.
    for mapping in validation.compliance_mappings:
        _assert_traceable(mapping, {
            "TXN-TEST-001", "DOC-TEST-001", "EVID-TEST-001",
            "CUST-TEST-001", "ANOM-TEST-001",
            # HYP-TEST-001 is NOT available when reasoning is None.
        })
