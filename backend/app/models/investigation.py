"""SQLAlchemy ORM model for investigation cases."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, JSON, String, Uuid, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class InvestigationCase(Base):
    """Persisted investigation case record.

    Stores the case identifier and the full serialised
    ``InvestigationState`` as JSON for round-trip persistence.
    """

    __tablename__ = "investigation_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    case_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="INTAKE",
    )
    state_json: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
    )
    # The investigator who triggered this case. Historical and permanent —
    # distinct from live presence, so a completed case still shows who handled
    # it. Nullable: investigations predating investigator accounts have none.
    investigator_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("investigator_profiles.user_id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<InvestigationCase case_id={self.case_id!r} status={self.status!r}>"
