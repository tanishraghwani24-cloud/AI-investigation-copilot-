"""Investigator profile and case-presence persistence.

Keeps the two collaboration concepts apart:

* **Historical** — ``InvestigationCase.investigator_id``: who triggered this
  investigation. Set once, never expires, still correct after completion.
* **Active** — ``CasePresence``: who is working a case *right now*. Heartbeat
  driven, and stale rows are ignored at read time so a closed browser or a
  finished investigation does not leave a case looking permanently occupied.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.investigator_auth import Investigator
from app.models.investigation import InvestigationCase
from app.models.investigator import CasePresence, InvestigatorProfile

logger = logging.getLogger(__name__)


def _presence_ttl() -> timedelta:
    return timedelta(seconds=int(getattr(settings, "CASE_PRESENCE_TTL_SECONDS", 90)))


def _as_uuid(value: str | uuid.UUID) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


class InvestigatorService:
    """Profile upsert, case attribution, and live presence."""

    async def upsert_profile(
        self,
        session: AsyncSession,
        investigator: Investigator,
    ) -> InvestigatorProfile:
        """Mirror the verified Supabase identity into the local profile table.

        Called on authenticated actions so a new officer needs no separate
        registration step. Only claims from the verified token are written —
        a caller cannot supply their own name.
        """
        user_id = _as_uuid(investigator.user_id)
        profile = (await session.execute(
            select(InvestigatorProfile).where(InvestigatorProfile.user_id == user_id)
        )).scalar_one_or_none()

        if profile is None:
            profile = InvestigatorProfile(
                user_id=user_id,
                full_name=investigator.full_name,
                email=investigator.email,
            )
            session.add(profile)
        else:
            # Keep the display name current if it changed in Supabase.
            profile.full_name = investigator.full_name
            if investigator.email:
                profile.email = investigator.email
        await session.flush()
        return profile

    async def get_profiles(
        self,
        session: AsyncSession,
        user_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, InvestigatorProfile]:
        """Look up several profiles at once, for list rendering."""
        if not user_ids:
            return {}
        rows = (await session.execute(
            select(InvestigatorProfile).where(InvestigatorProfile.user_id.in_(user_ids))
        )).scalars().all()
        return {row.user_id: row for row in rows}

    async def assign_case(
        self,
        session: AsyncSession,
        case_id: str,
        investigator: Investigator,
    ) -> None:
        """Record who triggered *case_id* (historical attribution).

        First writer wins: re-opening a case does not reassign it away from the
        officer who actually raised it.
        """
        case = (await session.execute(
            select(InvestigationCase).where(InvestigationCase.case_id == case_id)
        )).scalar_one_or_none()
        if case is None:
            logger.warning("cannot attribute unknown case %s", case_id)
            return
        if case.investigator_id is None:
            case.investigator_id = _as_uuid(investigator.user_id)

    async def heartbeat(
        self,
        session: AsyncSession,
        case_id: str,
        investigator: Investigator,
    ) -> None:
        """Mark this investigator as actively working *case_id* right now."""
        user_id = _as_uuid(investigator.user_id)
        presence = (await session.execute(
            select(CasePresence).where(
                CasePresence.case_id == case_id, CasePresence.user_id == user_id,
            )
        )).scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if presence is None:
            session.add(CasePresence(case_id=case_id, user_id=user_id, last_seen_at=now))
        else:
            presence.last_seen_at = now

    async def release(
        self,
        session: AsyncSession,
        case_id: str,
        investigator: Investigator,
    ) -> None:
        """Drop this investigator's presence on a case immediately."""
        await session.execute(
            delete(CasePresence).where(
                CasePresence.case_id == case_id,
                CasePresence.user_id == _as_uuid(investigator.user_id),
            )
        )

    async def release_case(self, session: AsyncSession, case_id: str) -> int:
        """Clear all presence on a case, whoever holds it.

        Called when the pipeline finishes so "currently working on this case"
        stops being true the moment it stops being true, rather than lingering
        until the heartbeat TTL expires. Historical attribution on the
        investigation itself is untouched.
        """
        result = await session.execute(
            delete(CasePresence).where(CasePresence.case_id == case_id)
        )
        return result.rowcount or 0

    async def active_presence(
        self,
        session: AsyncSession,
        case_ids: list[str] | None = None,
    ) -> dict[str, list[InvestigatorProfile]]:
        """Return the investigators currently active per case.

        Rows older than the TTL are ignored rather than deleted, so a brief
        network blip does not lose presence, and expired rows are cleaned up
        opportunistically on the next write.
        """
        cutoff = datetime.now(timezone.utc) - _presence_ttl()
        stmt = (
            select(CasePresence, InvestigatorProfile)
            .join(InvestigatorProfile, CasePresence.user_id == InvestigatorProfile.user_id)
            .where(CasePresence.last_seen_at >= cutoff)
            .order_by(CasePresence.last_seen_at.desc())
        )
        if case_ids:
            stmt = stmt.where(CasePresence.case_id.in_(case_ids))

        active: dict[str, list[InvestigatorProfile]] = {}
        for presence, profile in (await session.execute(stmt)).all():
            active.setdefault(presence.case_id, []).append(profile)
        return active

    async def purge_expired(self, session: AsyncSession) -> int:
        """Delete presence rows past the TTL. Returns the number removed."""
        cutoff = datetime.now(timezone.utc) - _presence_ttl()
        result = await session.execute(
            delete(CasePresence).where(CasePresence.last_seen_at < cutoff)
        )
        return result.rowcount or 0
