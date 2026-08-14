"""Repository layer for database operations.

``InvestigationRepository`` methods remain stubs (future round).
``DocumentRepository`` provides real CRUD for supporting documents.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        """Persist a new investigation case."""
        raise NotImplementedError

    async def get_by_case_id(
        self,
        session: AsyncSession,
        case_id: str,
    ) -> InvestigationCase | None:
        """Retrieve an investigation case by its case_id."""
        raise NotImplementedError

    async def update_state(
        self,
        session: AsyncSession,
        case_id: str,
        state_json: dict,
    ) -> InvestigationCase | None:
        """Update the stored state for an investigation case."""
        raise NotImplementedError

    async def list_all(
        self,
        session: AsyncSession,
    ) -> list[InvestigationCase]:
        """List all investigation cases."""
        raise NotImplementedError


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

