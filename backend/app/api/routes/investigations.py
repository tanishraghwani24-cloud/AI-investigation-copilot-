"""Investigation API routes.

Provides the persisted investigation REST API.
"""

import asyncio
import secrets
from datetime import datetime, timezone
import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import rate_limit
from app.db.session import async_session_factory, get_db_session
from app.mock_bank.generator import MockBankScenario, generate_investigation_data
from app.core.config import settings
from app.services.gemini_client import _demo_mode_enabled
from app.services.investigator_service import InvestigatorService
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    CustomerProfile,
    InvestigationState,
    Transaction,
    CurrentStage,
    create_initial_state,
)
from app.services.investigation_service import InvestigationService
from app.services.mock_bank_service import MockBankService
from app.services.report_pdf_service import render_investigation_report_pdf

router = APIRouter()
logger = logging.getLogger(__name__)

CaseIdPath = Annotated[
    str,
    Path(
        min_length=1,
        max_length=80,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$",
        description="Investigation case identifier.",
    ),
]


class InvestigationRunResponse(BaseModel):
    """Immediate acknowledgement returned when a run is scheduled."""

    case_id: str
    status: AgentStatus
    current_stage: CurrentStage
    message: str

# ── Default seed for deterministic generation ────────────────────────
_DEFAULT_SEED: int = 42

# ── Service instance ─────────────────────────────────────────────────
_investigation_service = InvestigationService()
_investigators = InvestigatorService()


def _build_investigation_state(
    seed: int,
    scenario: MockBankScenario | str = MockBankScenario.DEFAULT,
) -> InvestigationState:
    """Build an InvestigationState from generated Mock Bank data.

    Maps mock_bank models into the schema-layer types used by the
    investigation pipeline.

    Args:
        seed: Integer seed for deterministic generation.

    Returns:
        A fully initialised InvestigationState ready for pipeline
        execution.
    """
    data = generate_investigation_data(seed, scenario=scenario)
    customer = data.customer
    account = data.account

    # Map mock_bank.Customer → schemas.CustomerProfile
    customer_profile = CustomerProfile(
        customer_id=customer.customer_id,
        name=f"{customer.first_name} {customer.last_name}",
        email=customer.email,
        phone=customer.phone,
        address=customer.address,
        date_of_birth=customer.date_of_birth,
        account_open_date=(
            customer.created_at.strftime("%Y-%m-%d")
            if customer.created_at
            else None
        ),
        risk_rating=customer.risk_rating,
        occupation=customer.occupation,
        nationality=customer.nationality,
    )

    # Map mock_bank.Transaction list → schemas.Transaction list
    schema_transactions: list[Transaction] = []
    for txn in data.transactions:
        schema_transactions.append(
            Transaction(
                transaction_id=txn.transaction_id,
                amount=txn.amount,
                currency=txn.currency,
                timestamp=(
                    txn.timestamp
                    if txn.timestamp
                    else datetime.now(timezone.utc)
                ),
                sender_account=txn.sender_account_id,
                receiver_account=txn.receiver_account_id,
                transaction_type=txn.transaction_type,
                channel=txn.channel,
                description=txn.description,
                location=txn.location,
            )
        )

    case_input = CaseInput(
        transactions=schema_transactions,
        customer_profile=customer_profile,
        alert_reason=data.alert_reason,
    )

    # Use deterministic case ID from seed
    selected_scenario = MockBankScenario(scenario)
    case_id = f"CASE-2025-{seed:05d}"
    if selected_scenario is not MockBankScenario.DEFAULT:
        case_id = f"{case_id}-{selected_scenario.value.upper()}"

    return create_initial_state(case_id=case_id, case_input=case_input)


# A fresh case is generated from an unused Mock Bank seed. The seed feeds both
# the case_id and the generated customer/account/transactions, so a new seed
# yields a genuinely different, valid case rather than a renamed copy of an
# existing one. Collisions are re-rolled rather than silently reusing a case.
_FRESH_SEED_MIN: int = 10_000
_FRESH_SEED_MAX: int = 999_999
_FRESH_SEED_ATTEMPTS: int = 12


async def _build_fresh_investigation_state(
    scenario: MockBankScenario | str,
    db: AsyncSession,
) -> InvestigationState:
    """Build a Mock Bank case whose ID is not already taken.

    ``create_investigation`` is idempotent per case ID, so reusing the default
    seed would re-open the same case instead of creating one. Picking an unused
    seed is what makes each request a distinct investigation.
    """
    span = _FRESH_SEED_MAX - _FRESH_SEED_MIN
    for _ in range(_FRESH_SEED_ATTEMPTS):
        seed = _FRESH_SEED_MIN + secrets.randbelow(span)
        state = _build_investigation_state(seed, scenario=scenario)
        if await _investigation_service.get_investigation(state.case_id, db) is None:
            return state
    raise HTTPException(
        status_code=503,
        detail="Could not allocate an unused investigation ID; please retry.",
    )


async def _build_investigation_state_from_db(account_id: str, db: AsyncSession) -> InvestigationState:
    svc = MockBankService()
    account = await svc.get_account(db, account_id)
    customer = None
    if account:
        customer = await svc.get_customer(db, account.customer_id)

    if not customer or not account:
        raise HTTPException(status_code=404, detail="Account or customer not found in Mock Bank")

    customer_profile = CustomerProfile(
        customer_id=customer.customer_id,
        name=customer.name or "",
        email=customer.email,
        phone=customer.phone,
        address=customer.address,
        date_of_birth=customer.date_of_birth,
        account_open_date=customer.created_at.strftime("%Y-%m-%d") if customer.created_at else None,
        risk_rating=customer.risk_rating,
        occupation=customer.occupation,
        nationality=customer.nationality,
    )

    transactions_db = await svc.get_account_transactions(db, account_id)
    alert_txns = transactions_db[-5:] if len(transactions_db) >= 5 else transactions_db

    schema_transactions = []
    for txn in alert_txns:
        schema_transactions.append(
            Transaction(
                transaction_id=txn.transaction_id,
                amount=txn.amount,
                currency=txn.currency,
                timestamp=txn.timestamp if txn.timestamp else datetime.now(timezone.utc),
                sender_account=txn.account_id,
                receiver_account=txn.receiver_account_id,
                transaction_type=txn.transaction_type,
                channel=txn.channel,
                description=txn.description,
                location=txn.location,
            )
        )

    case_input = CaseInput(
        transactions=schema_transactions,
        customer_profile=customer_profile,
        alert_reason="Suspicious activity detected in recent transactions",
    )

    # Extract the last part of the account ID for the case ID, defaulting to random if missing
    suffix = account_id[-4:] if len(account_id) >= 4 else "0001"
    case_id = f"CASE-MOCK-{suffix}"
    return create_initial_state(case_id=case_id, case_input=case_input)


@router.post("/investigations", response_model=InvestigationState)
async def create_investigation(
    scenario: MockBankScenario = Query(default=MockBankScenario.DEFAULT),
    account_id: str | None = Query(default=None, description="Mock bank account to investigate"),
    fresh: bool = Query(
        default=False,
        description="Allocate a new case ID instead of reopening the deterministic seed=42 case.",
    ),
    db: AsyncSession = Depends(get_db_session),
) -> InvestigationState:
    """Create a new investigation case.

    Persists a deterministic Mock Bank case input (seed=42) by default, so
    repeated calls reopen the same case. Pass ``fresh=true`` to allocate a new
    case from an unused seed — creation is idempotent per case ID, so that flag
    is what makes a request create rather than reopen. ``account_id`` continues
    to map an account to its own stable case. Agent outputs are populated only
    when the investigation is subsequently run.
    """
    if account_id:
        state = await _build_investigation_state_from_db(account_id, db)
    elif fresh:
        state = await _build_fresh_investigation_state(scenario, db)
    else:
        state = _build_investigation_state(_DEFAULT_SEED, scenario=scenario)

    case_input = state.case_input
    if _demo_mode_enabled():
        # Mock Bank supplies no counterparty or device, which would leave the
        # report's entity graph a single isolated node. Demo mode derives them
        # from the case; production case building is unchanged.
        from app.services.demo_data import enrich_case_for_demo

        case_input = enrich_case_for_demo(case_input)

    return await _investigation_service.create_investigation(
        state.case_id,
        case_input,
        db,
    )


@router.get("/investigations", response_model=list[InvestigationState])
async def list_investigations(
    status: CurrentStage | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> list[InvestigationState]:
    """List persisted investigations with optional stage filtering."""
    return await _investigation_service.list_investigations(
        db,
        status=status,
        offset=offset,
        limit=limit,
    )


@router.get("/investigations/{case_id}", response_model=InvestigationState)
async def get_investigation(
    case_id: CaseIdPath,
    db: AsyncSession = Depends(get_db_session),
) -> InvestigationState:
    """Retrieve the current persisted investigation state.

    Polls the persistence layer for the investigation identified by
    ``case_id`` and returns the full InvestigationState.

    Delegates to the InvestigationService for retrieval.

    Args:
        case_id: The investigation case identifier.
        db: Async database session (injected).

    Returns:
        The persisted InvestigationState.

    Raises:
        HTTPException 404: If no investigation exists with the given case_id.
    """
    state = await _investigation_service.get_investigation(case_id, db)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation not found: {case_id}",
        )

    return state


async def _demo_observability_pause() -> None:
    """Hold a demo investigation in progress long enough to be observed.

    A demo run completes in a couple of seconds, so a second officer polling the
    Officer Box would never catch the "in progress" presence. Pausing *before*
    the graph runs widens that window without touching the pipeline or its
    output. Never applied outside demo mode.
    """
    if not _demo_mode_enabled():
        return
    delay = float(getattr(settings, "DEMO_INVESTIGATION_DELAY_SECONDS", 0) or 0)
    if delay <= 0:
        return
    logger.info("demo mode: holding investigation in progress for %.1fs", delay)
    await asyncio.sleep(delay)


async def _release_case_presence(case_id: str) -> None:
    """Clear live presence once the pipeline has stopped running.

    Presence means "being worked on right now", so it ends with the run rather
    than lingering until the heartbeat TTL. Best-effort: a failure here must
    never mask the investigation's own outcome, and the TTL still expires the
    row as a backstop.
    """
    try:
        async with async_session_factory() as session:
            await _investigators.release_case(session, case_id)
            await session.commit()
    except Exception:
        logger.exception("Could not release case presence for %s", case_id)


async def _run_investigation_background(case_id: str) -> None:
    """Execute a scheduled investigation using an independent DB session."""
    try:
        await _demo_observability_pause()
        async with async_session_factory() as session:
            try:
                state = await _investigation_service.run_investigation(case_id, session)
                if state is None:
                    logger.error("Scheduled investigation disappeared: %s", case_id)
                await session.commit()
            except Exception as exc:
                await session.rollback()
                try:
                    await _investigation_service.record_background_failure(
                        case_id,
                        exc,
                        session,
                    )
                    await session.commit()
                except Exception:
                    await session.rollback()
                    logger.exception(
                        "Could not persist background failure for investigation %s",
                        case_id,
                    )
                logger.exception("Background investigation failed: %s", case_id)
    except Exception:
        logger.exception("Could not open a session for investigation %s", case_id)
    finally:
        # Whether the run succeeded or failed, it is no longer in progress.
        await _release_case_presence(case_id)


@router.post(
    "/investigations/{case_id}/run",
    response_model=InvestigationRunResponse,
    status_code=202,
)
async def run_investigation(
    case_id: CaseIdPath,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    _rate_limited: None = Depends(rate_limit("investigation_run", limit=10)),
) -> InvestigationRunResponse:
    """Acknowledge a run and execute the existing graph in the background."""
    started = await _investigation_service.start_investigation(case_id, db)
    if started is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation not found: {case_id}",
        )

    state, scheduled = started
    if scheduled:
        background_tasks.add_task(_run_investigation_background, case_id)
        message = "Investigation execution started in the background. Poll this resource for progress."
    else:
        message = "Investigation execution is already in progress. Poll this resource for progress."

    return InvestigationRunResponse(
        case_id=state.case_id,
        status=AgentStatus.IN_PROGRESS,
        current_stage=state.current_stage,
        message=message,
    )


@router.get("/investigations/{case_id}/report/download")
async def download_report(
    case_id: CaseIdPath,
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    """Download the investigation report as a Markdown file.

    Returns the ``detailed_narrative`` produced by the Reporting agent
    as a downloadable ``text/markdown`` attachment.

    Raises:
        HTTPException 404: If the case does not exist or its report
            has not been generated yet.
    """
    state = await _investigation_service.get_investigation(case_id, db)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation not found: {case_id}",
        )

    report = state.investigation_report
    if report is None or not report.detailed_narrative:
        raise HTTPException(
            status_code=404,
            detail=f"Report not yet generated for investigation: {case_id}",
        )

    filename = f"{case_id}-report.md"
    return Response(
        content=report.detailed_narrative,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/investigations/{case_id}/report/download.pdf")
async def download_report_pdf(
    case_id: CaseIdPath,
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    """Download the completed reporting agent output as a PDF."""
    state = await _investigation_service.get_investigation(case_id, db)
    if (
        state is None
        or state.current_stage != CurrentStage.DONE
        or state.investigation_report is None
        or state.investigation_report.status != AgentStatus.COMPLETED
    ):
        raise HTTPException(
            status_code=404,
            detail=f"Completed report not found for investigation: {case_id}",
        )

    return Response(
        content=render_investigation_report_pdf(case_id, state.investigation_report),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{case_id}-report.pdf"'},
    )
