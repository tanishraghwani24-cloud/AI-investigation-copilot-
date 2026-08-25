"""Live Ollama reasoning-agent integration tests for fraud scenarios.

These tests hit a real Ollama server and take ~20+ minutes in total.
They are excluded from the default pytest suite and must be invoked
explicitly with:

    python -m pytest -m ollama_integration -v

Marker registration and default exclusion live in backend/pytest.ini.
"""
import pytest
from datetime import datetime, timezone

from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    Transaction,
    InvestigationState,
    CurrentStage,
)
from app.agents.reasoning_agent import reasoning_agent

# ---------------------------------------------------------------------------
# Module-level marker: every test in this file is an Ollama integration test.
# ---------------------------------------------------------------------------
pytestmark = pytest.mark.ollama_integration


@pytest.fixture(autouse=True)
def force_ollama_provider(monkeypatch):
    """Force the reasoning agent to use Ollama for all tests in this module.

    Uses monkeypatch so the override is automatically reverted after each
    test — global application settings are never permanently modified.
    """
    import sys
    from app.services.ollama_client import OllamaClient
    from app.core.config import settings
    import app.agents.reasoning_agent

    def fake_get_reasoning_client():
        return OllamaClient(
            base_url=settings.OLLAMA_BASE_URL,
            model_name=settings.OLLAMA_MODEL,
            timeout_seconds=300.0,
            max_retries=1,
            keep_alive="5m",
            options={"temperature": 0.0},
        )

    monkeypatch.setattr(
        sys.modules["app.agents.reasoning_agent"],
        "get_reasoning_client",
        fake_get_reasoning_client,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(case_id: str, case_input: CaseInput) -> InvestigationState:
    now = datetime.now(timezone.utc)
    return InvestigationState(
        case_id=case_id,
        case_input=case_input,
        current_stage=CurrentStage.REASONING,
        created_at=now,
        updated_at=now,
    )


def _grounded_terms(case_input: CaseInput) -> set[str]:
    """Collect lowercased terms that are grounded in the supplied case data.

    A forbidden term that appears in the alert_reason or transaction fields
    is considered *grounded* and should not trigger a hallucination failure.
    """
    fragments: list[str] = []
    if case_input.alert_reason:
        fragments.append(case_input.alert_reason)
    for tx in case_input.transactions:
        if tx.description:
            fragments.append(tx.description)
        if tx.transaction_type:
            fragments.append(tx.transaction_type)
    return {f.lower() for f in " ".join(fragments).split()}


_FORBIDDEN_TERMS = [
    "biometric", "face", "facial",
    "history", "past behavior", "previous transaction", "historical",
    "profile", "demographic", "kyc",
    "document", "passport", "id card", "invoice",
    "alert", "risk indicator",
    "channel", "mobile", "web", "ip address", "device",
]


def _assert_no_forbidden_terms(hypothesis, case_input: CaseInput):
    """Verify that a hypothesis does not hallucinate forbidden data categories.

    Checks:
      - title
      - description (factual portion — text before the first "recommend")
      - supporting_evidence
      - contradicting_evidence

    A forbidden term is *exempt* only when it literally appears in the
    supplied case input (alert_reason / transaction text), meaning it is
    grounded rather than hallucinated.

    Recommendation / action text may legitimately discuss information that
    should be verified, so only the pre-"recommend" portion of the
    description is checked.
    """
    grounded = _grounded_terms(case_input)

    # Collect the full text of the case input for substring grounding checks
    case_text_fragments: list[str] = []
    if case_input.alert_reason:
        case_text_fragments.append(case_input.alert_reason.lower())
    for tx in case_input.transactions:
        if tx.description:
            case_text_fragments.append(tx.description.lower())
    case_full_lower = " ".join(case_text_fragments)

    # Build the text to inspect (factual claims only).
    desc_factual = hypothesis.description.lower().split("recommend")[0]
    evidence_text = (
        " ".join(hypothesis.supporting_evidence).lower()
        + " "
        + " ".join(hypothesis.contradicting_evidence).lower()
    )
    text_to_check = (
        hypothesis.title.lower()
        + " " + desc_factual
        + " " + evidence_text
    )

    for term in _FORBIDDEN_TERMS:
        if term in text_to_check:
            # Exempt if the term (or the multi-word phrase) is grounded.
            term_words = set(term.split())
            if term_words.issubset(grounded):
                continue
            # Also check substring presence in the full case input text.
            if term in case_full_lower:
                continue
            raise AssertionError(
                f"Hallucinated forbidden term '{term}' in hypothesis "
                f"'{hypothesis.hypothesis_id}': {text_to_check[:200]}..."
            )


# ---------------------------------------------------------------------------
# 1. Normal / low-risk transaction
# ---------------------------------------------------------------------------
def test_reasoning_agent_normal_transaction():
    tx = Transaction(
        transaction_id="TX-50-USD", amount=50.0, currency="USD",
        timestamp=datetime.now(timezone.utc), sender_account="ACC-SENDER",
        receiver_account="ACC-RECV", transaction_type="P2P",
        description="Dinner split",
    )
    case_input = CaseInput(
        transactions=[tx],
        alert_reason="Random sample. No other information is available.",
    )
    state = _make_state("CASE-NORMAL-01", case_input)

    result_state = reasoning_agent(state)
    reasoning = result_state["investigation_reasoning"]

    assert reasoning.status == AgentStatus.COMPLETED
    assert len(reasoning.hypotheses) >= 2

    for h in reasoning.hypotheses:
        assert h.confidence <= 0.5, (
            f"Sparse-evidence confidence cap violated: {h.confidence}"
        )
        _assert_no_forbidden_terms(h, case_input)


# ---------------------------------------------------------------------------
# 2. Known amount anomaly
# ---------------------------------------------------------------------------
def test_reasoning_agent_amount_anomaly():
    tx = Transaction(
        transaction_id="TX-ANOM-01", amount=950.0, currency="USD",
        timestamp=datetime.now(timezone.utc), sender_account="ACC-SENDER",
        receiver_account="ACC-RECV", transaction_type="WIRE",
        description="Payment",
    )
    case_input = CaseInput(
        transactions=[tx],
        alert_reason=(
            "Account ACC-SENDER normally transfers less than 100. "
            "This is 950. No other information is available."
        ),
    )
    state = _make_state("CASE-ANOMALY-01", case_input)

    result_state = reasoning_agent(state)
    reasoning = result_state["investigation_reasoning"]

    assert reasoning.status == AgentStatus.COMPLETED
    assert len(reasoning.hypotheses) >= 2

    all_text = " ".join(
        h.title + " " + h.description for h in reasoning.hypotheses
    ).lower()

    # Verify supplied facts are actually used in the reasoning.
    assert "950" in all_text, "Supplied amount 950 not referenced"
    assert "100" in all_text, "Supplied baseline 100 not referenced"
    assert "acc-sender" in all_text, "Supplied sender account not referenced"

    for h in reasoning.hypotheses:
        _assert_no_forbidden_terms(h, case_input)


# ---------------------------------------------------------------------------
# 3. Sparse case
# ---------------------------------------------------------------------------
def test_reasoning_agent_sparse_case():
    tx = Transaction(
        transaction_id="TX-SPARSE-01", amount=1500.0, currency="USD",
        timestamp=datetime.now(timezone.utc), sender_account="ACC-UNK-SENDER",
        receiver_account="ACC-UNK-RECV", transaction_type="WIRE",
    )
    case_input = CaseInput(
        transactions=[tx],
        alert_reason="Threshold rule triggered. No other information is available.",
    )
    state = _make_state("CASE-SPARSE-01", case_input)

    result_state = reasoning_agent(state)
    reasoning = result_state["investigation_reasoning"]

    assert reasoning.status == AgentStatus.COMPLETED
    assert len(reasoning.hypotheses) >= 2

    for h in reasoning.hypotheses:
        assert h.confidence <= 0.5, (
            f"Sparse-evidence confidence cap violated: {h.confidence}"
        )
        _assert_no_forbidden_terms(h, case_input)


# ---------------------------------------------------------------------------
# 4. Multiple supplied transactions
# ---------------------------------------------------------------------------
def test_reasoning_agent_multiple_transactions():
    t1 = Transaction(
        transaction_id="TX-MULTI-01", amount=10.0, currency="USD",
        timestamp=datetime.now(timezone.utc), sender_account="ACC-S",
        receiver_account="ACC-R", transaction_type="CARD",
    )
    t2 = Transaction(
        transaction_id="TX-MULTI-02", amount=10.0, currency="USD",
        timestamp=datetime.now(timezone.utc), sender_account="ACC-S",
        receiver_account="ACC-R", transaction_type="CARD",
    )
    t3 = Transaction(
        transaction_id="TX-MULTI-03", amount=4999.0, currency="USD",
        timestamp=datetime.now(timezone.utc), sender_account="ACC-S",
        receiver_account="ACC-R", transaction_type="CARD",
    )
    case_input = CaseInput(
        transactions=[t1, t2, t3],
        alert_reason="Structuring suspected. No other information is available.",
    )
    state = _make_state("CASE-MULTI-01", case_input)

    result_state = reasoning_agent(state)
    reasoning = result_state["investigation_reasoning"]

    assert reasoning.status == AgentStatus.COMPLETED
    assert len(reasoning.hypotheses) >= 2

    all_text = " ".join(
        h.title + " " + h.description for h in reasoning.hypotheses
    ).lower()

    # Verify at least one supplied identifier or amount made it into reasoning.
    assert any(
        x in all_text
        for x in ["tx-multi-01", "tx-multi-02", "tx-multi-03", "4999"]
    ), "None of the supplied transaction IDs or the key amount 4999 appeared"

    for h in reasoning.hypotheses:
        _assert_no_forbidden_terms(h, case_input)


# ---------------------------------------------------------------------------
# 5. Missing optional data
# ---------------------------------------------------------------------------
def test_reasoning_agent_missing_optional_data():
    tx = Transaction(
        transaction_id="TX-MINIMAL-01", amount=100.0, currency="USD",
        timestamp=datetime.now(timezone.utc), sender_account="ACC-S",
        receiver_account="ACC-R", transaction_type="WIRE",
    )
    case_input = CaseInput(transactions=[tx])
    state = _make_state("CASE-MISSING-01", case_input)

    result_state = reasoning_agent(state)
    reasoning = result_state["investigation_reasoning"]

    assert reasoning.status == AgentStatus.COMPLETED
    assert len(reasoning.hypotheses) >= 2

    for h in reasoning.hypotheses:
        _assert_no_forbidden_terms(h, case_input)


# ---------------------------------------------------------------------------
# 6. Competing hypotheses
# ---------------------------------------------------------------------------
def test_reasoning_agent_competing_hypotheses():
    tx = Transaction(
        transaction_id="TX-AMBIG-01", amount=2500.0, currency="USD",
        timestamp=datetime.now(timezone.utc), sender_account="ACC-S",
        receiver_account="ACC-R", transaction_type="WIRE",
    )
    case_input = CaseInput(
        transactions=[tx],
        alert_reason=(
            "Transaction is large but to a known vendor. "
            "No other information is available."
        ),
    )
    state = _make_state("CASE-AMBIG-01", case_input)

    result_state = reasoning_agent(state)
    reasoning = result_state["investigation_reasoning"]

    assert reasoning.status == AgentStatus.COMPLETED
    assert len(reasoning.hypotheses) >= 2

    for h in reasoning.hypotheses:
        _assert_no_forbidden_terms(h, case_input)


# ---------------------------------------------------------------------------
# 7. Grounding against invented evidence — safety contract
# ---------------------------------------------------------------------------
def test_reasoning_agent_grounding_safety_contract():
    """Verify the grounding safety contract with a minimal, temptation-prone case.

    The case provides ONLY a high-value transaction with no alert_reason,
    maximising the temptation for a small model to hallucinate context.

    Safety contract:
      - COMPLETED  => every hypothesis must be grounded (no forbidden terms
                       in title, description, supporting/contradicting evidence)
                       and confidence must respect the sparse-evidence cap.
      - FAILED     => must be the *specific* structured-output / grounding
                       failure produced by the reasoning agent's retry logic,
                       not an arbitrary crash.  The sentinel text
                       "Unable to validate structured reasoning output"
                       must appear in reasoning_summary.
    """
    tx = Transaction(
        transaction_id="TX-CLEAN-01", amount=9999.0, currency="USD",
        timestamp=datetime.now(timezone.utc), sender_account="ACC-S",
        receiver_account="ACC-R", transaction_type="WIRE",
    )
    case_input = CaseInput(transactions=[tx])
    state = _make_state("CASE-CLEAN-01", case_input)

    result_state = reasoning_agent(state)
    reasoning = result_state["investigation_reasoning"]

    if reasoning.status == AgentStatus.COMPLETED:
        # --- COMPLETED path: full grounding verification ---
        assert len(reasoning.hypotheses) >= 2, (
            "Production contract requires at least 2 hypotheses"
        )
        for h in reasoning.hypotheses:
            assert h.confidence <= 0.5, (
                f"Sparse-evidence confidence cap violated: {h.confidence}"
            )
            _assert_no_forbidden_terms(h, case_input)

    elif reasoning.status == AgentStatus.FAILED:
        # --- FAILED path: must be the expected grounding / parse failure ---
        assert reasoning.reasoning_summary is not None, (
            "FAILED status must include a reasoning_summary"
        )
        assert "Unable to validate structured reasoning output" in reasoning.reasoning_summary, (
            f"Unexpected failure reason: {reasoning.reasoning_summary}"
        )
        # Verify the failure is represented safely — no hypotheses leaked.
        assert len(reasoning.hypotheses) == 0, (
            "FAILED status must not leak unvalidated hypotheses"
        )

    else:
        pytest.fail(
            f"Unexpected status {reasoning.status}; expected COMPLETED or FAILED"
        )


# ---------------------------------------------------------------------------
# 8. Known fact vs. recommendation
# ---------------------------------------------------------------------------
def test_reasoning_agent_known_fact_vs_recommendation():
    tx = Transaction(
        transaction_id="TX-REC-01", amount=5000.0, currency="USD",
        timestamp=datetime.now(timezone.utc), sender_account="ACC-S",
        receiver_account="ACC-R", transaction_type="WIRE",
    )
    case_input = CaseInput(
        transactions=[tx],
        alert_reason="High risk transaction. Missing customer information.",
    )
    state = _make_state("CASE-REC-01", case_input)

    result_state = reasoning_agent(state)
    reasoning = result_state["investigation_reasoning"]

    assert reasoning.status == AgentStatus.COMPLETED
    assert len(reasoning.hypotheses) >= 2

    # Verify the agent produces actionable recommendations.
    assert len(reasoning.recommended_actions) >= 1, (
        "Expected at least one recommended action"
    )

    # Verify no hallucinated factual evidence in hypotheses.
    for h in reasoning.hypotheses:
        _assert_no_forbidden_terms(h, case_input)
