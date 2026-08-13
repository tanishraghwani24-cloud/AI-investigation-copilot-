"""Initial schema — investigation_cases and document_records.

Revision ID: a1b2c3d4e5f6
Revises: None
Create Date: 2026-08-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create investigation_cases and document_records tables."""
    op.create_table(
        "investigation_cases",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("case_id", sa.String(64), unique=True, index=True, nullable=False),
        sa.Column(
            "status", sa.String(32), nullable=False, server_default="INTAKE",
        ),
        sa.Column("state_json", sa.JSON, nullable=True),
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

    op.create_table(
        "document_records",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "case_id",
            sa.String(64),
            sa.ForeignKey("investigation_cases.case_id"),
            index=True,
            nullable=False,
        ),
        sa.Column("document_id", sa.String(64), unique=True, nullable=False),
        sa.Column("document_type", sa.String(32), nullable=False),
        sa.Column("file_name", sa.String(256), nullable=True),
        sa.Column("file_url", sa.String(1024), nullable=True),
        sa.Column(
            "processing_status",
            sa.String(32),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    """Drop document_records and investigation_cases tables."""
    op.drop_table("document_records")
    op.drop_table("investigation_cases")
