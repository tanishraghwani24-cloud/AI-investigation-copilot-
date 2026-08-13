"""Repository skeleton for database operations.

All methods raise ``NotImplementedError`` — actual CRUD logic
belongs to a future round.  This file defines the interface
contract that the API layer will depend on.
"""

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
        """Persist a new document record."""
        raise NotImplementedError

    async def get_by_document_id(
        self,
        session: AsyncSession,
        document_id: str,
    ) -> DocumentRecord | None:
        """Retrieve a document by its document_id."""
        raise NotImplementedError

    async def list_by_case(
        self,
        session: AsyncSession,
        case_id: str,
    ) -> list[DocumentRecord]:
        """List all documents for a given case."""
        raise NotImplementedError
