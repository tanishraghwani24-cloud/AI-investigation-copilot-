"""Round 7 validation and API error-envelope tests."""

import io
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes import investigations as investigation_routes
from app.db.session import get_db_session
from app.main import app
from app.schemas.investigation_state import (
    CaseInput,
    CurrentStage,
    CustomerProfile,
    InvestigationState,
    Transaction,
    create_initial_state,
)


async def _mock_db_session():
    yield MagicMock()


@pytest.fixture
def api_client():
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db_session] = _mock_db_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous_overrides)


def _state(case_id: str = "CASE-2025-00042") -> InvestigationState:
    return create_initial_state(
        case_id=case_id,
        case_input=CaseInput(
            transactions=[
                Transaction(
                    transaction_id="TXN-VALID-001",
                    amount=1250.0,
                    timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
                    sender_account="ACC-SOURCE",
                    receiver_account="ACC-DESTINATION",
                    transaction_type="WIRE",
                )
            ],
            customer_profile=CustomerProfile(
                customer_id="CUST-VALID-001",
                name="Validation Test Customer",
            ),
            alert_reason="Validation test alert",
        ),
    )


def _assert_error_envelope(
    response,
    *,
    code: str | None = None,
) -> dict:
    payload = response.json()
    assert set(payload.keys()) == {"error"}
    assert set(payload["error"].keys()) == {"code", "message", "details"}
    assert isinstance(payload["error"]["code"], str)
    assert isinstance(payload["error"]["message"], str)
    if code is not None:
        assert payload["error"]["code"] == code
    return payload


def test_missing_required_upload_file_returns_validation_envelope(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/api/investigations/CASE-2025-00042/documents",
        data={"document_type": "INVOICE"},
    )

    assert response.status_code == 422
    payload = _assert_error_envelope(response, code="VALIDATION_ERROR")
    assert any(
        detail["loc"][-1] == "file"
        for detail in payload["error"]["details"]
    )


def test_invalid_document_type_form_value_returns_field_details(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/api/investigations/CASE-2025-00042/documents",
        files={"file": ("report.txt", io.BytesIO(b"hello"), "text/plain")},
        data={"document_type": " "},
    )

    assert response.status_code == 422
    payload = _assert_error_envelope(response, code="VALIDATION_ERROR")
    assert any(
        detail["loc"][-1] == "document_type"
        for detail in payload["error"]["details"]
    )


def test_invalid_scenario_enum_returns_validation_envelope(
    api_client: TestClient,
) -> None:
    response = api_client.post("/api/investigations?scenario=not-a-scenario")

    assert response.status_code == 422
    payload = _assert_error_envelope(response, code="VALIDATION_ERROR")
    assert any(
        detail["loc"] == ["query", "scenario"]
        for detail in payload["error"]["details"]
    )


def test_invalid_status_enum_returns_validation_envelope(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/investigations?status=ARCHIVED")

    assert response.status_code == 422
    payload = _assert_error_envelope(response, code="VALIDATION_ERROR")
    assert any(
        detail["loc"] == ["query", "status"]
        for detail in payload["error"]["details"]
    )


def test_invalid_pagination_query_parameter_returns_validation_envelope(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/investigations?offset=-1&limit=0")

    assert response.status_code == 422
    payload = _assert_error_envelope(response, code="VALIDATION_ERROR")
    locations = {tuple(detail["loc"]) for detail in payload["error"]["details"]}
    assert ("query", "offset") in locations
    assert ("query", "limit") in locations


def test_invalid_case_id_path_parameter_returns_validation_envelope(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/investigations/CASE 2025 00042")

    assert response.status_code == 422
    payload = _assert_error_envelope(response, code="VALIDATION_ERROR")
    assert any(
        detail["loc"] == ["path", "case_id"]
        for detail in payload["error"]["details"]
    )


def test_valid_nonexistent_investigation_returns_not_found_envelope(
    api_client: TestClient,
) -> None:
    with patch.object(
        investigation_routes._investigation_service,
        "get_investigation",
        new=AsyncMock(return_value=None),
    ):
        response = api_client.get("/api/investigations/CASE-NOT-FOUND-777")

    assert response.status_code == 404
    payload = _assert_error_envelope(response, code="NOT_FOUND")
    assert "CASE-NOT-FOUND-777" in payload["error"]["message"]


def test_representative_valid_list_request_still_works(
    api_client: TestClient,
) -> None:
    persisted = [_state("CASE-VALID-LIST")]
    with patch.object(
        investigation_routes._investigation_service,
        "list_investigations",
        new=AsyncMock(return_value=persisted),
    ) as list_investigations:
        response = api_client.get("/api/investigations?status=INTAKE&offset=0&limit=1")

    assert response.status_code == 200
    assert response.json()[0]["case_id"] == "CASE-VALID-LIST"
    list_investigations.assert_awaited_once()
    assert list_investigations.await_args is not None
    assert list_investigations.await_args.kwargs == {
        "status": CurrentStage.INTAKE,
        "offset": 0,
        "limit": 1,
    }


def test_error_shape_is_consistent_across_endpoint_categories(
    api_client: TestClient,
) -> None:
    validation_response = api_client.get("/api/investigations?limit=101")
    not_found_response = api_client.get(
        "/api/investigations/CASE-DOES-NOT-EXIST/documents",
    )

    assert validation_response.status_code == 422
    assert not_found_response.status_code == 404
    validation_payload = _assert_error_envelope(
        validation_response,
        code="VALIDATION_ERROR",
    )
    not_found_payload = _assert_error_envelope(
        not_found_response,
        code="NOT_FOUND",
    )
    assert validation_payload.keys() == not_found_payload.keys()
    assert validation_payload["error"].keys() == not_found_payload["error"].keys()


def test_unexpected_server_error_returns_safe_envelope() -> None:
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db_session] = _mock_db_session
    try:
        with patch.object(
            investigation_routes._investigation_service,
            "list_investigations",
            new=AsyncMock(side_effect=RuntimeError("database password leaked")),
        ), TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/api/investigations")
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)

    assert response.status_code == 500
    payload = _assert_error_envelope(response, code="INTERNAL_SERVER_ERROR")
    assert payload["error"]["message"] == "An unexpected server error occurred"
    assert payload["error"]["details"] is None
    assert "database password leaked" not in response.text
