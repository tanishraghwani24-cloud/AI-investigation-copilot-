"""Test: Investigation service layer — Round 3 Tanish.

Verifies that InvestigationService:
  A. Can create and run an investigation via the graph.
  B. Can retrieve an existing investigation from the repository.
  C. Delegates persistence to the repository (not bypassing it).
  D. Delegates pipeline execution to the graph entrypoint.
  E. Returns a failed investigation result when the graph fails
     (rather than an unhandled service exception).

Uses an in-memory SQLite database. The Gemini boundary is mocked
globally by conftest.py.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.repository import InvestigationRepository
from app.db.session import Base
from app.models.investigation import InvestigationCase
from app.schemas.investigation_state import (
    CaseInput,
    CustomerProfile,
    InvestigationState,
    Transaction,
    create_initial_state,
)
from app.services.investigation_service import InvestigationService


# ── Fixtures ─────────────────────────────────────────────────────────


def _build_case_input() -> CaseInput:
    """Build a minimal realistic CaseInput for testing."""
    transaction = Transaction(
        transaction_id="TXN-SVC-001",
        amount=10_000.00,
        currency="USD",
        timestamp=datetime(2025, 8, 19, 14, 0, 0),
        sender_account="ACC-SVC-SENDER",
        receiver_account="ACC-SVC-RECEIVER",
        transaction_type="WIRE",
        channel="ONLINE",
    )

    customer = CustomerProfile(
        customer_id="CUST-SVC-001",
        name="Service Test User",
        email="svc@test.com",
        risk_rating="LOW",
    )

    return CaseInput(
        transactions=[transaction],
        customer_profile=customer,
        alert_reason="Service layer test case",
    )


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


# ── Test A — Create and run ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_run_investigation(db_session):
    """Service can create and execute an investigation end-to-end."""
    service = InvestigationService()
    case_input = _build_case_input()

    result = await service.create_and_run_investigation(
        case_id="CASE-SVC-001",
        case_input=case_input,
        session=db_session,
    )

    assert isinstance(result, InvestigationState)
    assert result.case_id == "CASE-SVC-001"
    # Pipeline should have run (at least context populated)
    assert result.context_intelligence is not None


# ── Test B — Retrieval ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_investigation(db_session):
    """Service retrieves an existing investigation correctly."""
    service = InvestigationService()
    case_input = _build_case_input()

    # First create one
    await service.create_and_run_investigation(
        case_id="CASE-SVC-002",
        case_input=case_input,
        session=db_session,
    )

    # Now retrieve it
    result = await service.get_investigation("CASE-SVC-002", db_session)

    assert result is not None
    assert isinstance(result, InvestigationState)
    assert result.case_id == "CASE-SVC-002"


@pytest.mark.asyncio
async def test_get_investigation_not_found(db_session):
    """Service returns None for a non-existent investigation."""
    service = InvestigationService()

    result = await service.get_investigation("CASE-NONEXISTENT", db_session)

    assert result is None


# ── Test C — Repository delegation ───────────────────────────────────


@pytest.mark.asyncio
async def test_repository_delegation(db_session):
    """Service uses the repository — the DB row exists after creation."""
    service = InvestigationService()
    case_input = _build_case_input()

    await service.create_and_run_investigation(
        case_id="CASE-SVC-003",
        case_input=case_input,
        session=db_session,
    )

    # Verify directly via DB query that the repository was used
    stmt = select(InvestigationCase).where(
        InvestigationCase.case_id == "CASE-SVC-003"
    )
    result = await db_session.execute(stmt)
    record = result.scalar_one_or_none()

    assert record is not None
    assert record.case_id == "CASE-SVC-003"
    assert record.state_json is not None


# ── Test D — Graph delegation ────────────────────────────────────────


@pytest.mark.asyncio
async def test_graph_delegation(db_session):
    """Service invokes the graph entrypoint — state is processed."""
    service = InvestigationService()
    case_input = _build_case_input()

    result = await service.create_and_run_investigation(
        case_id="CASE-SVC-004",
        case_input=case_input,
        session=db_session,
    )

    # If the graph ran, agent outputs should be populated
    assert result.context_intelligence is not None
    assert result.investigation_reasoning is not None
    assert result.evidence_compliance_validation is not None
    assert result.decision_optimization is not None
    assert result.investigation_report is not None


# ── Test E — Failed graph run ────────────────────────────────────────


@pytest.mark.asyncio
async def test_failed_graph_run_returns_failed_state(db_session):
    """A graph failure results in a FAILED state, not an unhandled exception."""
    service = InvestigationService()
    case_input = _build_case_input()

    # Make the context node blow up
    with patch(
        "app.graph.nodes.context_node.context_agent",
        side_effect=RuntimeError("Simulated context failure"),
    ):
        result = await service.create_and_run_investigation(
            case_id="CASE-SVC-005",
            case_input=case_input,
            session=db_session,
        )

    # Should NOT have raised — should return a failed state
    assert isinstance(result, InvestigationState)
    assert len(result.errors) >= 1
    assert result.errors[0].agent_name == "context"
    assert "Simulated context failure" in result.errors[0].message
