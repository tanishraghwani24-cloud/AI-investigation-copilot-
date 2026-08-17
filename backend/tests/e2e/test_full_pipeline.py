import asyncio
from unittest.mock import patch

import httpx
import pytest

from app.main import app
from app.schemas.investigation_state import CurrentStage
from app.models.investigation import InvestigationCase
from app.models.document import DocumentRecord

@pytest.fixture
def mock_db():
    fake_db = {}
    fake_docs = {}

    async def fake_inv_create(self, session, case_id, state_json):
        record = InvestigationCase(case_id=case_id, status=state_json.get("current_stage", "INTAKE"), state_json=state_json)
        fake_db[case_id] = record
        return record

    async def fake_inv_get(self, session, case_id):
        return fake_db.get(case_id)

    async def fake_inv_update(self, session, case_id, state_json):
        if case_id in fake_db:
            fake_db[case_id].state_json = state_json
            fake_db[case_id].status = state_json.get("current_stage", fake_db[case_id].status)
            return fake_db[case_id]
        return None

    async def fake_doc_create(self, session, case_id, document_data):
        doc_id = document_data.get("document_id", "DOC-123")
        record = DocumentRecord(case_id=case_id, **document_data)
        fake_docs[doc_id] = record
        return record

    async def fake_doc_list(self, session, case_id):
        return [doc for doc in fake_docs.values() if doc.case_id == case_id]

    from app.api.routes.documents import _KNOWN_CASE_IDS
    _KNOWN_CASE_IDS.update({
        "CASE-2025-00042-HIGH-RISK",
        "CASE-2025-00042-LOW-RISK",
        "CASE-2025-00042-MISSING-DATA"
    })

    with patch("app.db.repository.InvestigationRepository.create", fake_inv_create), \
         patch("app.db.repository.InvestigationRepository.get_by_case_id", fake_inv_get), \
         patch("app.db.repository.InvestigationRepository.update_state", fake_inv_update), \
         patch("app.db.repository.DocumentRepository.create", fake_doc_create), \
         patch("app.db.repository.DocumentRepository.list_by_case", fake_doc_list):
        yield fake_db

async def _run_e2e_scenario(client: httpx.AsyncClient, scenario_name: str, expected_case_id: str):
    # 1. Create Investigation
    resp = await client.post(f"/api/investigations?scenario={scenario_name}")
    assert resp.status_code == 200, f"Failed to create investigation: {resp.text}"
    data = resp.json()
    case_id = data["case_id"]
    assert case_id == expected_case_id

    # 2. Upload dummy PDF document
    dummy_pdf = b"%PDF-1.4\n%EOF"  # minimal valid PDF signature
    files = {"file": ("test_doc.pdf", dummy_pdf, "application/pdf")}
    data_payload = {"document_type": "INVOICE"}

    doc_resp = await client.post(
        f"/api/investigations/{case_id}/documents",
        files=files,
        data=data_payload,
    )
    assert doc_resp.status_code == 200, f"Failed to upload document: {doc_resp.text}"

    # 3. Trigger background execution
    trigger_task = asyncio.create_task(client.post(f"/api/investigations/{case_id}/run"))

    # Give it a moment to start
    await asyncio.sleep(1)

    # 4. Poll until completion
    max_retries = 60
    final_state = None

    try:
        for _ in range(max_retries):
            poll_resp = await client.get(f"/api/investigations/{case_id}")
            assert poll_resp.status_code == 200
            final_state = poll_resp.json()
            if final_state["current_stage"] in [CurrentStage.DONE.value, "FAILED"]:
                break
            await asyncio.sleep(2)

        # 5. Verify the investigation reached DONE successfully
        assert final_state is not None
        assert final_state["current_stage"] == CurrentStage.DONE.value, f"Investigation failed or timed out: {final_state.get('errors')}"

        # 6. Verify final data is persisted
        assert final_state.get("decision_optimization") is not None
        assert final_state["decision_optimization"].get("status") == "COMPLETED"
        assert final_state.get("investigation_report") is not None
        assert final_state["investigation_report"].get("status") == "COMPLETED"
    finally:
        await trigger_task


@pytest.mark.asyncio
async def test_full_pipeline_happy_path_default(mock_db):
    """Verify that the default scenario executes successfully."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await _run_e2e_scenario(client, "default", "CASE-2025-00042")


@pytest.mark.asyncio
async def test_full_pipeline_high_risk_scenario(mock_db):
    """Verify that the high-risk scenario executes successfully."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await _run_e2e_scenario(client, "high-risk", "CASE-2025-00042-HIGH-RISK")


@pytest.mark.asyncio
async def test_full_pipeline_low_risk_scenario(mock_db):
    """Verify that the low-risk scenario executes successfully."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await _run_e2e_scenario(client, "low-risk", "CASE-2025-00042-LOW-RISK")


@pytest.mark.asyncio
async def test_full_pipeline_missing_data_scenario(mock_db):
    """Verify that the missing-data scenario executes successfully."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await _run_e2e_scenario(client, "missing-data", "CASE-2025-00042-MISSING-DATA")


@pytest.mark.asyncio
async def test_full_pipeline_failure_path(mock_db):
    """Verify that background execution failures are gracefully caught and persisted."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create a new case using a different scenario to avoid collision with happy-path
        resp = await client.post("/api/investigations?scenario=high-risk")
        assert resp.status_code == 200
        case_id = resp.json()["case_id"]

        # Mock the workflow to throw an error immediately upon background execution
        with patch("app.api.routes.investigations._investigation_service.run_investigation", side_effect=ValueError("Mocked Background Failure")):
            trigger_task = asyncio.create_task(client.post(f"/api/investigations/{case_id}/run"))

            await asyncio.sleep(1)

            max_retries = 10
            final_state = None
            try:
                for _ in range(max_retries):
                    poll_resp = await client.get(f"/api/investigations/{case_id}")
                    assert poll_resp.status_code == 200
                    final_state = poll_resp.json()
                    if final_state["errors"]:
                        break
                    await asyncio.sleep(1)

                assert final_state is not None
                assert len(final_state["errors"]) > 0
                assert final_state["errors"][0]["message"] == "Background execution failed: Mocked Background Failure"
            finally:
                try:
                    await trigger_task
                except ValueError:
                    pass
