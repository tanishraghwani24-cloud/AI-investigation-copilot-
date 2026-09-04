"""Proof that protected data actually requires a signed-in officer.

The rest of the suite runs with the officer-session requirement bypassed (see
conftest) so business-logic tests need not mint tokens. These tests deliberately
remove that bypass and assert against the real dependency, because "the API is
protected" is a claim that must be checked, not assumed.

Before this was enforced, the shared API key alone opened every data route — and
the browser proxy attaches that key for anyone, so it protected the deployment
from the internet but not one user from another.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.investigator_auth import require_investigator
from app.core.security import require_api_key
from app.db.session import get_db_session
from app.main import app

# Every route an unauthenticated caller must not be able to read or act on.
PROTECTED_GET = [
    "/api/investigations",
    "/api/investigations/CASE-ANY",
    "/api/investigations/CASE-ANY/report/download",
    "/api/alerts",
    "/api/alerts/by-case/CASE-ANY",
    "/api/mock-bank/customers/CUST-MOCK-001",
    "/api/mock-bank/accounts/ACC-MOCK-001",
    "/api/mock-bank/accounts/ACC-MOCK-001/transactions",
    "/api/mock-bank/transactions/TXN-ANY",
    "/api/investigators/me",
    "/api/investigators/assignments",
    "/api/presence",
]

PROTECTED_POST = [
    "/api/investigations",
    "/api/investigations/CASE-ANY/run",
    "/api/alerts/ALERT-ANY/investigate",
    "/api/mock-bank/simulate",
    "/api/presence/CASE-ANY/heartbeat",
]


@pytest.fixture()
def unauthenticated_client(monkeypatch):
    """A client presenting the API key but no officer session.

    This is exactly the position a logged-out browser is in: the Next proxy
    attaches the shared secret on its behalf.
    """
    async def _db():
        yield None

    previous = app.dependency_overrides.copy()
    app.dependency_overrides.clear()
    # Keep the deployment key satisfied so the *session* requirement is what is
    # under test, not the API key.
    app.dependency_overrides[require_api_key] = lambda: None
    app.dependency_overrides[get_db_session] = _db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)


class TestUnauthenticatedAccessIsRefused:
    @pytest.mark.parametrize("path", PROTECTED_GET)
    def test_get_requires_an_officer_session(self, unauthenticated_client, path):
        assert unauthenticated_client.get(path).status_code == 401, path

    @pytest.mark.parametrize("path", PROTECTED_POST)
    def test_post_requires_an_officer_session(self, unauthenticated_client, path):
        assert unauthenticated_client.post(path).status_code == 401, path

    def test_an_invalid_token_is_refused(self, unauthenticated_client):
        response = unauthenticated_client.get(
            "/api/investigations", headers={"Authorization": "Bearer not-a-real-token"},
        )

        assert response.status_code == 401

    def test_no_case_data_leaks_in_the_refusal(self, unauthenticated_client):
        """A 401 body must not carry the very data it is withholding."""
        body = unauthenticated_client.get("/api/investigations").text.lower()

        assert "case-" not in body
        assert "customer" not in body


class TestOpenRoutesAreDeliberate:
    def test_health_stays_open_for_uptime_checks(self, unauthenticated_client):
        assert unauthenticated_client.get("/api/health").status_code == 200

    def test_officer_lookup_is_reachable_before_sign_in(self, unauthenticated_client):
        """Sign-in cannot require a session, so this one route must not either.

        It is still behind the deployment API key and grants nothing on its own:
        the password must still satisfy Supabase.
        """
        from unittest.mock import AsyncMock, MagicMock

        # This route reaches the database, unlike the ones above which are
        # rejected before any handler runs.
        session = MagicMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result)

        async def _db():
            yield session

        app.dependency_overrides[get_db_session] = _db
        response = unauthenticated_client.post(
            "/api/officers/lookup", json={"officer_id": "OFF-NOPE"},
        )

        # 404 (unknown id), never 401 — the route itself is reachable.
        assert response.status_code == 404


class TestApiKeyStillRequired:
    """The officer session is additive; it does not replace the shared secret."""

    def test_a_valid_session_without_the_api_key_is_still_refused(self, monkeypatch):
        from app.core.investigator_auth import Investigator

        previous = app.dependency_overrides.copy()
        app.dependency_overrides.clear()
        app.dependency_overrides[require_investigator] = lambda: Investigator(
            user_id="1", email="a@b.com", full_name="A B",
        )
        monkeypatch.setattr(
            "app.core.config.settings.API_SHARED_SECRET", "the-real-secret",
        )
        with TestClient(app) as client:
            response = client.get("/api/investigations")
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)

        assert response.status_code == 401
