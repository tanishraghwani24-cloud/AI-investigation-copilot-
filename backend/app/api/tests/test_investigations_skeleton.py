"""Tests for the POST /api/investigations skeleton endpoint.

Verifies Round 1 requirements:
- FastAPI app starts and serves requests
- POST /api/investigations returns HTTP 200 with valid InvestigationState
- GET /api/health continues to work
- No database or external dependencies required
"""

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.investigation_state import InvestigationState


client = TestClient(app)


class TestInvestigationsEndpoint:
    """POST /api/investigations endpoint tests."""

    def test_returns_http_200(self) -> None:
        """Endpoint returns HTTP 200."""
        response = client.post("/api/investigations")
        assert response.status_code == 200

    def test_returns_valid_json(self) -> None:
        """Endpoint returns parseable JSON."""
        response = client.post("/api/investigations")
        data = response.json()
        assert isinstance(data, dict)

    def test_validates_against_investigation_state(self) -> None:
        """Response validates against the Pydantic InvestigationState schema."""
        response = client.post("/api/investigations")
        data = response.json()
        state = InvestigationState.model_validate(data)
        assert state.case_id is not None
        assert len(state.case_id) > 0

    def test_has_case_input(self) -> None:
        """Response includes a populated case_input."""
        response = client.post("/api/investigations")
        state = InvestigationState.model_validate(response.json())
        assert state.case_input is not None
        assert len(state.case_input.transactions) > 0

    def test_has_customer_profile(self) -> None:
        """Response includes customer profile data."""
        response = client.post("/api/investigations")
        state = InvestigationState.model_validate(response.json())
        assert state.case_input.customer_profile is not None
        assert len(state.case_input.customer_profile.name) > 0

    def test_has_agent_output_placeholders(self) -> None:
        """Response includes agent output sections (placeholder data)."""
        response = client.post("/api/investigations")
        state = InvestigationState.model_validate(response.json())
        assert state.context_intelligence is not None
        assert state.investigation_reasoning is not None
        assert state.evidence_compliance_validation is not None
        assert state.decision_optimization is not None
        assert state.investigation_report is not None

    def test_is_deterministic(self) -> None:
        """Two consecutive calls return identical data."""
        r1 = client.post("/api/investigations")
        r2 = client.post("/api/investigations")
        assert r1.json() == r2.json()

    def test_no_database_required(self) -> None:
        """Endpoint works without any database configuration."""
        # If we got here, the TestClient started the app successfully
        # without any database — this is the assertion.
        response = client.post("/api/investigations")
        assert response.status_code == 200


class TestHealthEndpoint:
    """Ensure existing /api/health still works after changes."""

    def test_health_returns_200(self) -> None:
        """GET /api/health returns HTTP 200."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_returns_ok(self) -> None:
        """GET /api/health response contains status ok."""
        response = client.get("/api/health")
        data = response.json()
        assert data["status"] == "ok"
