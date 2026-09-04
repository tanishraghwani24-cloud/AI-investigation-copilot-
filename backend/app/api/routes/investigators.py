"""Investigator identity and live case-presence routes.

Every identity here comes from a verified Supabase token. Nothing in a request
body or query string can name an investigator, so one officer cannot act or
appear as another.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.core.investigator_auth import Investigator, require_investigator
from app.models.investigation import InvestigationCase
from app.models.investigator import InvestigatorProfile
from app.db.session import get_db_session
from app.services.investigator_service import InvestigatorService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["investigators"])

_service = InvestigatorService()

CaseIdPath = Annotated[str, Path(min_length=1, max_length=64)]


class InvestigatorSummary(BaseModel):
    """The identity the UI needs to draw an avatar and its tooltip."""

    user_id: str
    full_name: str
    email: str | None = None
    initial: str
    officer_id: str | None = None
    role: str | None = None


class OfficerLookupRequest(BaseModel):
    """Resolve an Officer ID to the account Supabase authenticates."""

    officer_id: str


class OfficerLookupResponse(BaseModel):
    """The internal email for an Officer ID.

    Consumed only by the Next.js sign-in route, which runs server-side and
    never returns the email to the browser. It carries no credential and
    proves nothing on its own — a password still has to satisfy Supabase.
    """

    email: str


class PresenceEntry(BaseModel):
    """Who is currently working a given case."""

    case_id: str
    investigators: list[InvestigatorSummary]


def _summary(
    user_id, full_name: str, email: str | None,
    officer_id: str | None = None, role: str | None = None,
) -> InvestigatorSummary:
    # The initial is derived from the stored name, never sent by the client.
    return InvestigatorSummary(
        user_id=str(user_id),
        full_name=full_name,
        email=email,
        initial=(full_name or "?").strip()[:1].upper() or "?",
        officer_id=officer_id,
        role=role,
    )


@router.get("/investigators/me", response_model=InvestigatorSummary)
async def get_me(
    investigator: Investigator = Depends(require_investigator),
    db: AsyncSession = Depends(get_db_session),
) -> InvestigatorSummary:
    """Return the signed-in investigator, creating their profile on first use.

    This doubles as registration: an officer who can authenticate with Supabase
    gets a profile the first time they use the app, with no separate signup.
    """
    profile = await _service.upsert_profile(db, investigator)
    await db.commit()
    return _summary(
        profile.user_id, profile.full_name, profile.email,
        profile.officer_id, profile.role,
    )


@router.get("/presence", response_model=list[PresenceEntry])
async def list_presence(
    investigator: Investigator = Depends(require_investigator),
    db: AsyncSession = Depends(get_db_session),
) -> list[PresenceEntry]:
    """List every case with an investigator currently working it.

    The Officer Box polls this alongside its alert poll, reusing the existing
    refresh rhythm rather than adding a socket.
    """
    active = await _service.active_presence(db)
    return [
        PresenceEntry(
            case_id=case_id,
            investigators=[_summary(p.user_id, p.full_name, p.email) for p in profiles],
        )
        for case_id, profiles in active.items()
    ]


@router.post("/presence/{case_id}/heartbeat", response_model=PresenceEntry, status_code=200)
async def heartbeat(
    case_id: CaseIdPath,
    investigator: Investigator = Depends(require_investigator),
    db: AsyncSession = Depends(get_db_session),
) -> PresenceEntry:
    """Refresh this investigator's claim on a case.

    Presence expires without heartbeats, so a crashed tab or a finished
    investigation stops showing as active on its own.
    """
    await _service.upsert_profile(db, investigator)
    await _service.heartbeat(db, case_id, investigator)
    await _service.purge_expired(db)
    await db.commit()

    active = await _service.active_presence(db, [case_id])
    return PresenceEntry(
        case_id=case_id,
        investigators=[
            _summary(p.user_id, p.full_name, p.email) for p in active.get(case_id, [])
        ],
    )


@router.delete("/presence/{case_id}", status_code=204)
async def release_presence(
    case_id: CaseIdPath,
    investigator: Investigator = Depends(require_investigator),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Give up this investigator's claim on a case immediately."""
    await _service.release(db, case_id, investigator)
    await db.commit()


class CaseAssignment(BaseModel):
    """The investigator who handled one case (historical attribution)."""

    case_id: str
    investigator: InvestigatorSummary | None = None


@router.get("/investigators/assignments", response_model=list[CaseAssignment])
async def list_assignments(
    investigator: Investigator = Depends(require_investigator),
    db: AsyncSession = Depends(get_db_session),
) -> list[CaseAssignment]:
    """Map each investigation to the officer who triggered it.

    Returned separately from the investigation list so the existing
    ``InvestigationState`` response contract is untouched; the Investigations
    page joins the two by case id. Cases raised before investigator accounts
    existed simply come back with ``investigator: null``, which the UI renders
    as unassigned rather than inventing a name.
    """
    rows = (await db.execute(
        select(InvestigationCase.case_id, InvestigationCase.investigator_id)
    )).all()

    profiles = await _service.get_profiles(
        db, [row.investigator_id for row in rows if row.investigator_id is not None],
    )
    assignments: list[CaseAssignment] = []
    for row in rows:
        profile = profiles.get(row.investigator_id) if row.investigator_id else None
        assignments.append(CaseAssignment(
            case_id=row.case_id,
            investigator=(
                _summary(profile.user_id, profile.full_name, profile.email)
                if profile is not None else None
            ),
        ))
    return assignments


@router.post("/officers/lookup", response_model=OfficerLookupResponse)
async def lookup_officer(
    payload: OfficerLookupRequest,
    db: AsyncSession = Depends(get_db_session),
) -> OfficerLookupResponse:
    """Map an Officer ID to the email Supabase authenticates it with.

    Deliberately *not* behind an investigator session: it runs before anyone is
    signed in. It is still behind the deployment's API key, is only ever called
    by the server-side sign-in route, and grants nothing by itself — the
    password must still satisfy Supabase Auth.

    Unknown IDs return 404 with no detail beyond that, so this cannot be used
    to confirm anything about an officer other than whether the ID exists.
    """
    officer_id = payload.officer_id.strip().upper()
    profile = (await db.execute(
        select(InvestigatorProfile).where(InvestigatorProfile.officer_id == officer_id)
    )).scalar_one_or_none()
    if profile is None or not profile.email:
        raise HTTPException(status_code=404, detail="Unknown officer ID.")
    return OfficerLookupResponse(email=profile.email)
