"""Persistence of final investigation reports in Supabase Storage.

The application currently persists investigations as ``state_json`` through
``InvestigationRepository``.  This service deliberately uses that established
mechanism to link the report's Storage URL/reference without requiring a
schema migration.  A Supabase-compatible client is injected by the caller so
unit tests and local code do not need credentials or the Supabase SDK.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import quote

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository import InvestigationRepository
from app.schemas.investigation_state import InvestigationReport


DEFAULT_REPORT_BUCKET = "investigation-reports"


class ReportStorageError(Exception):
    """Raised when report upload or report-to-case linkage cannot complete."""


@dataclass(frozen=True)
class StoredReport:
    """Stable result of persisting a report artifact."""

    case_id: str
    bucket: str
    path: str
    reference: str
    url: str | None


class ReportStorageService:
    """Store a report artifact and link its retrievable reference to a case."""

    def __init__(
        self,
        storage_client: Any,
        investigation_repo: InvestigationRepository | None = None,
        bucket_name: str | None = None,
    ) -> None:
        self._storage_client = storage_client
        self._repo = investigation_repo or InvestigationRepository()
        # The project has no Supabase Storage setting yet.  This optional
        # environment override follows its existing Settings/.env convention
        # without placing credentials in source code.
        self._bucket_name = bucket_name or os.getenv(
            "SUPABASE_STORAGE_BUCKET", DEFAULT_REPORT_BUCKET
        )

    @staticmethod
    def storage_path(case_id: str) -> str:
        """Return a deterministic, safely case-scoped artifact path.

        Re-generating a report for the same case replaces that case's current
        final report; quoting prevents a case ID from escaping its directory.
        """
        if not case_id:
            raise ValueError("case_id is required to store a report")
        return f"investigations/{quote(case_id, safe='-_.')}/final-report.json"

    @staticmethod
    def serialize_report(report: InvestigationReport | Mapping[str, Any]) -> bytes:
        """Serialize a report to stable UTF-8 JSON suitable for Storage."""
        if isinstance(report, InvestigationReport):
            payload = report.model_dump(mode="json")
        elif isinstance(report, Mapping):
            payload = dict(report)
        else:
            raise TypeError("report must be an InvestigationReport or mapping")
        return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8")

    @staticmethod
    def _extract_url(value: Any) -> str | None:
        """Accept the public-URL shapes returned by common Supabase clients."""
        if isinstance(value, str):
            return value
        if isinstance(value, Mapping):
            for key in ("publicUrl", "public_url", "signedURL", "signed_url", "url"):
                if value.get(key):
                    return str(value[key])
        for attribute in ("public_url", "publicUrl", "signed_url", "signedURL", "url"):
            candidate = getattr(value, attribute, None)
            if candidate:
                return str(candidate)
        return None

    async def store_report(
        self,
        case_id: str,
        report: InvestigationReport | Mapping[str, Any],
        session: AsyncSession,
    ) -> StoredReport:
        """Upload *report* then persist the URL/reference in existing state JSON."""
        path = self.storage_path(case_id)
        artifact = self.serialize_report(report)
        reference = f"{self._bucket_name}:{path}"
        try:
            bucket = self._storage_client.storage.from_(self._bucket_name)
            bucket.upload(path, artifact, {"content-type": "application/json", "upsert": "true"})
            url = self._extract_url(bucket.get_public_url(path))
        except Exception as exc:
            raise ReportStorageError(f"Failed to upload report for case {case_id}: {exc}") from exc

        try:
            record = await self._repo.get_by_case_id(session, case_id)
            if record is None:
                raise ReportStorageError(f"Investigation case {case_id} was not found")
            state_json = dict(record.state_json or {})
            state_json["report_storage"] = {
                "bucket": self._bucket_name,
                "path": path,
                "reference": reference,
                "url": url,
                "content_type": "application/json",
            }
            updated = await self._repo.update_state(session, case_id, state_json)
            if updated is None:
                raise ReportStorageError(f"Investigation case {case_id} could not be updated")
        except ReportStorageError:
            raise
        except Exception as exc:
            raise ReportStorageError(f"Failed to link report to case {case_id}: {exc}") from exc
        return StoredReport(case_id=case_id, bucket=self._bucket_name, path=path, reference=reference, url=url)
