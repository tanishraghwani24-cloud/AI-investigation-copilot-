"""Tests for strict compliance grounding constraints (Round 8)."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from app.agents.compliance_agent import _build_prompt, compliance_agent
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    ComplianceMapping,
    ContextIntelligence,
    CurrentStage,
    EvidenceComplianceValidation,
    SeverityLevel,
    Transaction,
    create_initial_state,
)


def _state():
    transaction = Transaction(
        transaction_id="TXN-MOCK-001-030", amount=59_900.0, currency="USD",
        timestamp=datetime(2026, 8, 1, 10), sender_account="ACC-MOCK-001",
        receiver_account="ACC-OFFSHORE-5", transaction_type="WIRE",
    )
    case_input = CaseInput(transactions=[transaction], alert_reason="Large wire")
    state = create_initial_state("CASE-MOCK--001", case_input)
    state.context_intelligence = ContextIntelligence(
        status=AgentStatus.COMPLETED, context_summary="Wire to offshore.",
    )
    return state


def test_prompt_enforces_strict_grounding_and_no_hallucination():
    """Verify the prompt contains the new strict grounding rules."""
    prompt = _build_prompt(_state())
    
    # Must explicitly forbid altering amounts and directions
    assert "STRICT EVIDENCE GROUNDING" in prompt
    assert "MUST NOT invent, alter, or hallucinate transaction amounts" in prompt
    
    # Must explicitly forbid assumed intent (structuring)
    assert "NO ASSUMED INTENT" in prompt
    assert "Do not claim intentional criminal/regulatory conduct (such as \"structuring\" or \"smurfing\")" in prompt
    
    # Must distinguish signals from violations
    assert "DISTINGUISH SIGNALS FROM VIOLATIONS" in prompt
    assert "A suspicious indicator or risk signal is NOT a confirmed violation." in prompt
    
    # Must enforce exact amounts
    assert "EXACT AMOUNTS AND DIRECTIONS" in prompt
    assert "Use the exact amounts and currencies provided" in prompt

    # Ensure the old hallucinatory example is completely removed
    assert "$9,900" not in prompt


def test_agent_accepts_properly_grounded_non_violation():
    """Verify that when the LLM correctly outputs is_violated=False for a signal, it passes through."""
    response = EvidenceComplianceValidation(
        status=AgentStatus.COMPLETED,
        compliance_mappings=[ComplianceMapping(
            regulation_id="AML-STRUCTURING",
            regulation_name="Structuring / Smurfing",
            description="The $59,900 wire transfer is large but there is insufficient evidence to establish intentional structuring to bypass reporting thresholds.",
            is_violated=False,
            severity=SeverityLevel.LOW,
            evidence_references=["TXN-MOCK-001-030"],
        )],
        evidence_gaps=["No documentation showing intent to evade thresholds."],
        validation_summary="No confirmed violations, but some signals present."
    )
    
    client = MagicMock()
    client.generate.return_value = response
    
    with patch("app.agents.compliance_agent.get_reasoning_client", return_value=client):
        result = compliance_agent(_state())
        
    validation = result["evidence_compliance_validation"]
    assert len(validation.compliance_mappings) == 1
    mapping = validation.compliance_mappings[0]
    
    # Assert the non-violation is preserved because it used real evidence
    assert mapping.is_violated is False
    assert mapping.evidence_references == ["TXN-MOCK-001-030"]
    assert "59,900" in mapping.description
