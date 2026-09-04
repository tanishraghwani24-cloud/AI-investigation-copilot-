"""Tests for investigator attribution and live case presence.

The two concepts must stay separate: historical attribution is permanent, live
presence expires. Conflating them would leave completed cases looking forever
"in progress".
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.investigator_auth import Investigator
from app.db.session import Base
from app.models.investigation import InvestigationCase
from app.models.investigator import CasePresence, InvestigatorProfile
from app.services.investigator_service import InvestigatorService

RAHUL = Investigator(
    user_id="11111111-1111-1111-1111-111111111111",
    email="rahul.sharma@hollabank.com",
    full_name="Rahul Sharma",
)
PRIYA = Investigator(
    user_id="22222222-2222-2222-2222-222222222222",
    email="priya.nair@hollabank.com",
    full_name="Priya Nair",
)


@pytest_asyncio.fixture()
async def session():
    """In-memory SQLite session over the real ORM metadata."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[
                InvestigatorProfile.__table__,
                CasePresence.__table__,
                InvestigationCase.__table__,
            ],
        )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


@pytest.fixture()
def service():
    return InvestigatorService()


async def _case(session: AsyncSession, case_id: str) -> InvestigationCase:
    case = InvestigationCase(case_id=case_id, status="DONE", state_json={})
    session.add(case)
    await session.flush()
    return case


async def _age_presence(session: AsyncSession) -> None:
    """Push every presence row past the TTL, as an abandoned session would."""
    stale = datetime.now(timezone.utc) - timedelta(
        seconds=settings.CASE_PRESENCE_TTL_SECONDS + 60,
    )
    for presence in (await session.execute(select(CasePresence))).scalars().all():
        presence.last_seen_at = stale
    await session.flush()


class TestProfiles:
    @pytest.mark.asyncio
    async def test_a_profile_is_created_from_the_verified_identity(self, session, service):
        profile = await service.upsert_profile(session, RAHUL)

        assert profile.full_name == "Rahul Sharma"
        assert profile.email == "rahul.sharma@hollabank.com"
        assert str(profile.user_id) == RAHUL.user_id

    @pytest.mark.asyncio
    async def test_upsert_is_idempotent(self, session, service):
        await service.upsert_profile(session, RAHUL)
        await service.upsert_profile(session, RAHUL)

        profiles = await service.get_profiles(session, [uuid.UUID(RAHUL.user_id)])
        assert len(profiles) == 1

    @pytest.mark.asyncio
    async def test_a_renamed_investigator_is_kept_current(self, session, service):
        await service.upsert_profile(session, RAHUL)
        renamed = Investigator(
            user_id=RAHUL.user_id, email=RAHUL.email, full_name="Rahul S. Sharma",
        )

        profile = await service.upsert_profile(session, renamed)

        assert profile.full_name == "Rahul S. Sharma"

    @pytest.mark.asyncio
    async def test_different_investigators_are_distinct(self, session, service):
        await service.upsert_profile(session, RAHUL)
        await service.upsert_profile(session, PRIYA)

        profiles = await service.get_profiles(
            session, [uuid.UUID(RAHUL.user_id), uuid.UUID(PRIYA.user_id)],
        )
        assert {p.full_name for p in profiles.values()} == {"Rahul Sharma", "Priya Nair"}


class TestHistoricalAttribution:
    @pytest.mark.asyncio
    async def test_a_case_records_who_triggered_it(self, session, service):
        await service.upsert_profile(session, RAHUL)
        case = await _case(session, "CASE-ALERT-1")

        await service.assign_case(session, "CASE-ALERT-1", RAHUL)

        assert str(case.investigator_id) == RAHUL.user_id

    @pytest.mark.asyncio
    async def test_attribution_is_not_stolen_by_a_later_officer(self, session, service):
        """Re-opening a case must not reassign it away from its originator."""
        await service.upsert_profile(session, RAHUL)
        await service.upsert_profile(session, PRIYA)
        case = await _case(session, "CASE-ALERT-1")
        await service.assign_case(session, "CASE-ALERT-1", RAHUL)

        await service.assign_case(session, "CASE-ALERT-1", PRIYA)

        assert str(case.investigator_id) == RAHUL.user_id

    @pytest.mark.asyncio
    async def test_an_unknown_case_is_ignored_rather_than_raising(self, session, service):
        await service.upsert_profile(session, RAHUL)

        await service.assign_case(session, "CASE-DOES-NOT-EXIST", RAHUL)

    @pytest.mark.asyncio
    async def test_a_legacy_case_simply_has_no_investigator(self, session, service):
        case = await _case(session, "CASE-LEGACY")

        assert case.investigator_id is None


class TestLivePresence:
    @pytest.mark.asyncio
    async def test_a_heartbeat_marks_an_investigator_active(self, session, service):
        await service.upsert_profile(session, RAHUL)

        await service.heartbeat(session, "CASE-1", RAHUL)

        active = await service.active_presence(session)
        assert [p.full_name for p in active["CASE-1"]] == ["Rahul Sharma"]

    @pytest.mark.asyncio
    async def test_repeated_heartbeats_do_not_duplicate_the_officer(self, session, service):
        await service.upsert_profile(session, RAHUL)
        await service.heartbeat(session, "CASE-1", RAHUL)
        await service.heartbeat(session, "CASE-1", RAHUL)

        active = await service.active_presence(session)
        assert len(active["CASE-1"]) == 1

    @pytest.mark.asyncio
    async def test_another_officer_sees_who_is_working_the_case(self, session, service):
        await service.upsert_profile(session, RAHUL)
        await service.heartbeat(session, "CASE-102", RAHUL)

        active = await service.active_presence(session, ["CASE-102"])

        profile = active["CASE-102"][0]
        assert profile.full_name == "Rahul Sharma"
        assert profile.full_name[0].upper() == "R"

    @pytest.mark.asyncio
    async def test_stale_presence_is_not_reported_as_active(self, session, service):
        """A crashed tab must not pin a case as occupied forever."""
        await service.upsert_profile(session, RAHUL)
        await service.heartbeat(session, "CASE-1", RAHUL)
        assert await service.active_presence(session)  # sanity: active first

        await _age_presence(session)

        assert await service.active_presence(session) == {}

    @pytest.mark.asyncio
    async def test_releasing_clears_presence_immediately(self, session, service):
        await service.upsert_profile(session, RAHUL)
        await service.heartbeat(session, "CASE-1", RAHUL)

        await service.release(session, "CASE-1", RAHUL)

        assert await service.active_presence(session) == {}

    @pytest.mark.asyncio
    async def test_releasing_only_clears_your_own_presence(self, session, service):
        await service.upsert_profile(session, RAHUL)
        await service.upsert_profile(session, PRIYA)
        await service.heartbeat(session, "CASE-1", RAHUL)
        await service.heartbeat(session, "CASE-1", PRIYA)

        await service.release(session, "CASE-1", RAHUL)

        active = await service.active_presence(session)
        assert [p.full_name for p in active["CASE-1"]] == ["Priya Nair"]

    @pytest.mark.asyncio
    async def test_purge_removes_expired_rows(self, session, service):
        await service.upsert_profile(session, RAHUL)
        await service.heartbeat(session, "CASE-1", RAHUL)

        await _age_presence(session)

        assert await service.purge_expired(session) == 1

    @pytest.mark.asyncio
    async def test_presence_and_attribution_are_independent(self, session, service):
        """Completing a case clears presence but keeps the historical handler."""
        await service.upsert_profile(session, RAHUL)
        case = await _case(session, "CASE-1")
        await service.assign_case(session, "CASE-1", RAHUL)
        await service.heartbeat(session, "CASE-1", RAHUL)

        await service.release(session, "CASE-1", RAHUL)

        assert await service.active_presence(session) == {}
        assert str(case.investigator_id) == RAHUL.user_id
