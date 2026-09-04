"""SQLAlchemy ORM models for the persistent Mock Bank.

Provides relational tables for customers, accounts, and transactions
that mirror the in-memory Pydantic models in ``app.mock_bank.models``
but are backed by the Supabase PostgreSQL database.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class MockBankCustomer(Base):
    """Persistent Mock Bank customer record."""

    __tablename__ = "mock_bank_customers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    customer_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(256), nullable=False,
    )
    email: Mapped[str | None] = mapped_column(
        String(256), nullable=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String(64), nullable=True,
    )
    address: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    date_of_birth: Mapped[str | None] = mapped_column(
        String(32), nullable=True,
    )
    account_open_date: Mapped[str | None] = mapped_column(
        String(32), nullable=True,
    )
    risk_rating: Mapped[str | None] = mapped_column(
        String(32), nullable=True,
    )
    occupation: Mapped[str | None] = mapped_column(
        String(256), nullable=True,
    )
    nationality: Mapped[str | None] = mapped_column(
        String(16), nullable=True,
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

    # Relationships
    accounts: Mapped[list["MockBankAccount"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<MockBankCustomer customer_id={self.customer_id!r}>"


class MockBankAccount(Base):
    """Persistent Mock Bank account record."""

    __tablename__ = "mock_bank_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    account_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False,
    )
    customer_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("mock_bank_customers.customer_id"),
        index=True,
        nullable=False,
    )
    account_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(8), nullable=False, default="USD",
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="ACTIVE",
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

    # Relationships
    customer: Mapped["MockBankCustomer"] = relationship(
        back_populates="accounts",
    )
    transactions: Mapped[list["MockBankTransaction"]] = relationship(
        back_populates="account", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<MockBankAccount account_id={self.account_id!r}>"


class MockBankTransaction(Base):
    """Persistent Mock Bank transaction record."""

    __tablename__ = "mock_bank_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    transaction_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False,
    )
    account_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("mock_bank_accounts.account_id"),
        index=True,
        nullable=False,
    )
    receiver_account_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True,
    )
    amount: Mapped[float] = mapped_column(
        Float, nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(8), nullable=False, default="USD",
    )
    transaction_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
    )
    channel: Mapped[str] = mapped_column(
        String(32), nullable=False, default="ONLINE",
    )
    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True,
    )
    location: Mapped[str | None] = mapped_column(
        String(256), nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="COMPLETED",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    # Relationships
    account: Mapped["MockBankAccount"] = relationship(
        back_populates="transactions",
    )

    def __repr__(self) -> str:
        return f"<MockBankTransaction transaction_id={self.transaction_id!r}>"


class MockBankAlert(Base):
    """A fraud alert raised against one Mock Bank transaction.

    Alerts are produced by the Mock Bank simulator from real transaction rows
    using the same thresholds the Context agent applies, so an alert always
    points at a transaction that exists. ``transaction_id`` is unique, which is
    what prevents the simulator from raising a second alert for the same
    transaction.

    ``case_id`` records the investigation an officer triggered from this alert.
    It is the alert-to-investigation link, and — being set once — is also what
    stops the same alert creating a duplicate investigation.
    """

    __tablename__ = "mock_bank_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    alert_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False,
    )
    transaction_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False,
    )
    account_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False,
    )
    customer_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True,
    )
    reason: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, default="MEDIUM",
    )
    risk_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5,
    )
    # OPEN until an officer investigates it, then INVESTIGATING.
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="OPEN", index=True,
    )
    case_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        index=True,
    )

    def __repr__(self) -> str:
        return f"<MockBankAlert alert_id={self.alert_id!r} status={self.status!r}>"
