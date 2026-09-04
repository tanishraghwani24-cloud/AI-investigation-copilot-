"""Add officer_id and role to investigator profiles.

Officers sign in with an Officer ID rather than an email address. The Supabase
account still authenticates by email internally — that is Supabase's mechanism
and is left alone — but the mapping lives here so the email never has to appear
in the UI. No credential material is stored.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-09-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable: profiles created before officer IDs existed stay valid, and a
    # unique index still prevents two officers sharing one ID.
    op.add_column(
        "investigator_profiles",
        sa.Column("officer_id", sa.String(32), nullable=True),
    )
    op.add_column(
        "investigator_profiles",
        sa.Column(
            "role", sa.String(32), nullable=False, server_default="INVESTIGATOR",
        ),
    )
    op.create_index(
        "ix_investigator_profiles_officer_id",
        "investigator_profiles", ["officer_id"], unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_investigator_profiles_officer_id", table_name="investigator_profiles",
    )
    op.drop_column("investigator_profiles", "role")
    op.drop_column("investigator_profiles", "officer_id")
