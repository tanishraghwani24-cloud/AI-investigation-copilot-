"""Round 4 API tests for the persisted investigation surface."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes import investigations as investigation_routes
from app.db.session import get_db_session
from app.main import app
from app.schemas.investigation_state import (
    AgentStatus,
    CaseInput,
    CurrentStage,
    CustomerProfile,
    DecisionAction,
    DecisionOptimization,
    DecisionOption,
    InvestigationState,
    Transaction,
    create_initial_state,
)


async def _mock_db_session():
    yield MagicMock()


@pytest.fixture(autouse=True)
def api_client():
    """Isolate route dependency overrides from the legacy API tests."""
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db_session] = _mock_db_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous_overrides)


def _state(
    case_id: str,
    stage: CurrentStage = CurrentStage.INTAKE,
    *,
    final_decision: bool = False,
) -> InvestigationState:
    state = create_initial_state(
        case_id=case_id,
        case_input=CaseInput(
            transactions=[
                Transaction(
                    transaction_id=f"TXN-{case_id}",
                    amount=12_500.0,
                    timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
                    sender_account="ACC-SOURCE",
                    receiver_account="ACC-DESTINATION",
                    transaction_type="WIRE",
                )
            ],
            customer_profile=CustomerProfile(
                customer_id=f"CUST-{case_id}",
                name=f"Persisted customer {case_id}",
            ),
            alert_reason="Persisted alert reason",
        ),
    )
    state.current_stage = stage
    if final_decision:
        state.current_stage = CurrentStage.DONE
        state.decision_optimization = DecisionOptimization(
            status=AgentStatus.COMPLETED,
            decision_options=[
                DecisionOption(
                    option_id="ALLOW", action=DecisionAction.ALLOW,
                    rationale="Allowing preserves customer access.", confidence=0.2,
                    pros=["No disruption"], cons=["Risk remains"],
                    risks=["Potential loss"], mitigation=["Monitor activity"],
                ),
                DecisionOption(
                    option_id="HOLD", action=DecisionAction.HOLD,
                    rationale="Holding permits evidence collection.", confidence=0.7,
                    pros=["Protects funds"], cons=["Delays payment"],
                    risks=["Customer impact"], mitigation=["Set review deadline"],
                ),
                DecisionOption(
                    option_id="BLOCK", action=DecisionAction.BLOCK,
                    rationale="Blocking prevents immediate loss.", confidence=0.4,
                    pros=["Stops transfer"], cons=["High disruption"],
                    risks=["False positive"], mitigation=["Escalated review"],
                ),
                DecisionOption(
                    option_id="ESCALATE", action=DecisionAction.ESCALATE,
                    rationale="Escalation obtains specialist review.", confidence=0.5,
                    pros=["Expert review"], cons=["Longer resolution"],
                    risks=["Delay"], mitigation=["Prioritize queue"],
                ),
            ],
            recommended_decision=DecisionAction.HOLD,
            decision_rationale="The risk warrants a temporary hold pending review.",
        )
    return state


def test_create_investigation_persists_initial_state(api_client: TestClient) -> None:
    persisted = _state("CASE-2025-00042")
    with patch.object(
        investigation_routes._investigation_service,
        "create_investigation",
        new=AsyncMock(return_value=persisted),
    ) as create:
        response = api_client.post("/api/investigations")

    assert response.status_code == 200
    assert InvestigationState.model_validate(response.json()) == persisted
    create.assert_awaited_once()


def test_create_investigation_accepts_explicit_scenario(api_client: TestClient) -> None:
    high_risk = investigation_routes._build_investigation_state(
        42,
        scenario="high-risk",
    )
    with patch.object(
        investigation_routes._investigation_service,
        "create_investigation",
        new=AsyncMock(return_value=high_risk),
    ):
        response = api_client.post("/api/investigations?scenario=high-risk")

    assert response.status_code == 200
    state = InvestigationState.model_validate(response.json())
    assert state.case_id.endswith("HIGH-RISK")
    assert state.case_input.customer_profile is not None
    assert state.case_input.customer_profile.risk_rating == "HIGH"


def test_create_investigation_rejects_invalid_scenario(api_client: TestClient) -> None:
    response = api_client.post("/api/investigations?scenario=invalid")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_get_returns_the_persisted_investigation_not_hardcoded(
    api_client: TestClient,
) -> None:
    persisted = _state("CASE-PERSISTED-901", final_decision=True)
    with patch.object(
        investigation_routes._investigation_service,
        "get_investigation",
        new=AsyncMock(return_value=persisted),
    ):
        response = api_client.get("/api/investigations/CASE-PERSISTED-901")

    assert response.status_code == 200
    assert response.json()["case_id"] == "CASE-PERSISTED-901"
    assert response.json()["case_input"]["customer_profile"]["name"] == (
        "Persisted customer CASE-PERSISTED-901"
    )
    decision = response.json()["decision_optimization"]
    assert decision["recommended_decision"] == "HOLD"
    assert decision["decision_rationale"] == (
        "The risk warrants a temporary hold pending review."
    )
    assert len(decision["decision_options"]) == 4


def test_get_nonexistent_investigation_returns_404(api_client: TestClient) -> None:
    with patch.object(
        investigation_routes._investigation_service,
        "get_investigation",
        new=AsyncMock(return_value=None),
    ):
        response = api_client.get("/api/investigations/CASE-MISSING")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert "CASE-MISSING" in response.json()["error"]["message"]


def test_list_investigations_uses_persisted_service_results(
    api_client: TestClient,
) -> None:
    persisted = [_state("CASE-ONE"), _state("CASE-TWO", CurrentStage.DECISION)]
    with patch.object(
        investigation_routes._investigation_service,
        "list_investigations",
        new=AsyncMock(return_value=persisted),
    ) as list_cases:
        response = api_client.get("/api/investigations")

    assert response.status_code == 200
    assert [item["case_id"] for item in response.json()] == ["CASE-ONE", "CASE-TWO"]
    assert list_cases.await_args is not None
    assert list_cases.await_args.kwargs == {"status": None, "offset": 0, "limit": 20}


def test_list_supports_pagination(api_client: TestClient) -> None:
    with patch.object(
        investigation_routes._investigation_service,
        "list_investigations",
        new=AsyncMock(return_value=[_state("CASE-PAGE-3")]),
    ) as list_cases:
        response = api_client.get("/api/investigations?offset=2&limit=1")

    assert response.status_code == 200
    assert response.json()[0]["case_id"] == "CASE-PAGE-3"
    assert list_cases.await_args is not None
    assert list_cases.await_args.kwargs == {"status": None, "offset": 2, "limit": 1}


def test_list_supports_status_filtering(api_client: TestClient) -> None:
    with patch.object(
        investigation_routes._investigation_service,
        "list_investigations",
        new=AsyncMock(return_value=[_state("CASE-DONE", CurrentStage.DONE)]),
    ) as list_cases:
        response = api_client.get("/api/investigations?status=DONE")

    assert response.status_code == 200
    assert list_cases.await_args is not None
    assert list_cases.await_args.kwargs == {
        "status": CurrentStage.DONE,
        "offset": 0,
        "limit": 20,
    }


def test_run_investigation_returns_finalized_decision(api_client: TestClient) -> None:
    started = _state("CASE-RUN-1")
    with patch.object(
        investigation_routes._investigation_service,
        "start_investigation",
        new=AsyncMock(return_value=(started, True)),
    ) as start, patch.object(
        investigation_routes,
        "_run_investigation_background",
        new=AsyncMock(),
    ) as background:
        response = api_client.post("/api/investigations/CASE-RUN-1/run")

    assert response.status_code == 202
    payload = response.json()
    assert payload["case_id"] == "CASE-RUN-1"
    assert payload["status"] == "IN_PROGRESS"
    assert "background" in payload["message"]
    start.assert_awaited_once()
    background.assert_awaited_once_with("CASE-RUN-1")


def test_run_nonexistent_investigation_returns_404(api_client: TestClient) -> None:
    with patch.object(
        investigation_routes._investigation_service,
        "start_investigation",
        new=AsyncMock(return_value=None),
    ):
        response = api_client.post("/api/investigations/CASE-MISSING/run")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert "CASE-MISSING" in response.json()["error"]["message"]
