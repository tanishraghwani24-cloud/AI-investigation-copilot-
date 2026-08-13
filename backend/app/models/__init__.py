"""ORM model exports."""

from app.models.document import DocumentRecord
from app.models.investigation import InvestigationCase

__all__ = [
    "DocumentRecord",
    "InvestigationCase",
]
