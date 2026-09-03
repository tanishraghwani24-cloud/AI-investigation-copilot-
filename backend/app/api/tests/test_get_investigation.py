"""Round 3 tests for GET /api/investigations/{case_id} endpoint.

Covers:
- TEST 7: Existing investigation returns HTTP 200 with valid state
- TEST 8: Unknown investigation returns HTTP 404
- TEST 9: Persisted state round trip — fields survive

Uses the same mock DB session pattern established in
test_document_upload.py to avoid requiring live Postgres.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.schemas.investigation_state import (
    CaseInput,
    CustomerProfile,
    InvestigationState,
    Transaction,
    create_initial_state,
)

from datetime import datetime, timezone


# ── Mock database session ────────────────────────────────────────────


async def _mock_get_db_session():
    """Yield a mock async session that doesn't touch Postgres."""
    yield MagicMock()


@pytest.fixture(autouse=True)
def _override_dependencies():
    """Override the DB session dependency globally for these tests."""
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db_session] = _mock_get_db_session
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)

client = TestClient(app)


# ── Test data ────────────────────────────────────────────────────────


def _make_test_state() -> InvestigationState:
    """Create a test InvestigationState for persistence mocking."""
    transactions = [
        Transaction(
            transaction_id="TXN-GET-001",
            amount=12_000.00,
            currency="USD",
            timestamp=datetime(2025, 8, 10, 10, 0, 0),
            sender_account="ACC-SRC-GET",
            receiver_account="ACC-DST-GET",
            transaction_type="WIRE",
            channel="ONLINE",
            description="Test wire transfer",
            location="Boston, US",
        ),
    ]
    case_input = CaseInput(
        transactions=transactions,
        customer_profile=CustomerProfile(
            customer_id="CUST-GET-001",
            name="Get Endpoint Test Customer",
            risk_rating="LOW",
        ),
        alert_reason="Automated test alert.",
    )
    return create_initial_state(
        case_id="CASE-GET-001",
        case_input=case_input,
    )





# ── TEST 7: Existing investigation ───────────────────────────────────


class TestExistingInvestigation:
    """GET /api/investigations/{case_id} for an existing case."""

    def test_returns_http_200(self) -> None:
        """GET returns HTTP 200 for an existing investigation."""
        test_state = _make_test_state()
        with patch(
            "app.api.routes.investigations._investigation_service.get_investigation",
            new_callable=AsyncMock,
            return_value=test_state,
        ):
            response = client.get("/api/investigations/CASE-GET-001")
        assert response.status_code == 200

    def test_returns_valid_investigation_state(self) -> None:
        """Response validates against InvestigationState schema."""
        test_state = _make_test_state()
        with patch(
            "app.api.routes.investigations._investigation_service.get_investigation",
            new_callable=AsyncMock,
            return_value=test_state,
        ):
            response = client.get("/api/investigations/CASE-GET-001")
        data = response.json()
        state = InvestigationState.model_validate(data)
        assert state.case_id == "CASE-GET-001"

    def test_identifier_matches(self) -> None:
        """Returned case_id matches the requested identifier."""
        test_state = _make_test_state()
        with patch(
            "app.api.routes.investigations._investigation_service.get_investigation",
            new_callable=AsyncMock,
            return_value=test_state,
        ):
            response = client.get("/api/investigations/CASE-GET-001")
        assert response.json()["case_id"] == "CASE-GET-001"


# ── TEST 8: Unknown investigation ────────────────────────────────────


class TestUnknownInvestigation:
    """GET /api/investigations/{case_id} for a non-existent case."""

    def test_returns_http_404(self) -> None:
        """GET returns HTTP 404 for a non-existent investigation."""
        with patch(
            "app.api.routes.investigations._investigation_service.get_investigation",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.get("/api/investigations/CASE-DOES-NOT-EXIST")
        assert response.status_code == 404

    def test_404_response_has_detail(self) -> None:
        """404 response includes a detail message."""
        with patch(
            "app.api.routes.investigations._investigation_service.get_investigation",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = client.get("/api/investigations/CASE-UNKNOWN-XYZ")
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
        assert "CASE-UNKNOWN-XYZ" in data["error"]["message"]


# ── TEST 9: Persisted state round trip ───────────────────────────────


class TestPersistedStateRoundTrip:
    """Retrieved state preserves important fields."""

    def test_case_input_survives(self) -> None:
        """case_input data is preserved in the round trip."""
        test_state = _make_test_state()
        with patch(
            "app.api.routes.investigations._investigation_service.get_investigation",
            new_callable=AsyncMock,
            return_value=test_state,
        ):
            response = client.get("/api/investigations/CASE-GET-001")
        state = InvestigationState.model_validate(response.json())
        assert state.case_input is not None
        assert len(state.case_input.transactions) == 1
        assert state.case_input.transactions[0].transaction_id == "TXN-GET-001"
        assert state.case_input.transactions[0].amount == 12_000.00

    def test_customer_profile_survives(self) -> None:
        """Customer profile data is preserved in the round trip."""
        test_state = _make_test_state()
        with patch(
            "app.api.routes.investigations._investigation_service.get_investigation",
            new_callable=AsyncMock,
            return_value=test_state,
        ):
            response = client.get("/api/investigations/CASE-GET-001")
        state = InvestigationState.model_validate(response.json())
        assert state.case_input.customer_profile is not None
        assert state.case_input.customer_profile.name == "Get Endpoint Test Customer"

    def test_current_stage_survives(self) -> None:
        """current_stage is preserved in the round trip."""
        test_state = _make_test_state()
        with patch(
            "app.api.routes.investigations._investigation_service.get_investigation",
            new_callable=AsyncMock,
            return_value=test_state,
        ):
            response = client.get("/api/investigations/CASE-GET-001")
        state = InvestigationState.model_validate(response.json())
        assert state.current_stage is not None
        assert state.current_stage.value == "INTAKE"

    def test_alert_reason_survives(self) -> None:
        """alert_reason is preserved in the round trip."""
        test_state = _make_test_state()
        with patch(
            "app.api.routes.investigations._investigation_service.get_investigation",
            new_callable=AsyncMock,
            return_value=test_state,
        ):
            response = client.get("/api/investigations/CASE-GET-001")
        state = InvestigationState.model_validate(response.json())
        assert state.case_input.alert_reason == "Automated test alert."

    @pytest.mark.asyncio
    async def test_context_intelligence_when_persisted(self) -> None:
        """context_intelligence is returned when it exists in persisted state."""
        from app.agents.context_agent import context_agent as run_agent

        test_state = _make_test_state()
        # Run context agent to populate context_intelligence
        agent_result = await run_agent(test_state)
        test_state.context_intelligence = agent_result["context_intelligence"]

        with patch(
            "app.api.routes.investigations._investigation_service.get_investigation",
            new_callable=AsyncMock,
            return_value=test_state,
        ):
            response = client.get("/api/investigations/CASE-GET-001")
        state = InvestigationState.model_validate(response.json())
        assert state.context_intelligence is not None
        assert state.context_intelligence.context_summary is not None
        assert len(state.context_intelligence.context_summary) > 0
