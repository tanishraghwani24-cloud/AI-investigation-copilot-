"""Tests for the lifetime of "currently working on this case".

Presence must last exactly as long as the pipeline runs: long enough for a
colleague's Officer Box to poll and see it, and no longer. Historical
attribution is unaffected either way.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.routes import investigations as investigation_routes
from app.core.config import settings
from app.core.investigator_auth import Investigator

RAHUL = Investigator(
    user_id="11111111-1111-1111-1111-111111111111",
    email="rahul.sharma@hollabank.com",
    full_name="Rahul Sharma",
)


@pytest.fixture()
def demo_mode(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True, raising=False)


@pytest.fixture()
def production_mode(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False, raising=False)


class TestDemoObservabilityDelay:
    """A demo run is held in progress long enough to be seen."""

    @pytest.mark.asyncio
    async def test_demo_mode_pauses_before_running(self, demo_mode, monkeypatch):
        monkeypatch.setattr(settings, "DEMO_INVESTIGATION_DELAY_SECONDS", 12.0, raising=False)
        slept: list[float] = []

        async def _record(seconds):
            slept.append(seconds)

        monkeypatch.setattr(investigation_routes.asyncio, "sleep", _record)
        await investigation_routes._demo_observability_pause()

        assert slept == [12.0]

    @pytest.mark.asyncio
    async def test_the_delay_is_long_enough_to_outlast_a_ui_poll(self, demo_mode):
        """The window must exceed the Officer Box poll interval, or a colleague
        can miss it entirely."""
        delay = float(settings.DEMO_INVESTIGATION_DELAY_SECONDS)

        # The frontend polls every 10s; a strictly longer window guarantees at
        # least one poll lands inside it.
        assert delay > 10.0

    @pytest.mark.asyncio
    async def test_production_is_never_delayed(self, production_mode, monkeypatch):
        monkeypatch.setattr(settings, "DEMO_INVESTIGATION_DELAY_SECONDS", 12.0, raising=False)
        slept: list[float] = []

        async def _record(seconds):
            slept.append(seconds)

        monkeypatch.setattr(investigation_routes.asyncio, "sleep", _record)
        await investigation_routes._demo_observability_pause()

        assert slept == []

    @pytest.mark.asyncio
    async def test_a_zero_delay_disables_the_pause(self, demo_mode, monkeypatch):
        monkeypatch.setattr(settings, "DEMO_INVESTIGATION_DELAY_SECONDS", 0, raising=False)
        slept: list[float] = []

        async def _record(seconds):
            slept.append(seconds)

        monkeypatch.setattr(investigation_routes.asyncio, "sleep", _record)
        await investigation_routes._demo_observability_pause()

        assert slept == []


class TestPresenceReleasedOnCompletion:
    """Presence ends with the run, not with the heartbeat TTL."""

    @pytest.mark.asyncio
    async def test_presence_is_released_after_a_successful_run(self, production_mode):
        released: list[str] = []

        async def _release(_session, case_id):
            released.append(case_id)
            return 1

        session = MagicMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()

        with patch.object(
            investigation_routes, "async_session_factory",
            return_value=_ctx(session),
        ), patch.object(
            investigation_routes._investigation_service, "run_investigation",
            new=AsyncMock(return_value=MagicMock()),
        ), patch.object(
            investigation_routes._investigators, "release_case", new=_release,
        ):
            await investigation_routes._run_investigation_background("CASE-1")

        assert released == ["CASE-1"]

    @pytest.mark.asyncio
    async def test_presence_is_released_even_when_the_run_fails(self, production_mode):
        """A crashed pipeline must not leave the case looking occupied."""
        released: list[str] = []

        async def _release(_session, case_id):
            released.append(case_id)
            return 1

        session = MagicMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()

        with patch.object(
            investigation_routes, "async_session_factory",
            return_value=_ctx(session),
        ), patch.object(
            investigation_routes._investigation_service, "run_investigation",
            new=AsyncMock(side_effect=RuntimeError("pipeline exploded")),
        ), patch.object(
            investigation_routes._investigation_service, "record_background_failure",
            new=AsyncMock(),
        ), patch.object(
            investigation_routes._investigators, "release_case", new=_release,
        ):
            await investigation_routes._run_investigation_background("CASE-2")

        assert released == ["CASE-2"]

    @pytest.mark.asyncio
    async def test_a_release_failure_does_not_escape(self, production_mode):
        """Releasing presence is best-effort; the TTL is the backstop."""
        session = MagicMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()

        with patch.object(
            investigation_routes, "async_session_factory",
            return_value=_ctx(session),
        ), patch.object(
            investigation_routes._investigation_service, "run_investigation",
            new=AsyncMock(return_value=MagicMock()),
        ), patch.object(
            investigation_routes._investigators, "release_case",
            new=AsyncMock(side_effect=RuntimeError("db gone")),
        ):
            await investigation_routes._run_investigation_background("CASE-3")


def _ctx(session):
    """Async-context-manager wrapper around a stub session."""
    class _Ctx:
        async def __aenter__(self):
            return session

        async def __aexit__(self, *_exc):
            return False

    return _Ctx()
