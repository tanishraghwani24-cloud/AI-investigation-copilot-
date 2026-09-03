"""P1 hardening: shared-secret API authentication.

Verifies the X-API-Key dependency added to the investigations, documents,
and mock-bank routers, and that /health stays open.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes import investigations as investigation_routes
from app.core.config import settings
from app.core.security import require_api_key
from app.db.session import get_db_session
from app.main import app


async def _mock_db_session():
    yield MagicMock()


@pytest.fixture
def auth_client():
    """A TestClient with the global auth bypass fixture removed for this test module."""
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides.pop(require_api_key, None)
    app.dependency_overrides[get_db_session] = _mock_db_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous_overrides)


def test_health_is_reachable_without_a_credential(auth_client: TestClient) -> None:
    response = auth_client.get("/api/health")
    assert response.status_code == 200


def test_protected_route_rejects_missing_credential(auth_client: TestClient) -> None:
    response = auth_client.get("/api/investigations")
    assert response.status_code == 401


def test_protected_route_rejects_invalid_credential(auth_client: TestClient) -> None:
    response = auth_client.get(
        "/api/investigations", headers={"X-API-Key": "not-the-secret"}
    )
    assert response.status_code == 401


def test_protected_route_accepts_valid_credential(auth_client: TestClient) -> None:
    with patch.object(
        investigation_routes._investigation_service,
        "list_investigations",
        new=AsyncMock(return_value=[]),
    ):
        response = auth_client.get(
            "/api/investigations", headers={"X-API-Key": settings.API_SHARED_SECRET}
        )
    assert response.status_code == 200


def test_mock_bank_route_is_also_protected(auth_client: TestClient) -> None:
    response = auth_client.get("/api/mock-bank/customers/CUST-DOES-NOT-EXIST")
    assert response.status_code == 401


def test_changing_case_id_without_a_credential_is_still_rejected(
    auth_client: TestClient,
) -> None:
    """A caller cannot bypass auth by simply guessing/changing a case ID."""
    response = auth_client.get("/api/investigations/SOME-OTHER-CASE-ID")
    assert response.status_code == 401
