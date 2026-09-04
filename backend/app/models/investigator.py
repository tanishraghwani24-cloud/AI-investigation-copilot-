"""Investigator profile and live case-presence models.

Two deliberately separate concepts:

* ``InvestigatorProfile`` mirrors a Supabase ``auth.users`` row into the
  application schema so investigations can carry a foreign key and the UI can
  render a name without a second round trip to the auth service. Supabase Auth
  remains the source of truth for credentials — no password ever lands here.
* ``CasePresence`` is *live* state: who is looking at a case right now. It is
  heartbeat-driven and expires, which is what keeps a finished case from
  appearing permanently "in progress".

The historical "who handled this case" answer lives on
``InvestigationCase.investigator_id``, not here.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class InvestigatorProfile(Base):
    """Display identity for one authenticated Supabase user."""

    __tablename__ = "investigator_profiles"

    # Same value as auth.users.id, so the profile needs no surrogate key.
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True,
    )
    # The identifier officers actually type at sign-in (e.g. "OFF-001"). The
    # Supabase account keeps an email internally because that is what Supabase
    # authenticates with, but the email is never shown in the UI.
    officer_id: Mapped[str | None] = mapped_column(
        String(32), unique=True, index=True, nullable=True,
    )
    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="INVESTIGATOR")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc), server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc), server_default=text("now()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<InvestigatorProfile user_id={self.user_id!r} name={self.full_name!r}>"


class CasePresence(Base):
    """Heartbeat marking an investigator as actively working a case.

    One row per (case, investigator): a returning officer refreshes their own
    heartbeat rather than accumulating rows. Staleness is decided at read time
    from ``last_seen_at`` so a crashed browser cannot pin a case forever.
    """

    __tablename__ = "case_presence"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    case_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("investigator_profiles.user_id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
        default=lambda: datetime.now(timezone.utc), server_default=text("now()"),
    )

    def __repr__(self) -> str:
        return f"<CasePresence case_id={self.case_id!r} user_id={self.user_id!r}>"
