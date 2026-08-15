"""Add extracted_entities and extracted_transactions columns to document_records.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add extracted_entities and extracted_transactions JSON columns."""
    op.add_column(
        "document_records",
        sa.Column("extracted_entities", sa.JSON, nullable=True),
    )
    op.add_column(
        "document_records",
        sa.Column("extracted_transactions", sa.JSON, nullable=True),
    )


def downgrade() -> None:
    """Remove extracted_entities and extracted_transactions columns."""
    op.drop_column("document_records", "extracted_transactions")
    op.drop_column("document_records", "extracted_entities")
