"""Tests for the evidence-backed Compliance Agent (Harshita - Round 4)."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from app.agents.compliance_agent import _build_prompt, compliance_agent
from app.graph.nodes.compliance_node import compliance_node
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    ComplianceMapping,
    ContextIntelligence,
    CurrentStage,
    DetectedAnomaly,
    EvidenceComplianceValidation,
    Hypothesis,
    InvestigationReasoning,
    SeverityLevel,
    SupportingDocument,
    Transaction,
    create_initial_state,
)


def _state(*, documents: bool = True):
    transaction = Transaction(
        transaction_id="TXN-COMP-001", amount=25_000, currency="USD",
        timestamp=datetime(2026, 1, 15, 10), sender_account="SRC-1",
        receiver_account="DST-1", transaction_type="WIRE",
    )
    case_input = CaseInput(transactions=[transaction], alert_reason="Large transfer review")
    if documents:
        case_input.supporting_documents = [SupportingDocument(
            document_id="DOC-COMP-001", document_type="BANK_STATEMENT",
            summary="Statement records the reviewed wire transfer.",
            extracted_transactions=["TXN-COMP-001"], evidence_references=["EVID-COMP-001"],
        )]
    state = create_initial_state("CASE-COMP-001", case_input)
    state.context_intelligence = ContextIntelligence(
        status=AgentStatus.COMPLETED, context_summary="Large wire detected.",
        anomalies=[DetectedAnomaly(
            anomaly_id="ANOM-COMP-001", anomaly_type="POINT", severity=SeverityLevel.HIGH,
            description="Large wire", related_transactions=["TXN-COMP-001"],
        )], risk_score=0.8,
    )
    state.investigation_reasoning = InvestigationReasoning(
        status=AgentStatus.COMPLETED,
        hypotheses=[Hypothesis(
            hypothesis_id="HYP-COMP-001", title="Suspicious activity review",
            description="The large wire warrants review.", confidence=0.7,
            supporting_evidence=["TXN-COMP-001"], contradicting_evidence=[],
        )],
    )
    return state


def _response(*, references: list[str] | None = None) -> EvidenceComplianceValidation:
    return EvidenceComplianceValidation(
        status=AgentStatus.COMPLETED,
        compliance_mappings=[ComplianceMapping(
            regulation_id="AML-ACTIVITY-REVIEW", regulation_name="Suspicious transaction review",
            description="The reviewed transfer is unusually large for this case.",
            is_violated=True, severity=SeverityLevel.HIGH,
            evidence_references=references if references is not None else ["TXN-COMP-001", "DOC-COMP-001"],
        )],
        evidence_gaps=[], validation_summary="Evidence-backed compliance review completed.",
    )


def _patch(response: EvidenceComplianceValidation):
    client = MagicMock()
    client.generate.return_value = response
    return patch("app.agents.compliance_agent.get_reasoning_client", return_value=client)


def test_basic_compliance_output_and_context_reasoning_input() -> None:
    state = _state()
    with _patch(_response()) as client_factory:
        result = compliance_agent(state)
    validation = result["evidence_compliance_validation"]
    assert validation.status == AgentStatus.COMPLETED
    assert validation.compliance_mappings
    prompt = client_factory.return_value.generate.call_args.args[0]
    assert "Large wire detected." in prompt
    assert "HYP-COMP-001" in prompt


def test_real_document_and_transaction_evidence_references_are_preserved() -> None:
    with _patch(_response()):
        mapping = compliance_agent(_state())["evidence_compliance_validation"].compliance_mappings[0]
    assert mapping.evidence_references == ["TXN-COMP-001", "DOC-COMP-001"]


def test_no_fabricated_evidence_reference_survives() -> None:
    with _patch(_response(references=["DOC-COMP-001", "TXN-INVENTED-999"])):
        mapping = compliance_agent(_state())["evidence_compliance_validation"].compliance_mappings[0]
    assert mapping.evidence_references == ["DOC-COMP-001"]


def test_unsupported_finding_is_explicitly_insufficient_and_not_a_violation() -> None:
    with _patch(_response(references=["DOC-NOT-REAL"])):
        mapping = compliance_agent(_state())["evidence_compliance_validation"].compliance_mappings[0]
    assert mapping.evidence_references == []
    assert not mapping.is_violated
    assert "insufficient evidence" in mapping.description.lower()


def test_missing_evidence_and_sparse_input_do_not_invent_references() -> None:
    state = _state(documents=False)
    with _patch(_response(references=[])):
        validation = compliance_agent(state)["evidence_compliance_validation"]
    assert any("no supporting documents" in gap.lower() for gap in validation.evidence_gaps)
    assert all(not mapping.evidence_references for mapping in validation.compliance_mappings)


def test_document_extracted_evidence_reference_is_available() -> None:
    with _patch(_response(references=["EVID-COMP-001"])):
        mapping = compliance_agent(_state())["evidence_compliance_validation"].compliance_mappings[0]
    assert mapping.evidence_references == ["EVID-COMP-001"]


def test_compliance_node_delegates_and_preserves_upstream_state_contract() -> None:
    state = _state()
    with _patch(_response()):
        result = compliance_node(state.model_dump(mode="json"))
    assert result["current_stage"] == CurrentStage.COMPLIANCE
    assert result["evidence_compliance_validation"].status == AgentStatus.COMPLETED
    assert state.context_intelligence is not None
    assert state.investigation_reasoning is not None


def test_prompt_exposes_actual_document_metadata() -> None:
    prompt = _build_prompt(_state())
    assert "DOC-COMP-001" in prompt
    assert "BANK_STATEMENT" in prompt
    assert "TXN-COMP-001" in prompt
