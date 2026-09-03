"""Add mock_bank_customers, mock_bank_accounts, mock_bank_transactions.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create persistent Mock Bank tables."""

    # -- Customers --
    op.create_table(
        "mock_bank_customers",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "customer_id", sa.String(64), unique=True, index=True, nullable=False,
        ),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("email", sa.String(256), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("date_of_birth", sa.String(32), nullable=True),
        sa.Column("account_open_date", sa.String(32), nullable=True),
        sa.Column("risk_rating", sa.String(32), nullable=True),
        sa.Column("occupation", sa.String(256), nullable=True),
        sa.Column("nationality", sa.String(16), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # -- Accounts --
    op.create_table(
        "mock_bank_accounts",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "account_id", sa.String(64), unique=True, index=True, nullable=False,
        ),
        sa.Column(
            "customer_id",
            sa.String(64),
            sa.ForeignKey("mock_bank_customers.customer_id"),
            index=True,
            nullable=False,
        ),
        sa.Column("account_type", sa.String(32), nullable=False),
        sa.Column(
            "currency", sa.String(8), nullable=False, server_default="USD",
        ),
        sa.Column(
            "status", sa.String(32), nullable=False, server_default="ACTIVE",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # -- Transactions --
    op.create_table(
        "mock_bank_transactions",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "transaction_id", sa.String(64), unique=True, index=True, nullable=False,
        ),
        sa.Column(
            "account_id",
            sa.String(64),
            sa.ForeignKey("mock_bank_accounts.account_id"),
            index=True,
            nullable=False,
        ),
        sa.Column("receiver_account_id", sa.String(64), nullable=True),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column(
            "currency", sa.String(8), nullable=False, server_default="USD",
        ),
        sa.Column("transaction_type", sa.String(32), nullable=False),
        sa.Column(
            "channel", sa.String(32), nullable=False, server_default="ONLINE",
        ),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True), nullable=True, index=True,
        ),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("location", sa.String(256), nullable=True),
        sa.Column(
            "status", sa.String(32), nullable=False, server_default="COMPLETED",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    """Drop Mock Bank tables in reverse dependency order."""
    op.drop_table("mock_bank_transactions")
    op.drop_table("mock_bank_accounts")
    op.drop_table("mock_bank_customers")
