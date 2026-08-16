"""Unit tests for Supabase-compatible report persistence without credentials."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.investigation_state import AgentStatus, InvestigationReport
from app.services.report_storage_service import ReportStorageError, ReportStorageService


def _report():
    return InvestigationReport(status=AgentStatus.COMPLETED, executive_summary="Case summary", detailed_narrative="Detailed report", generated_at=datetime(2026, 1, 1))


def _service_and_repo(url="https://storage.example/report.json"):
    bucket = MagicMock()
    bucket.get_public_url.return_value = {"publicUrl": url}
    client = MagicMock()
    client.storage.from_.return_value = bucket
    repo = MagicMock()
    repo.get_by_case_id = AsyncMock(return_value=MagicMock(state_json={"case_id": "CASE-1", "current_stage": "DONE"}))
    repo.update_state = AsyncMock(return_value=MagicMock())
    return ReportStorageService(client, repo, "reports"), bucket, repo


def test_serialization_and_case_scoped_paths_are_stable():
    payload = ReportStorageService.serialize_report(_report())

    assert json.loads(payload)["executive_summary"] == "Case summary"
    assert ReportStorageService.storage_path("CASE/ONE") == "investigations/CASE%2FONE/final-report.json"
    assert ReportStorageService.storage_path("CASE-1") != ReportStorageService.storage_path("CASE-2")
    assert ReportStorageService.storage_path("CASE-1") == ReportStorageService.storage_path("CASE-1")


@pytest.mark.asyncio
async def test_uploads_report_gets_url_and_links_existing_state_json():
    service, bucket, repo = _service_and_repo()

    result = await service.store_report("CASE-1", _report(), MagicMock())

    bucket.upload.assert_called_once()
    path, artifact, options = bucket.upload.call_args.args
    assert path == "investigations/CASE-1/final-report.json"
    assert json.loads(artifact)["detailed_narrative"] == "Detailed report"
    assert options == {"content-type": "application/json", "upsert": "true"}
    bucket.get_public_url.assert_called_once_with(path)
    assert result.url == "https://storage.example/report.json"
    assert result.reference == "reports:investigations/CASE-1/final-report.json"
    saved_state = repo.update_state.call_args.args[2]
    assert saved_state["report_storage"]["url"] == result.url
    assert saved_state["report_storage"]["reference"] == result.reference


@pytest.mark.asyncio
async def test_storage_failure_is_wrapped_and_does_not_require_credentials():
    service, bucket, repo = _service_and_repo()
    bucket.upload.side_effect = RuntimeError("storage unavailable")

    with pytest.raises(ReportStorageError, match="Failed to upload report"):
        await service.store_report("CASE-1", _report(), MagicMock())
    repo.get_by_case_id.assert_not_called()


@pytest.mark.asyncio
async def test_database_link_failure_is_wrapped_after_upload():
    service, bucket, repo = _service_and_repo()
    repo.update_state = AsyncMock(side_effect=RuntimeError("database unavailable"))

    with pytest.raises(ReportStorageError, match="Failed to link report"):
        await service.store_report("CASE-1", _report(), MagicMock())
    bucket.upload.assert_called_once()


@pytest.mark.asyncio
async def test_missing_case_is_reported_as_database_link_failure():
    service, _, repo = _service_and_repo()
    repo.get_by_case_id = AsyncMock(return_value=None)

    with pytest.raises(ReportStorageError, match="was not found"):
        await service.store_report("CASE-1", _report(), MagicMock())
