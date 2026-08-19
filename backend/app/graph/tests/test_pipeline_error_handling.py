"""Test: Pipeline error handling — Round 3 Tanish.

Comprehensive tests verifying that graph-level node failures:
  1. Do NOT crash the graph invocation.
  2. Record an AgentError identifying the failed node.
  3. Mark the investigation as FAILED at the correct stage.
  4. Preserve all successful upstream agent outputs.
  5. Prevent downstream nodes from executing.
  6. Persist partial state (with failure info) to the database.

Failure is tested at EVERY node position:
  - Context, Reasoning, Compliance, Decision, Reporting.

Uses an in-memory SQLite database (via aiosqlite). The reasoning
agent's Gemini call is mocked to return a deterministic hypothesis.

For nodes that delegate to agents (context, reasoning, decision),
the agent function is patched to raise. For inline nodes (compliance,
reporting), a custom graph is built with a failing node function.
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from langgraph.graph import END, START, StateGraph
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.agents.reasoning_agent import HypothesesResponse
from app.db.session import Base
from app.graph.builder import (
    COMPLIANCE,
    CONTEXT,
    DECISION,
    REASONING,
    REPORTING,
)
from app.graph.nodes import (
    compliance_node,
    context_node,
    decision_node,
    reasoning_node,
    reporting_node,
)
from app.graph.workflow import run_investigation_with_persistence
from app.models.investigation import InvestigationCase
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    CurrentStage,
    CustomerProfile,
    DecisionAction,
    DecisionOption,
    Hypothesis,
    InvestigationState,
    SeverityLevel,
    Transaction,
    create_initial_state,
)


# ── Mock data ────────────────────────────────────────────────────────

MOCK_HYPOTHESIS = Hypothesis(
    hypothesis_id="HYP-ERR-TEST-001",
    title="Suspected Layering Activity",
    description="Test hypothesis for error handling tests.",
    confidence=0.78,
    supporting_evidence=["Evidence 1"],
    contradicting_evidence=["Counter-evidence 1"],
)

MOCK_HYPOTHESES_RESPONSE = HypothesesResponse(hypotheses=[MOCK_HYPOTHESIS])


# ── Graph builder helpers ────────────────────────────────────────────


def _build_graph_with_failing_node(failing_node_name: str, error_msg: str):
    """Build a compiled graph identical to the main one, but with one
    node replaced by a function that raises RuntimeError.

    All other nodes are the real implementations.
    """
    node_map = {
        CONTEXT: context_node,
        REASONING: reasoning_node,
        COMPLIANCE: compliance_node,
        DECISION: decision_node,
        REPORTING: reporting_node,
    }

    def _failing_node(state: Any) -> dict:
        raise RuntimeError(error_msg)

    node_map[failing_node_name] = _failing_node

    graph = StateGraph(InvestigationState)
    for name, func in node_map.items():
        graph.add_node(name, func)

    graph.add_edge(START, CONTEXT)
    graph.add_edge(CONTEXT, REASONING)
    graph.add_edge(REASONING, COMPLIANCE)
    graph.add_edge(COMPLIANCE, DECISION)
    graph.add_edge(DECISION, REPORTING)
    graph.add_edge(REPORTING, END)

    return graph.compile()


# ── Fixtures ─────────────────────────────────────────────────────────


def _build_test_state(case_id: str = "CASE-ERR-001") -> InvestigationState:
    """Create a minimal realistic InvestigationState for testing."""
    from app.schemas.investigation_state import (
        BeneficiaryInfo,
        DeviceInfo,
        MerchantInfo,
    )

    transaction = Transaction(
        transaction_id="TXN-ERR-001",
        amount=48_500.00,
        currency="USD",
        timestamp=datetime(2025, 8, 19, 14, 32, 11),
        sender_account="ACC-US-ERR-001",
        receiver_account="ACC-KY-ERR-002",
        transaction_type="WIRE",
        channel="ONLINE",
        description="Test error handling deposit",
        location="New York, US",
    )

    customer = CustomerProfile(
        customer_id="CUST-ERR-001",
        name="Error Test User",
        email="err@test.com",
        risk_rating="MEDIUM",
        occupation="Portfolio Manager",
        nationality="US",
    )

    merchant = MerchantInfo(
        merchant_id="MERCH-ERR-001",
        name="TestVault Ltd.",
        category="Cryptocurrency Exchange",
        country="KY",
        risk_level=SeverityLevel.HIGH,
    )

    device = DeviceInfo(
        device_id="DEV-ERR-001",
        device_type="MOBILE",
        ip_address="185.220.101.99",
        geolocation="Bucharest, Romania",
        is_known_device=False,
    )

    beneficiary = BeneficiaryInfo(
        beneficiary_id="BEN-ERR-001",
        name="TestVault Ltd.",
        account_number="ACC-KY-ERR-002",
        bank_name="Test Bank",
        country="KY",
        is_new=True,
    )

    case_input = CaseInput(
        transactions=[transaction],
        customer_profile=customer,
        merchant_info=merchant,
        device_info=device,
        beneficiary_info=beneficiary,
        alert_reason="Error handling test case",
    )

    return create_initial_state(case_id=case_id, case_input=case_input)


@pytest_asyncio.fixture
async def db_session():
    """Provide an async SQLite in-memory session with all tables created."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def mock_gemini():
    """Patch the reasoning client factory and decision Gemini client.

    The google-genai SDK raises ValueError when api_key is empty, so we
    must mock the client factories (not just ``generate``) to prevent
    the constructors from reaching the real SDK.

    Both reasoning and decision agents use Gemini. The mock uses
    side_effect to return the appropriate response based on the
    response_schema argument.
    """
    from app.agents.decision_agent import _DecisionOptionsResponse

    mock_decision_options = _DecisionOptionsResponse(
        options=[
            DecisionOption(
                option_id="OPT-ALLOW",
                action=DecisionAction.ALLOW,
                rationale="Test allow rationale",
                confidence=0.20,
                risk_score=0.78,
                pros=["p1", "p2"], cons=["c1", "c2"], risks=["r1", "r2"], mitigation=["m1", "m2"],
            ),
            DecisionOption(
                option_id="OPT-HOLD",
                action=DecisionAction.HOLD,
                rationale="Test hold rationale",
                confidence=0.65,
                risk_score=0.40,
                pros=["p1", "p2"], cons=["c1", "c2"], risks=["r1", "r2"], mitigation=["m1", "m2"],
            ),
            DecisionOption(
                option_id="OPT-BLOCK",
                action=DecisionAction.BLOCK,
                rationale="Test block rationale",
                confidence=0.35,
                risk_score=0.15,
                pros=["p1", "p2"], cons=["c1", "c2"], risks=["r1", "r2"], mitigation=["m1", "m2"],
            ),
            DecisionOption(
                option_id="OPT-ESCALATE",
                action=DecisionAction.ESCALATE,
                rationale="Test escalate rationale",
                confidence=0.50,
                risk_score=0.30,
                pros=["p1", "p2"], cons=["c1", "c2"], risks=["r1", "r2"], mitigation=["m1", "m2"],
            ),
        ],
        recommended_decision=DecisionAction.HOLD,
        decision_rationale="Test rationale",
    )

    def _side_effect(prompt, response_schema=None):
        if response_schema is not None:
            name = response_schema.__name__
            if name == "HypothesesResponse":
                return MOCK_HYPOTHESES_RESPONSE
            if name == "_DecisionOptionsResponse":
                return mock_decision_options
        return "Mock text response"

    mock_client = MagicMock()
    mock_client.generate.side_effect = _side_effect

    with patch(
        "app.agents.reasoning_agent.get_reasoning_client",
        return_value=mock_client,
    ), patch(
        "app.agents.decision_agent.get_gemini_client",
        return_value=mock_client,
    ):
        yield mock_client



# ── Helper ───────────────────────────────────────────────────────────


async def _get_db_state(session: AsyncSession, case_id: str) -> dict | None:
    """Retrieve the state_json from the DB for the given case."""
    stmt = select(InvestigationCase).where(
        InvestigationCase.case_id == case_id
    )
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()
    if record is None:
        return None
    return record.state_json


# ══════════════════════════════════════════════════════════════════════
# Test 1 — Successful pipeline
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_successful_pipeline(db_session, mock_gemini):
    """All nodes succeed — state is valid, not FAILED, no errors."""
    state = _build_test_state("CASE-SUCCESS-001")
    result = await run_investigation_with_persistence(state, db_session)

    assert isinstance(result, InvestigationState)
    assert result.current_stage == CurrentStage.DONE
    assert result.errors == []
    assert result.context_intelligence is not None
    assert result.investigation_reasoning is not None
    assert result.evidence_compliance_validation is not None
    assert result.decision_optimization is not None
    assert result.investigation_report is not None


# ══════════════════════════════════════════════════════════════════════
# Test 2 — Context failure
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_context_failure(db_session, mock_gemini):
    """Context node fails — no downstream output, state has error."""
    state = _build_test_state("CASE-CTX-FAIL")

    failing_graph = _build_graph_with_failing_node(
        CONTEXT, "Context agent exploded",
    )

    with patch("app.graph.workflow._investigation_graph", failing_graph):
        result = await run_investigation_with_persistence(state, db_session)

    # No unhandled exception — returned cleanly
    assert isinstance(result, InvestigationState)

    # AgentError recorded, identifies context
    assert len(result.errors) >= 1
    assert result.errors[0].agent_name == "context"
    assert "Context agent exploded" in result.errors[0].message

    # Context output not produced
    assert result.context_intelligence is None

    # No downstream outputs produced
    assert result.investigation_reasoning is None
    assert result.evidence_compliance_validation is None
    assert result.decision_optimization is None
    assert result.investigation_report is None


# ══════════════════════════════════════════════════════════════════════
# Test 3 — Reasoning failure
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_reasoning_failure(db_session, mock_gemini):
    """Reasoning node fails — Context output preserved."""
    state = _build_test_state("CASE-RSN-FAIL")

    failing_graph = _build_graph_with_failing_node(
        REASONING, "Reasoning agent exploded",
    )

    with patch("app.graph.workflow._investigation_graph", failing_graph):
        result = await run_investigation_with_persistence(state, db_session)

    assert isinstance(result, InvestigationState)

    # AgentError identifies reasoning
    assert len(result.errors) >= 1
    assert result.errors[0].agent_name == "reasoning"

    # Context output preserved
    assert result.context_intelligence is not None

    # Reasoning and downstream not produced
    assert result.investigation_reasoning is None
    assert result.evidence_compliance_validation is None
    assert result.decision_optimization is None
    assert result.investigation_report is None


# ══════════════════════════════════════════════════════════════════════
# Test 4 — Compliance failure
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_compliance_failure(db_session, mock_gemini):
    """Compliance node fails — Context + Reasoning output preserved."""
    state = _build_test_state("CASE-CMP-FAIL")

    failing_graph = _build_graph_with_failing_node(
        COMPLIANCE, "Compliance node exploded",
    )

    with patch("app.graph.workflow._investigation_graph", failing_graph):
        result = await run_investigation_with_persistence(state, db_session)

    assert isinstance(result, InvestigationState)

    # AgentError identifies compliance
    assert len(result.errors) >= 1
    assert result.errors[0].agent_name == "compliance"

    # Upstream preserved
    assert result.context_intelligence is not None
    assert result.investigation_reasoning is not None

    # Compliance and downstream not produced
    assert result.evidence_compliance_validation is None
    assert result.decision_optimization is None
    assert result.investigation_report is None


# ══════════════════════════════════════════════════════════════════════
# Test 5 — Decision failure
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_decision_failure(db_session, mock_gemini):
    """Decision node fails — Context + Reasoning + Compliance preserved."""
    state = _build_test_state("CASE-DEC-FAIL")

    failing_graph = _build_graph_with_failing_node(
        DECISION, "Decision agent exploded",
    )

    with patch("app.graph.workflow._investigation_graph", failing_graph):
        result = await run_investigation_with_persistence(state, db_session)

    assert isinstance(result, InvestigationState)

    # AgentError identifies decision
    assert len(result.errors) >= 1
    assert result.errors[0].agent_name == "decision"

    # Upstream preserved
    assert result.context_intelligence is not None
    assert result.investigation_reasoning is not None
    assert result.evidence_compliance_validation is not None

    # Decision and downstream not produced
    assert result.decision_optimization is None
    assert result.investigation_report is None


# ══════════════════════════════════════════════════════════════════════
# Test 6 — Reporting failure
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_reporting_failure(db_session, mock_gemini):
    """Reporting node fails — all previous outputs preserved."""
    state = _build_test_state("CASE-RPT-FAIL")

    failing_graph = _build_graph_with_failing_node(
        REPORTING, "Reporting node exploded",
    )

    with patch("app.graph.workflow._investigation_graph", failing_graph):
        result = await run_investigation_with_persistence(state, db_session)

    assert isinstance(result, InvestigationState)

    # AgentError identifies reporting
    assert len(result.errors) >= 1
    assert result.errors[0].agent_name == "reporting"

    # All upstream preserved
    assert result.context_intelligence is not None
    assert result.investigation_reasoning is not None
    assert result.evidence_compliance_validation is not None
    assert result.decision_optimization is not None

    # Reporting not produced
    assert result.investigation_report is None


# ══════════════════════════════════════════════════════════════════════
# Test 7 — Partial state persistence
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_partial_state_persisted(db_session, mock_gemini):
    """Failed state in DB still contains successful upstream output."""
    state = _build_test_state("CASE-PARTIAL-001")

    failing_graph = _build_graph_with_failing_node(
        COMPLIANCE, "Compliance persistence test",
    )

    with patch("app.graph.workflow._investigation_graph", failing_graph):
        await run_investigation_with_persistence(state, db_session)

    # Query the DB directly
    db_state = await _get_db_state(db_session, "CASE-PARTIAL-001")
    assert db_state is not None

    # Successful upstream outputs are present in the persisted state
    assert db_state.get("context_intelligence") is not None
    assert db_state.get("investigation_reasoning") is not None

    # Failed node output is absent
    assert db_state.get("evidence_compliance_validation") is None

    # Downstream outputs are absent
    assert db_state.get("decision_optimization") is None
    assert db_state.get("investigation_report") is None

    # Error is recorded
    errors = db_state.get("errors", [])
    assert len(errors) >= 1
    assert errors[0]["agent_name"] == "compliance"

    # Stage reflects failure
    assert db_state.get("current_stage") in (
        CurrentStage.COMPLIANCE.value,
        "COMPLIANCE",
    )


# ══════════════════════════════════════════════════════════════════════
# Test 8 — Downstream stop guarantee
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_downstream_nodes_not_called_after_failure(db_session, mock_gemini):
    """When reasoning fails, compliance/decision/reporting are NOT called."""
    state = _build_test_state("CASE-STOP-001")

    # Track which nodes actually execute
    call_tracker: dict[str, int] = {
        CONTEXT: 0,
        REASONING: 0,
        COMPLIANCE: 0,
        DECISION: 0,
        REPORTING: 0,
    }

    def _tracking_context(st: Any) -> dict:
        call_tracker[CONTEXT] += 1
        return context_node(st)

    def _failing_reasoning(st: Any) -> dict:
        call_tracker[REASONING] += 1
        raise RuntimeError("Reasoning failed — stop test")

    def _tracking_compliance(st: Any) -> dict:
        call_tracker[COMPLIANCE] += 1
        return compliance_node(st)

    def _tracking_decision(st: Any) -> dict:
        call_tracker[DECISION] += 1
        return decision_node(st)

    def _tracking_reporting(st: Any) -> dict:
        call_tracker[REPORTING] += 1
        return reporting_node(st)

    graph = StateGraph(InvestigationState)
    graph.add_node(CONTEXT, _tracking_context)
    graph.add_node(REASONING, _failing_reasoning)
    graph.add_node(COMPLIANCE, _tracking_compliance)
    graph.add_node(DECISION, _tracking_decision)
    graph.add_node(REPORTING, _tracking_reporting)

    graph.add_edge(START, CONTEXT)
    graph.add_edge(CONTEXT, REASONING)
    graph.add_edge(REASONING, COMPLIANCE)
    graph.add_edge(COMPLIANCE, DECISION)
    graph.add_edge(DECISION, REPORTING)
    graph.add_edge(REPORTING, END)

    custom_graph = graph.compile()

    with patch("app.graph.workflow._investigation_graph", custom_graph):
        result = await run_investigation_with_persistence(state, db_session)

    # Graph returned cleanly
    assert isinstance(result, InvestigationState)

    # Reasoning failed
    assert len(result.errors) >= 1
    assert result.errors[0].agent_name == "reasoning"

    # Verify call counts
    assert call_tracker[CONTEXT] == 1, "Context should have been called once"
    assert call_tracker[REASONING] == 1, "Reasoning should have been called once"
    assert call_tracker[COMPLIANCE] == 0, "Compliance should NOT have been called"
    assert call_tracker[DECISION] == 0, "Decision should NOT have been called"
    assert call_tracker[REPORTING] == 0, "Reporting should NOT have been called"

    # Context preserved, downstream absent
    assert result.context_intelligence is not None
    assert result.evidence_compliance_validation is None
    assert result.decision_optimization is None
    assert result.investigation_report is None
