"""Test: Pipeline persistence — Round 2 Tanish.

Runs the full investigation graph on a fresh case with an attached
supporting document and asserts, via direct DB query, that:

1. The investigation case row exists with the correct case_id.
2. state_json is populated and reflects completed outputs from all
   5 pipeline stages (context, reasoning, compliance, decision,
   reporting).
3. status is "DONE".
4. A DocumentRecord for the attached document is correctly linked to
   the investigation's case_id.

Uses an in-memory SQLite database (via aiosqlite) so no running
Postgres instance is required.  The reasoning agent's Gemini call
is mocked to return a deterministic hypothesis.

Column type notes
-----------------
- ``state_json`` uses generic ``sqlalchemy.JSON`` (not JSONB) — works
  with SQLite.
- ``id`` columns use ``sqlalchemy.dialects.postgresql.UUID`` which
  SQLAlchemy renders as ``CHAR(32)`` on SQLite.  Python-side defaults
  (``uuid.uuid4``) always supply values, so the Postgres-specific
  ``server_default`` (``gen_random_uuid()``) is never evaluated.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select, event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.session import Base
from app.graph.workflow import run_investigation_with_persistence
from app.models.document import DocumentRecord
from app.models.investigation import InvestigationCase
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    CurrentStage,
    CustomerProfile,
    DecisionAction,
    DecisionOption,
    Hypothesis,
    SeverityLevel,
    SupportingDocument,
    Transaction,
    create_initial_state,
)
from app.agents.reasoning_agent import HypothesesResponse
from app.agents.decision_agent import _DecisionOptionsResponse


# ── Fixtures ─────────────────────────────────────────────────────────


MOCK_HYPOTHESIS = Hypothesis(
    hypothesis_id="HYP-PERSIST-001",
    title="Suspected Layering Activity",
    description=(
        "The customer may be layering funds through a series of rapid "
        "transactions to obscure the origin of $48,500 sent to a "
        "cryptocurrency exchange in the Cayman Islands."
    ),
    confidence=0.78,
    supporting_evidence=[
        "TXN-PERSIST-001: $48,500 wire to high-risk jurisdiction",
        "First-time beneficiary with no prior relationship",
    ],
    contradicting_evidence=[
        "Customer is a known Portfolio Manager with legitimate large-value activity",
    ],
)

MOCK_HYPOTHESES_RESPONSE = HypothesesResponse(hypotheses=[MOCK_HYPOTHESIS])
"""Deterministic hypothesis response returned by the mocked Gemini client."""


def _build_test_state() -> "InvestigationState":
    """Create a realistic InvestigationState with a supporting document."""
    from app.schemas.investigation_state import (
        BeneficiaryInfo,
        DeviceInfo,
        InvestigationState,
        MerchantInfo,
    )

    transaction = Transaction(
        transaction_id="TXN-PERSIST-001",
        amount=48_500.00,
        currency="USD",
        timestamp=datetime(2025, 8, 19, 14, 32, 11),
        sender_account="ACC-US-PERSIST-001",
        receiver_account="ACC-KY-PERSIST-002",
        transaction_type="WIRE",
        channel="ONLINE",
        description="Investment deposit — CryptoVault",
        location="New York, US",
    )

    customer = CustomerProfile(
        customer_id="CUST-PERSIST-001",
        name="Jane Doe",
        email="jane.doe@example.com",
        risk_rating="MEDIUM",
        occupation="Portfolio Manager",
        nationality="US",
    )

    merchant = MerchantInfo(
        merchant_id="MERCH-KY-PERSIST",
        name="CryptoVault Holdings Ltd.",
        category="Cryptocurrency Exchange",
        country="KY",
        risk_level=SeverityLevel.HIGH,
    )

    device = DeviceInfo(
        device_id="DEV-PERSIST-001",
        device_type="MOBILE",
        ip_address="185.220.101.99",
        geolocation="Bucharest, Romania",
        is_known_device=False,
    )

    beneficiary = BeneficiaryInfo(
        beneficiary_id="BEN-KY-PERSIST",
        name="CryptoVault Holdings Ltd.",
        account_number="ACC-KY-PERSIST-002",
        bank_name="Cayman National Bank",
        country="KY",
        is_new=True,
    )

    supporting_doc = SupportingDocument(
        document_id="DOC-PERSIST-001",
        document_type="BANK_STATEMENT",
        file_name="doe_aug2025_statement.pdf",
        uploaded_at=datetime(2025, 8, 19, 15, 0, 0),
        summary="Monthly statement showing irregular outbound transfers.",
        extracted_text="Account: 1234  Transfer: $48,500 to CryptoVault.",
    )

    case_input = CaseInput(
        transactions=[transaction],
        customer_profile=customer,
        merchant_info=merchant,
        device_info=device,
        beneficiary_info=beneficiary,
        supporting_documents=[supporting_doc],
        alert_reason=(
            "Large wire to first-time beneficiary in high-risk jurisdiction, "
            "unknown device with geolocation mismatch."
        ),
    )

    return create_initial_state(
        case_id="CASE-PERSIST-001",
        case_input=case_input,
    )


@pytest_asyncio.fixture
async def db_session():
    """Provide an async SQLite in-memory session with all tables created.

    SQLite needs ``check_same_thread=False`` for async usage, and we
    enable foreign key enforcement via a PRAGMA.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Enable FK enforcement on every raw connection
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
    """Patch reasoning and decision client factories so tests stay offline."""
    mock_decision_options = _DecisionOptionsResponse(
        options=[
            DecisionOption(
                option_id="OPT-ALLOW",
                action=DecisionAction.ALLOW,
                rationale="a",
                confidence=0.20,
                risk_score=0.78,
                pros=["p1", "p2"],
                cons=["c1", "c2"],
                risks=["r1", "r2"],
                mitigation=["m1", "m2"],
            ),
            DecisionOption(
                option_id="OPT-HOLD",
                action=DecisionAction.HOLD,
                rationale="h",
                confidence=0.65,
                risk_score=0.40,
                pros=["p1", "p2"],
                cons=["c1", "c2"],
                risks=["r1", "r2"],
                mitigation=["m1", "m2"],
            ),
            DecisionOption(
                option_id="OPT-BLOCK",
                action=DecisionAction.BLOCK,
                rationale="b",
                confidence=0.35,
                risk_score=0.15,
                pros=["p1", "p2"],
                cons=["c1", "c2"],
                risks=["r1", "r2"],
                mitigation=["m1", "m2"],
            ),
            DecisionOption(
                option_id="OPT-ESCALATE",
                action=DecisionAction.ESCALATE,
                rationale="e",
                confidence=0.50,
                risk_score=0.30,
                pros=["p1", "p2"],
                cons=["c1", "c2"],
                risks=["r1", "r2"],
                mitigation=["m1", "m2"],
            ),
        ],
        recommended_decision=DecisionAction.HOLD,
        decision_rationale="why hold",
    )

    def _side_effect(prompt, response_schema=None):
        if response_schema is not None:
            schema_name = response_schema.__name__
            if schema_name == "HypothesesResponse":
                return MOCK_HYPOTHESES_RESPONSE
            if schema_name == "_DecisionOptionsResponse":
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


# ── Tests ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_investigation_case_persisted(db_session, mock_gemini):
    """After a full graph run the investigation case row exists."""
    state = _build_test_state()
    await run_investigation_with_persistence(state, db_session)

    stmt = select(InvestigationCase).where(
        InvestigationCase.case_id == "CASE-PERSIST-001"
    )
    result = await db_session.execute(stmt)
    record = result.scalar_one_or_none()

    assert record is not None, "InvestigationCase row should exist"
    assert record.case_id == "CASE-PERSIST-001"


@pytest.mark.asyncio
async def test_final_status_is_done(db_session, mock_gemini):
    """The case status should be DONE after the full pipeline."""
    state = _build_test_state()
    await run_investigation_with_persistence(state, db_session)

    stmt = select(InvestigationCase).where(
        InvestigationCase.case_id == "CASE-PERSIST-001"
    )
    result = await db_session.execute(stmt)
    record = result.scalar_one()

    assert record.status == "DONE"


@pytest.mark.asyncio
async def test_state_json_contains_all_agent_outputs(db_session, mock_gemini):
    """state_json should contain completed output from all 5 agents."""
    state = _build_test_state()
    await run_investigation_with_persistence(state, db_session)

    stmt = select(InvestigationCase).where(
        InvestigationCase.case_id == "CASE-PERSIST-001"
    )
    result = await db_session.execute(stmt)
    record = result.scalar_one()

    sj = record.state_json
    assert sj is not None, "state_json should not be None"

    # Context agent
    ci = sj.get("context_intelligence")
    assert ci is not None, "context_intelligence missing from state_json"
    assert ci["status"] == AgentStatus.COMPLETED.value

    # Reasoning agent
    ir = sj.get("investigation_reasoning")
    assert ir is not None, "investigation_reasoning missing from state_json"
    assert ir["status"] == AgentStatus.COMPLETED.value
    assert len(ir["hypotheses"]) >= 1

    # Compliance agent
    ecv = sj.get("evidence_compliance_validation")
    assert ecv is not None, "evidence_compliance_validation missing from state_json"
    assert ecv["status"] == AgentStatus.COMPLETED.value

    # Decision agent
    do = sj.get("decision_optimization")
    assert do is not None, "decision_optimization missing from state_json"
    assert do["status"] == AgentStatus.COMPLETED.value
    assert len(do["decision_options"]) == 4

    # Reporting agent
    rep = sj.get("investigation_report")
    assert rep is not None, "investigation_report missing from state_json"
    assert rep["status"] == AgentStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_document_record_linked_to_investigation(db_session, mock_gemini):
    """Supporting document row is linked to the investigation via case_id."""
    state = _build_test_state()
    await run_investigation_with_persistence(state, db_session)

    stmt = select(DocumentRecord).where(
        DocumentRecord.case_id == "CASE-PERSIST-001"
    )
    result = await db_session.execute(stmt)
    docs = list(result.scalars().all())

    assert len(docs) == 1, "Exactly one document should be linked"
    doc = docs[0]
    assert doc.document_id == "DOC-PERSIST-001"
    assert doc.document_type == "BANK_STATEMENT"
    assert doc.file_name == "doe_aug2025_statement.pdf"
    assert doc.case_id == "CASE-PERSIST-001"


@pytest.mark.asyncio
async def test_document_extracted_text_persisted(db_session, mock_gemini):
    """The document's extracted_text and summary are persisted."""
    state = _build_test_state()
    await run_investigation_with_persistence(state, db_session)

    stmt = select(DocumentRecord).where(
        DocumentRecord.document_id == "DOC-PERSIST-001"
    )
    result = await db_session.execute(stmt)
    doc = result.scalar_one()

    assert doc.extracted_text is not None
    assert "48,500" in doc.extracted_text
    assert doc.summary is not None
    assert "irregular" in doc.summary.lower()


@pytest.mark.asyncio
async def test_returned_state_matches_db(db_session, mock_gemini):
    """The InvestigationState returned matches what's in the DB."""
    state = _build_test_state()
    result_state = await run_investigation_with_persistence(state, db_session)

    assert result_state.current_stage == CurrentStage.DONE
    assert result_state.context_intelligence is not None
    assert result_state.investigation_reasoning is not None
    assert result_state.evidence_compliance_validation is not None
    assert result_state.decision_optimization is not None
    assert result_state.investigation_report is not None

    # Cross-check against DB
    stmt = select(InvestigationCase).where(
        InvestigationCase.case_id == "CASE-PERSIST-001"
    )
    db_result = await db_session.execute(stmt)
    record = db_result.scalar_one()

    assert record.state_json["current_stage"] == "DONE"
    assert record.state_json["case_id"] == result_state.case_id


@pytest.mark.asyncio
async def test_current_stage_reflects_final_stage(db_session, mock_gemini):
    """current_stage in state_json should be DONE after full run."""
    state = _build_test_state()
    await run_investigation_with_persistence(state, db_session)

    stmt = select(InvestigationCase).where(
        InvestigationCase.case_id == "CASE-PERSIST-001"
    )
    result = await db_session.execute(stmt)
    record = result.scalar_one()

    assert record.state_json["current_stage"] == "DONE"


@pytest.mark.asyncio
async def test_state_committed_after_each_graph_node(db_session, mock_gemini):
    """Each of the five completed nodes is committed independently."""
    state = _build_test_state()
    commit_stages = []
    original_commit = db_session.commit

    async def tracked_commit():
        commit_stages.append(True)
        await original_commit()

    with patch.object(db_session, "commit", new=tracked_commit):
        result = await run_investigation_with_persistence(state, db_session)

    assert result.current_stage == CurrentStage.DONE
    assert len(commit_stages) == 5
