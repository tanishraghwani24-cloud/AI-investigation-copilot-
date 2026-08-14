"""Add extracted_text and summary columns to document_records.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add extracted_text and summary columns to document_records."""
    op.add_column(
        "document_records",
        sa.Column("extracted_text", sa.Text, nullable=True),
    )
    op.add_column(
        "document_records",
        sa.Column("summary", sa.Text, nullable=True),
    )


def downgrade() -> None:
    """Remove extracted_text and summary columns from document_records."""
    op.drop_column("document_records", "summary")
    op.drop_column("document_records", "extracted_text")
