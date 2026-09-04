"""Fraud alert API routes.

The Officer Inbox reads alerts here and escalates one into an investigation.
Both the alert list and the escalation are backend state: the inbox does not
invent alerts, and it does not mark them handled on its own.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.investigator_auth import Investigator, get_optional_investigator
from app.db.session import get_db_session
from app.models.mock_bank import MockBankAlert
from app.schemas.investigation_state import (
    CaseInput,
    CustomerProfile,
    InvestigationState,
    Transaction,
)
from app.services.alert_simulator import AlertSimulator
from app.services.investigator_service import InvestigatorService
from app.services.mock_bank_service import MockBankService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["alerts"])

_mock_bank = MockBankService()
_simulator = AlertSimulator()
_investigators = InvestigatorService()

AlertIdPath = Annotated[str, Path(min_length=1, max_length=64, description="Alert identifier")]

# How much account history to attach to an investigation raised from an alert.
_HISTORY_LIMIT = 10


class AlertResponse(BaseModel):
    """One fraud alert as the Officer Inbox sees it."""

    alert_id: str
    transaction_id: str
    account_id: str
    customer_id: str | None = None
    customer_name: str | None = None
    reason: str
    severity: str
    risk_score: float
    status: str
    case_id: str | None = None
    amount: float | None = None
    currency: str | None = None
    transaction_type: str | None = None
    created_at: datetime


class SimulationResponse(BaseModel):
    """Result of one forced simulator tick."""

    transaction_id: str | None = None
    alert_id: str | None = None
    alert_raised: bool = False


class InvestigateAlertResponse(BaseModel):
    """The investigation an alert was escalated to."""

    alert_id: str
    case_id: str
    created: bool = Field(description="False when the alert was already escalated.")


def _to_response(alert: MockBankAlert, extras: dict | None = None) -> AlertResponse:
    payload = {
        "alert_id": alert.alert_id,
        "transaction_id": alert.transaction_id,
        "account_id": alert.account_id,
        "customer_id": alert.customer_id,
        "reason": alert.reason,
        "severity": alert.severity,
        "risk_score": alert.risk_score,
        "status": alert.status,
        "case_id": alert.case_id,
        "created_at": alert.created_at,
    }
    payload.update(extras or {})
    return AlertResponse(**payload)


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(
    status: Literal["OPEN", "INVESTIGATING", "ALL"] = Query(
        default="OPEN", description="Filter by alert status; ALL returns every alert.",
    ),
    limit: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> list[AlertResponse]:
    """List alerts, newest first.

    The inbox polls this, so it is a plain read: newly simulated alerts appear
    on the next poll without the officer reloading the page.
    """
    stmt = select(MockBankAlert).order_by(MockBankAlert.created_at.desc()).limit(limit)
    if status != "ALL":
        stmt = stmt.where(MockBankAlert.status == status)
    alerts = (await db.execute(stmt)).scalars().all()

    responses: list[AlertResponse] = []
    for alert in alerts:
        extras: dict = {}
        transaction = await _mock_bank.get_transaction(db, alert.transaction_id)
        if transaction is not None:
            extras.update({
                "amount": transaction.amount,
                "currency": transaction.currency,
                "transaction_type": transaction.transaction_type,
            })
        if alert.customer_id:
            customer = await _mock_bank.get_customer(db, alert.customer_id)
            if customer is not None:
                extras["customer_name"] = customer.name
        responses.append(_to_response(alert, extras))
    return responses


@router.post("/mock-bank/simulate", response_model=SimulationResponse, status_code=201)
async def simulate_activity(
    db: AsyncSession = Depends(get_db_session),
) -> SimulationResponse:
    """Force one simulator tick.

    The background loop already runs on its own timer; this exists so a demo or
    a test can produce an alert on demand instead of waiting for the interval.
    """
    transaction, alert = await _simulator.simulate_once(db)
    return SimulationResponse(
        transaction_id=transaction.transaction_id if transaction else None,
        alert_id=alert.alert_id if alert else None,
        alert_raised=alert is not None,
    )


async def _build_case_input_from_alert(
    alert: MockBankAlert,
    db: AsyncSession,
) -> CaseInput:
    """Assemble the investigation input from the alert's own transaction.

    The alerting transaction leads, followed by recent history on the same
    account, so the investigation reasons about the activity that was actually
    flagged rather than a generic sample.
    """
    flagged = await _mock_bank.get_transaction(db, alert.transaction_id)
    if flagged is None:
        raise HTTPException(
            status_code=409,
            detail=f"Alert {alert.alert_id} references a transaction that no longer exists.",
        )

    history = await _mock_bank.get_account_transactions(db, alert.account_id)
    records = [flagged] + [
        record for record in reversed(history)
        if record.transaction_id != flagged.transaction_id
    ][: _HISTORY_LIMIT - 1]

    transactions = [
        Transaction(
            transaction_id=record.transaction_id,
            amount=record.amount,
            currency=record.currency,
            timestamp=record.timestamp or alert.created_at,
            sender_account=record.account_id,
            receiver_account=record.receiver_account_id or "UNKNOWN",
            transaction_type=record.transaction_type,
            channel=record.channel,
            description=record.description,
            location=record.location,
        )
        for record in records
    ]

    customer_profile = None
    if alert.customer_id:
        customer = await _mock_bank.get_customer(db, alert.customer_id)
        if customer is not None:
            customer_profile = CustomerProfile(
                customer_id=customer.customer_id,
                name=customer.name or "Unknown customer",
                email=customer.email,
                phone=customer.phone,
                address=customer.address,
                date_of_birth=customer.date_of_birth,
                risk_rating=customer.risk_rating,
                occupation=customer.occupation,
                nationality=customer.nationality,
            )

    return CaseInput(
        transactions=transactions,
        customer_profile=customer_profile,
        alert_reason=alert.reason,
    )


@router.post(
    "/alerts/{alert_id}/investigate",
    response_model=InvestigateAlertResponse,
    status_code=201,
)
async def investigate_alert(
    alert_id: AlertIdPath,
    background_tasks: BackgroundTasks,
    investigator: Investigator | None = Depends(get_optional_investigator),
    db: AsyncSession = Depends(get_db_session),
) -> InvestigateAlertResponse:
    """Escalate one alert into its own investigation and start the pipeline.

    The case ID is derived from the alert ID, so escalating the same alert twice
    cannot produce two investigations: the second call finds the alert already
    carries a case and returns it untouched.

    When a signed-in investigator triggers this, the case is attributed to them
    and they are marked as actively working it. Identity comes only from the
    verified token — an unauthenticated caller creates an unassigned case
    exactly as before rather than being able to name someone else.
    """
    # Imported here so the investigations module stays the single owner of the
    # run/persist plumbing rather than this route duplicating it.
    from app.api.routes.investigations import (
        _investigation_service,
        _run_investigation_background,
    )
    from app.services.gemini_client import _demo_mode_enabled

    alert = (await db.execute(
        select(MockBankAlert).where(MockBankAlert.alert_id == alert_id)
    )).scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")

    if alert.case_id:
        # Already escalated. If a *different* officer is still actively working
        # it, refuse rather than quietly handing over the case — two officers
        # must not both believe they own an in-flight investigation. Once the
        # run finishes and presence is released, this reverts to the ordinary
        # idempotent response so the case can still be reopened or viewed.
        active = (await _investigators.active_presence(db, [alert.case_id])).get(
            alert.case_id, []
        )
        holder = next(
            (
                profile for profile in active
                if investigator is None or str(profile.user_id) != investigator.user_id
            ),
            None,
        )
        if holder is not None:
            raise HTTPException(
                status_code=409,
                detail=f"{holder.full_name} is already investigating this alert.",
            )
        return InvestigateAlertResponse(
            alert_id=alert.alert_id, case_id=alert.case_id, created=False,
        )

    case_id = f"CASE-{alert.alert_id}"
    case_input = await _build_case_input_from_alert(alert, db)
    if _demo_mode_enabled():
        # Same enrichment the manual create path applies, so the report's
        # entity graph is populated. Demo-mode behaviour is unchanged.
        from app.services.demo_data import enrich_case_for_demo

        case_input = enrich_case_for_demo(case_input)

    await _investigation_service.create_investigation(case_id, case_input, db)

    alert.case_id = case_id
    alert.status = "INVESTIGATING"
    if investigator is not None:
        await _investigators.upsert_profile(db, investigator)
        await _investigators.assign_case(db, case_id, investigator)
        await _investigators.heartbeat(db, case_id, investigator)
    await db.commit()

    started = await _investigation_service.start_investigation(case_id, db)
    if started is not None and started[1]:
        background_tasks.add_task(_run_investigation_background, case_id)

    logger.info("alert %s escalated to investigation %s", alert.alert_id, case_id)
    return InvestigateAlertResponse(alert_id=alert.alert_id, case_id=case_id, created=True)


@router.get("/alerts/by-case/{case_id}", response_model=AlertResponse)
async def get_alert_for_case(
    case_id: Annotated[str, Path(min_length=1, max_length=64)],
    db: AsyncSession = Depends(get_db_session),
) -> AlertResponse:
    """Return the alert an investigation was raised from.

    This is the investigation-to-alert direction of the link, so a case can
    always be traced back to the activity that triggered it.
    """
    alert = (await db.execute(
        select(MockBankAlert).where(MockBankAlert.case_id == case_id)
    )).scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=404, detail=f"No alert linked to case: {case_id}")
    return _to_response(alert)
