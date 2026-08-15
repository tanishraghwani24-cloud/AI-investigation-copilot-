"""Tests for the Reasoning Agent structured output (Mayur — Round 3).

All tests mock ``GeminiClient.generate()`` — no real Gemini API key
is required.

Covers:
- TEST 1 — MULTIPLE HYPOTHESES
- TEST 2 — VALID SCHEMA
- TEST 3 — SUPPORTING EVIDENCE
- TEST 4 — CONTRADICTING EVIDENCE
- TEST 5 — VALID CONFIDENCE
- TEST 6 — DISTINCT HYPOTHESES
- TEST 7 — ACTUAL CONTEXT IS SENT TO GEMINI
- TEST 8 — GEMINI STRUCTURED OUTPUT IS USED
- TEST 9 — NO FABRICATED FALLBACK
- TEST 10 — GRAPH INTEGRATION
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.agents.reasoning_agent import reasoning_agent, _build_prompt, HypothesesResponse
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
from app.services.gemini_client import GeminiClientError


# ── Fixtures ─────────────────────────────────────────────────────────


MOCK_HYPOTHESES_RESPONSE = HypothesesResponse(
    hypotheses=[
        Hypothesis(
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
        ),
        Hypothesis(
            hypothesis_id="HYP-GEMINI-002",
            title="Legitimate Business Operation",
            description=(
                "The transactions are part of normal business operations for a "
                "portfolio manager handling client funds."
            ),
            confidence=0.45,
            supporting_evidence=[
                "Customer occupation is Portfolio Manager",
            ],
            contradicting_evidence=[
                "Alert triggered by automated rule engine",
            ],
        )
    ]
)
"""Realistic competing hypotheses that the mocked Gemini will return."""


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


def _patch_gemini(return_value=None, side_effect=None):
    """Return a context-manager that patches get_gemini_client."""
    mock_client = MagicMock()
    if side_effect:
        mock_client.generate.side_effect = side_effect
    else:
        mock_client.generate.return_value = return_value or MOCK_HYPOTHESES_RESPONSE

    return patch(
        "app.agents.reasoning_agent.get_gemini_client",
        return_value=mock_client,
    )


# ── TEST 1: MULTIPLE HYPOTHESES ────────────────────────────────────────

def test_multiple_hypotheses_returned() -> None:
    """Verify reasoning agent returns at least 2 hypotheses."""
    state = _make_test_state()
    with _patch_gemini():
        result = reasoning_agent(state)
    hypotheses = result["investigation_reasoning"].hypotheses
    assert len(hypotheses) >= 2


# ── TEST 2: VALID SCHEMA ───────────────────────────────────────────────

def test_valid_schema() -> None:
    """Every returned hypothesis must conform to the existing Hypothesis schema/model."""
    state = _make_test_state()
    with _patch_gemini():
        result = reasoning_agent(state)
    hypotheses = result["investigation_reasoning"].hypotheses
    for hyp in hypotheses:
        assert isinstance(hyp, Hypothesis)
        assert hasattr(hyp, "hypothesis_id")
        assert hasattr(hyp, "title")
        assert hasattr(hyp, "description")


# ── TEST 3: SUPPORTING EVIDENCE ────────────────────────────────────────

def test_supporting_evidence_non_empty() -> None:
    """Every hypothesis must contain non-empty supporting evidence."""
    state = _make_test_state()
    with _patch_gemini():
        result = reasoning_agent(state)
    hypotheses = result["investigation_reasoning"].hypotheses
    for hyp in hypotheses:
        assert isinstance(hyp.supporting_evidence, list)
        assert len(hyp.supporting_evidence) > 0
        assert all(isinstance(ev, str) and ev for ev in hyp.supporting_evidence)


# ── TEST 4: CONTRADICTING EVIDENCE ─────────────────────────────────────

def test_contradicting_evidence_non_empty() -> None:
    """Every hypothesis must contain non-empty contradicting evidence."""
    state = _make_test_state()
    with _patch_gemini():
        result = reasoning_agent(state)
    hypotheses = result["investigation_reasoning"].hypotheses
    for hyp in hypotheses:
        assert isinstance(hyp.contradicting_evidence, list)
        assert len(hyp.contradicting_evidence) > 0
        assert all(isinstance(ev, str) and ev for ev in hyp.contradicting_evidence)


# ── TEST 5: VALID CONFIDENCE ───────────────────────────────────────────

def test_valid_confidence() -> None:
    """Every hypothesis must have a valid confidence value (0.0 to 1.0)."""
    state = _make_test_state()
    with _patch_gemini():
        result = reasoning_agent(state)
    hypotheses = result["investigation_reasoning"].hypotheses
    for hyp in hypotheses:
        assert isinstance(hyp.confidence, float)
        assert 0.0 <= hyp.confidence <= 1.0


# ── TEST 6: DISTINCT HYPOTHESES ────────────────────────────────────────

def test_distinct_hypotheses() -> None:
    """Verify the hypotheses are genuinely different."""
    state = _make_test_state()
    with _patch_gemini():
        result = reasoning_agent(state)
    hypotheses = result["investigation_reasoning"].hypotheses
    
    titles = set(h.title for h in hypotheses)
    assert len(titles) == len(hypotheses), "Hypothesis titles must be unique"
    
    descriptions = set(h.description for h in hypotheses)
    assert len(descriptions) == len(hypotheses), "Hypothesis descriptions must be unique"


# ── TEST 7: ACTUAL CONTEXT IS SENT TO GEMINI ───────────────────────────

def test_actual_context_sent_to_gemini() -> None:
    """Verify the prompt sent to Gemini contains relevant investigation information."""
    state = _make_test_state()
    with _patch_gemini() as mock_factory:
        reasoning_agent(state)
        mock_client = mock_factory.return_value
        call_args = mock_client.generate.call_args
        prompt_arg = call_args.args[0] if call_args.args else call_args.kwargs.get("prompt")
        
        # Verify specific case input and context intelligence are in the prompt
        assert "TXN-TEST-001" in prompt_arg
        assert "Test Customer" in prompt_arg
        assert "Suspicious wire transfer pattern detected" in prompt_arg
        assert "15000" in prompt_arg or "15000.0" in prompt_arg
        assert "under investigation" in prompt_arg
        assert "0.45" in prompt_arg


# ── TEST 8: GEMINI STRUCTURED OUTPUT IS USED ───────────────────────────

def test_gemini_structured_output_is_used() -> None:
    """Verify the expected hypotheses structure is returned and used."""
    state = _make_test_state()
    with _patch_gemini(return_value=MOCK_HYPOTHESES_RESPONSE):
        result = reasoning_agent(state)
    
    hypotheses = result["investigation_reasoning"].hypotheses
    assert len(hypotheses) == 2
    assert hypotheses[0].title == "Suspected Structuring Activity"
    assert hypotheses[1].title == "Legitimate Business Operation"


# ── TEST 9: NO FABRICATED FALLBACK ─────────────────────────────────────

def test_no_fabricated_fallback_on_error() -> None:
    """If Gemini fails, do not silently return fake placeholder hypotheses."""
    state = _make_test_state()
    
    with _patch_gemini(side_effect=GeminiClientError("Simulated API Error")):
        with pytest.raises(GeminiClientError):
            reasoning_agent(state)


# ── TEST 10: GRAPH INTEGRATION ─────────────────────────────────────────

def test_graph_integration_reasoning_node() -> None:
    """Run the investigation graph with the updated reasoning node."""
    state = _make_test_state()
    state_dict = state.model_dump(mode="json")
    
    with _patch_gemini():
        result = reasoning_node(state_dict)
        
    assert result["current_stage"] == CurrentStage.REASONING
    assert "investigation_reasoning" in result
    reasoning = result["investigation_reasoning"]
    assert len(reasoning.hypotheses) >= 2
    
    # Verify state preservation
    assert "case_id" not in result
    assert "case_input" not in result
