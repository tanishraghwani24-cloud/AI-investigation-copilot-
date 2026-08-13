"""SQLAlchemy ORM model for supporting documents."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DocumentRecord(Base):
    """Persisted supporting document record.

    Tracks uploaded documents linked to an investigation case.
    """

    __tablename__ = "document_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    case_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("investigation_cases.case_id"),
        index=True,
        nullable=False,
    )
    document_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False,
    )
    document_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
    )
    file_name: Mapped[str | None] = mapped_column(
        String(256), nullable=True,
    )
    file_url: Mapped[str | None] = mapped_column(
        String(1024), nullable=True,
    )
    processing_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING",
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    def __repr__(self) -> str:
        return f"<DocumentRecord document_id={self.document_id!r} case_id={self.case_id!r}>"
