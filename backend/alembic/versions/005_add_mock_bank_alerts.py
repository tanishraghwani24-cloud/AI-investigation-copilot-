"""Add mock_bank_alerts.

Stores fraud alerts raised by the Mock Bank simulator against real
transactions, and the investigation each alert was escalated to.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mock_bank_alerts",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"), nullable=False,
        ),
        sa.Column("alert_id", sa.String(64), nullable=False),
        # Unique: one alert per transaction, enforced by the database rather
        # than by the simulator remembering what it has already raised.
        sa.Column("transaction_id", sa.String(64), nullable=False),
        sa.Column("account_id", sa.String(64), nullable=False),
        sa.Column("customer_id", sa.String(64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="MEDIUM"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column("case_id", sa.String(64), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
    )
    op.create_index("ix_mock_bank_alerts_alert_id", "mock_bank_alerts", ["alert_id"], unique=True)
    op.create_index(
        "ix_mock_bank_alerts_transaction_id", "mock_bank_alerts", ["transaction_id"], unique=True,
    )
    op.create_index("ix_mock_bank_alerts_account_id", "mock_bank_alerts", ["account_id"])
    op.create_index("ix_mock_bank_alerts_status", "mock_bank_alerts", ["status"])
    op.create_index("ix_mock_bank_alerts_case_id", "mock_bank_alerts", ["case_id"])
    op.create_index("ix_mock_bank_alerts_created_at", "mock_bank_alerts", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_mock_bank_alerts_created_at", table_name="mock_bank_alerts")
    op.drop_index("ix_mock_bank_alerts_case_id", table_name="mock_bank_alerts")
    op.drop_index("ix_mock_bank_alerts_status", table_name="mock_bank_alerts")
    op.drop_index("ix_mock_bank_alerts_account_id", table_name="mock_bank_alerts")
    op.drop_index("ix_mock_bank_alerts_transaction_id", table_name="mock_bank_alerts")
    op.drop_index("ix_mock_bank_alerts_alert_id", table_name="mock_bank_alerts")
    op.drop_table("mock_bank_alerts")
