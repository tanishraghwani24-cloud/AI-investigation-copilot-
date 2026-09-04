"""Tests for the alert inbox and the alert -> investigation escalation."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes import alerts as alert_routes
from app.api.routes import investigations as investigation_routes
from app.db.session import get_db_session
from app.main import app
from app.models.mock_bank import MockBankAlert
from app.schemas.investigation_state import CaseInput, create_initial_state

_NOW = datetime(2026, 9, 4, 10, 0, tzinfo=timezone.utc)


def _alert(alert_id="ALERT-AAAA", *, status="OPEN", case_id=None, age=0) -> MockBankAlert:
    return MockBankAlert(
        alert_id=alert_id,
        transaction_id=f"TXN-SIM-{alert_id[-4:]}",
        account_id="ACC-MOCK-001",
        customer_id="CUST-MOCK-001",
        reason="Large transaction of 48,000.00 (WIRE) detected.",
        severity="HIGH",
        risk_score=0.48,
        status=status,
        case_id=case_id,
        created_at=_NOW - timedelta(minutes=age),
    )


def _txn(transaction_id="TXN-SIM-AAAA", amount=48000.0):
    return SimpleNamespace(
        transaction_id=transaction_id, account_id="ACC-MOCK-001",
        receiver_account_id="ACC-999999", amount=amount, currency="USD",
        transaction_type="WIRE", channel="ONLINE", timestamp=_NOW,
        description="Cross-border settlement", location="Dubai, AE", status="COMPLETED",
    )


def _customer():
    return SimpleNamespace(
        customer_id="CUST-MOCK-001", name="Test Customer", email=None, phone=None,
        address=None, date_of_birth=None, risk_rating="HIGH", occupation=None,
        nationality=None,
    )


class _Session:
    """Async session stub returning a scripted list of alerts."""

    def __init__(self, alerts):
        self.alerts = alerts
        self.committed = False

    async def execute(self, _stmt):
        result = MagicMock()
        result.scalars.return_value.all.return_value = self.alerts
        result.scalar_one_or_none.return_value = self.alerts[0] if self.alerts else None
        return result

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass


def _service():
    """Investigation service stub that echoes back what it is asked to create."""
    async def _create(case_id, case_input, _session):
        return create_initial_state(case_id=case_id, case_input=case_input)

    service = MagicMock()
    service.create_investigation = AsyncMock(side_effect=_create)
    service.start_investigation = AsyncMock(
        return_value=(create_initial_state(case_id="X", case_input=CaseInput()), False),
    )
    return service


@pytest.fixture()
def client_for():
    """Build a TestClient whose DB session yields the supplied alerts."""
    previous = app.dependency_overrides.copy()

    def _factory(alerts):
        session = _Session(alerts)

        async def _session_dep():
            yield session

        app.dependency_overrides[get_db_session] = _session_dep
        return TestClient(app), session

    yield _factory
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)


@pytest.fixture(autouse=True)
def mock_bank_lookups():
    with patch.object(alert_routes._mock_bank, "get_transaction", new=AsyncMock(return_value=_txn())), \
         patch.object(alert_routes._mock_bank, "get_customer", new=AsyncMock(return_value=_customer())), \
         patch.object(
             alert_routes._mock_bank, "get_account_transactions",
             new=AsyncMock(return_value=[_txn()]),
         ):
        yield


class TestInbox:
    def test_officer_inbox_receives_alerts(self, client_for):
        client, _ = client_for([_alert("ALERT-0001"), _alert("ALERT-0002")])

        body = client.get("/api/alerts").json()

        assert [a["alert_id"] for a in body] == ["ALERT-0001", "ALERT-0002"]

    def test_alerts_carry_the_detail_the_inbox_shows(self, client_for):
        client, _ = client_for([_alert("ALERT-0001")])

        alert = client.get("/api/alerts").json()[0]

        assert alert["reason"].startswith("Large transaction")
        assert alert["severity"] == "HIGH"
        assert alert["amount"] == 48000.0
        assert alert["transaction_type"] == "WIRE"
        assert alert["customer_name"] == "Test Customer"
        assert alert["status"] == "OPEN"

    def test_newly_generated_alerts_appear_on_the_next_poll(self, client_for):
        client, session = client_for([_alert("ALERT-0001")])
        assert len(client.get("/api/alerts").json()) == 1

        session.alerts = [_alert("ALERT-0002"), _alert("ALERT-0001")]

        assert [a["alert_id"] for a in client.get("/api/alerts").json()] == [
            "ALERT-0002", "ALERT-0001",
        ]

    def test_an_empty_inbox_is_not_an_error(self, client_for):
        client, _ = client_for([])

        response = client.get("/api/alerts")

        assert response.status_code == 200 and response.json() == []


class TestEscalation:
    def test_investigating_an_alert_creates_a_case_named_for_that_alert(self, client_for):
        client, _ = client_for([_alert("ALERT-BEEF")])

        with patch.object(investigation_routes, "_investigation_service", _service()):
            body = client.post("/api/alerts/ALERT-BEEF/investigate").json()

        assert body["case_id"] == "CASE-ALERT-BEEF"
        assert body["created"] is True
        assert body["alert_id"] == "ALERT-BEEF"

    def test_two_different_alerts_create_two_different_cases(self, client_for):
        service = _service()
        cases = []
        for alert_id in ("ALERT-0001", "ALERT-0002"):
            client, _ = client_for([_alert(alert_id)])
            with patch.object(investigation_routes, "_investigation_service", service):
                cases.append(
                    client.post(f"/api/alerts/{alert_id}/investigate").json()["case_id"]
                )

        assert cases[0] != cases[1]
        assert len(set(cases)) == 2

    def test_the_case_id_is_never_the_default_seed_case(self, client_for):
        client, _ = client_for([_alert("ALERT-BEEF")])

        with patch.object(investigation_routes, "_investigation_service", _service()):
            case_id = client.post("/api/alerts/ALERT-BEEF/investigate").json()["case_id"]

        assert case_id != "CASE-2025-00042"

    def test_the_same_alert_cannot_create_a_duplicate_investigation(self, client_for):
        """A second escalation returns the existing case and creates nothing."""
        client, _ = client_for([
            _alert("ALERT-DUPE", status="INVESTIGATING", case_id="CASE-ALERT-DUPE"),
        ])
        service = _service()

        with patch.object(investigation_routes, "_investigation_service", service):
            body = client.post("/api/alerts/ALERT-DUPE/investigate").json()

        assert body["case_id"] == "CASE-ALERT-DUPE"
        assert body["created"] is False
        service.create_investigation.assert_not_awaited()

    def test_escalation_marks_the_alert_in_backend_state(self, client_for):
        alert = _alert("ALERT-BEEF")
        client, session = client_for([alert])

        with patch.object(investigation_routes, "_investigation_service", _service()):
            client.post("/api/alerts/ALERT-BEEF/investigate")

        assert alert.status == "INVESTIGATING"
        assert alert.case_id == "CASE-ALERT-BEEF"
        assert session.committed

    def test_the_case_is_built_from_the_alerting_transaction(self, client_for):
        client, _ = client_for([_alert("ALERT-BEEF")])
        service = _service()

        with patch.object(investigation_routes, "_investigation_service", service):
            client.post("/api/alerts/ALERT-BEEF/investigate")

        case_input = service.create_investigation.await_args.args[1]
        assert case_input.transactions[0].transaction_id == "TXN-SIM-AAAA"
        assert case_input.alert_reason.startswith("Large transaction")
        assert case_input.customer_profile.customer_id == "CUST-MOCK-001"

    def test_an_unknown_alert_is_a_404(self, client_for):
        client, _ = client_for([])

        assert client.post("/api/alerts/ALERT-NOPE/investigate").status_code == 404


class TestAlertInvestigationLink:
    def test_a_case_can_be_traced_back_to_its_alert(self, client_for):
        client, _ = client_for([
            _alert("ALERT-LINK", status="INVESTIGATING", case_id="CASE-ALERT-LINK"),
        ])

        body = client.get("/api/alerts/by-case/CASE-ALERT-LINK").json()

        assert body["alert_id"] == "ALERT-LINK"
        assert body["transaction_id"] == "TXN-SIM-LINK"
        assert body["case_id"] == "CASE-ALERT-LINK"

    def test_a_case_with_no_alert_is_a_404(self, client_for):
        client, _ = client_for([])

        assert client.get("/api/alerts/by-case/CASE-MANUAL").status_code == 404
