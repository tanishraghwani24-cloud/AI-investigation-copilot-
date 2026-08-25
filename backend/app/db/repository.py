"""Repository layer for database operations.

``InvestigationRepository`` provides full CRUD for investigation cases.
``DocumentRepository`` provides real CRUD for supporting documents.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.document import DocumentRecord
from app.models.investigation import InvestigationCase


class InvestigationRepository:
    """Data-access layer for investigation cases."""

    async def create(
        self,
        session: AsyncSession,
        case_id: str,
        state_json: dict,
    ) -> InvestigationCase:
        """Persist a new investigation case.

        Args:
            session: Active async database session.
            case_id: The investigation case identifier.
            state_json: Full serialised InvestigationState as a dict.

        Returns:
            The newly created InvestigationCase record.
        """
        status = state_json.get("current_stage", "INTAKE")
        record = InvestigationCase(
            case_id=case_id,
            status=status,
            state_json=state_json,
        )
        session.add(record)
        await session.flush()
        return record

    async def get_by_case_id(
        self,
        session: AsyncSession,
        case_id: str,
    ) -> InvestigationCase | None:
        """Retrieve an investigation case by its case_id.

        Args:
            session: Active async database session.
            case_id: The investigation case identifier to look up.

        Returns:
            The matching InvestigationCase, or None if not found.
        """
        stmt = select(InvestigationCase).where(
            InvestigationCase.case_id == case_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_state(
        self,
        session: AsyncSession,
        case_id: str,
        state_json: dict,
    ) -> InvestigationCase | None:
        """Update the stored state for an investigation case.

        Overwrites the ``state_json`` column, derives ``status`` from the
        state's ``current_stage``, and bumps ``updated_at``.

        Args:
            session: Active async database session.
            case_id: The investigation case identifier.
            state_json: Updated serialised InvestigationState.

        Returns:
            The updated InvestigationCase, or None if the case was not found.
        """
        record = await self.get_by_case_id(session, case_id)
        if record is None:
            return None
        record.state_json = state_json
        flag_modified(record, "state_json")
        record.status = state_json.get("current_stage", record.status)
        record.updated_at = datetime.now(timezone.utc)
        await session.flush()
        return record

    async def list_all(
        self,
        session: AsyncSession,
        *,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[InvestigationCase]:
        """List persisted investigation cases with optional filtering.

        Args:
            session: Active async database session.

        Returns:
            A list of all InvestigationCase records.
        """
        stmt = select(InvestigationCase)
        if status is not None:
            stmt = stmt.where(InvestigationCase.status == status)
        stmt = (
            stmt.order_by(InvestigationCase.created_at)
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


class DocumentRepository:
    """Data-access layer for supporting documents."""

    async def create(
        self,
        session: AsyncSession,
        case_id: str,
        document_data: dict,
    ) -> DocumentRecord:
        """Persist a new document record.

        Args:
            session: Active async database session.
            case_id: The investigation case identifier.
            document_data: Dictionary of DocumentRecord column values
                           (excluding ``case_id``, which is set explicitly).

        Returns:
            The newly created DocumentRecord.
        """
        record = DocumentRecord(case_id=case_id, **document_data)
        session.add(record)
        await session.flush()
        return record

    async def get_by_document_id(
        self,
        session: AsyncSession,
        document_id: str,
    ) -> DocumentRecord | None:
        """Retrieve a document by its document_id."""
        stmt = select(DocumentRecord).where(
            DocumentRecord.document_id == document_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_case(
        self,
        session: AsyncSession,
        case_id: str,
    ) -> list[DocumentRecord]:
        """List all documents for a given case."""
        stmt = (
            select(DocumentRecord)
            .where(DocumentRecord.case_id == case_id)
            .order_by(DocumentRecord.uploaded_at)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        session: AsyncSession,
        record: DocumentRecord,
        update_data: dict,
    ) -> DocumentRecord:
        """Update an existing document record.

        Args:
            session: Active async database session.
            record: The DocumentRecord instance to update.
            update_data: Dictionary of column names → new values.

        Returns:
            The updated DocumentRecord.
        """
        for key, value in update_data.items():
            setattr(record, key, value)
        await session.flush()
        return record

