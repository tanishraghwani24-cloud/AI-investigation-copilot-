"""Regression tests for creating a genuinely new investigation.

``InvestigationService.create_investigation`` is idempotent per case ID, and the
default create path always rebuilds the deterministic seed=42 case. Together
that meant a "create" request reopened and re-ran the existing case instead of
making one. ``fresh=true`` allocates an unused case ID; these tests pin both
that behaviour and the unchanged default.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes import investigations as investigation_routes
from app.db.session import get_db_session
from app.main import app
from app.schemas.investigation_state import InvestigationState


async def _mock_db_session():
    yield MagicMock()


@pytest.fixture(autouse=True)
def api_client():
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db_session] = _mock_db_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)


@pytest.fixture()
def empty_store():
    """No case exists yet, and creation echoes back what it was given."""
    async def _create(case_id, case_input, _session):
        from app.schemas.investigation_state import create_initial_state
        return create_initial_state(case_id=case_id, case_input=case_input)

    with patch.object(
        investigation_routes._investigation_service, "get_investigation",
        new=AsyncMock(return_value=None),
    ), patch.object(
        investigation_routes._investigation_service, "create_investigation",
        new=AsyncMock(side_effect=_create),
    ):
        yield


def _create(client, **params) -> InvestigationState:
    response = client.post("/api/investigations", params=params)
    assert response.status_code == 200, response.text
    return InvestigationState.model_validate(response.json())


class TestFreshCreate:
    def test_two_consecutive_creates_produce_different_case_ids(self, api_client, empty_store):
        first = _create(api_client, fresh=True)
        second = _create(api_client, fresh=True)

        assert first.case_id != second.case_id

    def test_repeated_creates_stay_unique(self, api_client, empty_store):
        ids = {_create(api_client, fresh=True).case_id for _ in range(8)}

        assert len(ids) == 8

    def test_a_fresh_case_is_not_the_default_seed_case(self, api_client, empty_store):
        assert _create(api_client, fresh=True).case_id != "CASE-2025-00042"

    def test_a_fresh_case_carries_valid_case_input(self, api_client, empty_store):
        state = _create(api_client, fresh=True)

        assert state.case_input.customer_profile is not None
        assert state.case_input.customer_profile.customer_id
        assert state.case_input.transactions
        for transaction in state.case_input.transactions:
            assert transaction.transaction_id
            assert transaction.sender_account and transaction.receiver_account
            assert transaction.amount > 0
        assert state.case_input.alert_reason

    def test_fresh_cases_differ_in_content_not_just_id(self, api_client, empty_store):
        """A new seed drives the generated data, not only the identifier."""
        first, second = _create(api_client, fresh=True), _create(api_client, fresh=True)

        assert (
            first.case_input.customer_profile.customer_id
            != second.case_input.customer_profile.customer_id
        )

    def test_an_id_already_in_use_is_skipped(self, api_client):
        """Allocation re-rolls rather than handing back an existing case."""
        taken: list[str] = []

        async def _get(case_id, _session):
            # Reject the first candidate, accept the next.
            if len(taken) < 1:
                taken.append(case_id)
                return MagicMock()
            return None

        async def _create_state(case_id, case_input, _session):
            from app.schemas.investigation_state import create_initial_state
            return create_initial_state(case_id=case_id, case_input=case_input)

        with patch.object(
            investigation_routes._investigation_service, "get_investigation",
            new=AsyncMock(side_effect=_get),
        ), patch.object(
            investigation_routes._investigation_service, "create_investigation",
            new=AsyncMock(side_effect=_create_state),
        ):
            state = _create(api_client, fresh=True)

        assert taken and state.case_id != taken[0]

    def test_exhausting_every_attempt_fails_loudly(self, api_client):
        """Never silently reopen an existing case when allocation fails."""
        with patch.object(
            investigation_routes._investigation_service, "get_investigation",
            new=AsyncMock(return_value=MagicMock()),
        ):
            response = api_client.post("/api/investigations", params={"fresh": True})

        assert response.status_code == 503


class TestDefaultCreateUnchanged:
    """The pre-existing behaviour other callers depend on."""

    def test_default_create_is_still_the_deterministic_seed_case(self, api_client, empty_store):
        assert _create(api_client).case_id == "CASE-2025-00042"

    def test_default_create_is_still_repeatable(self, api_client, empty_store):
        assert _create(api_client).case_id == _create(api_client).case_id

    def test_scenario_still_selects_its_own_case(self, api_client, empty_store):
        assert _create(api_client, scenario="high-risk").case_id == "CASE-2025-00042-HIGH-RISK"

    def test_account_id_still_maps_to_its_stable_case(self, api_client, empty_store):
        """Officer Inbox opens a case per account; that must not become random."""
        # SimpleNamespace, not MagicMock: `MagicMock(name=...)` names the mock
        # itself rather than setting a `name` attribute.
        account = SimpleNamespace(account_id="ACC-MOCK-001", customer_id="CUST-MOCK-001")
        customer = SimpleNamespace(
            customer_id="CUST-MOCK-001", name="Test Customer", email=None, phone=None,
            address=None, date_of_birth=None, created_at=None, risk_rating="HIGH",
            occupation=None, nationality=None,
        )
        with patch("app.api.routes.investigations.MockBankService") as service:
            instance = service.return_value
            instance.get_account = AsyncMock(return_value=account)
            instance.get_customer = AsyncMock(return_value=customer)
            instance.get_account_transactions = AsyncMock(return_value=[])

            first = _create(api_client, account_id="ACC-MOCK-001")
            second = _create(api_client, account_id="ACC-MOCK-001")

        assert first.case_id == second.case_id == "CASE-MOCK--001"
