"""Add investigator profiles, case presence, and the investigation link.

Investigator identity comes from Supabase Auth. ``investigator_profiles``
mirrors ``auth.users`` into the application schema so investigations can carry
a foreign key and the UI can render a name; no credential material is copied.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "investigator_profiles",
        # Same id as auth.users; no surrogate key needed.
        sa.Column("user_id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("full_name", sa.String(256), nullable=False),
        sa.Column("email", sa.String(256), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
    )
    op.create_index("ix_investigator_profiles_email", "investigator_profiles", ["email"])

    op.create_table(
        "case_presence",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"), nullable=False,
        ),
        sa.Column("case_id", sa.String(64), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["investigator_profiles.user_id"], ondelete="CASCADE",
        ),
        # One heartbeat row per investigator per case: returning officers
        # refresh their row instead of accumulating new ones.
        sa.UniqueConstraint("case_id", "user_id", name="uq_case_presence_case_user"),
    )
    op.create_index("ix_case_presence_case_id", "case_presence", ["case_id"])
    op.create_index("ix_case_presence_user_id", "case_presence", ["user_id"])
    op.create_index("ix_case_presence_last_seen_at", "case_presence", ["last_seen_at"])

    # Historical handler. Nullable so pre-existing investigations survive, and
    # SET NULL so deleting a profile never destroys an investigation record.
    op.add_column(
        "investigation_cases",
        sa.Column("investigator_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_investigation_cases_investigator",
        "investigation_cases", "investigator_profiles",
        ["investigator_id"], ["user_id"], ondelete="SET NULL",
    )
    op.create_index(
        "ix_investigation_cases_investigator_id", "investigation_cases", ["investigator_id"],
    )

    # --- Row Level Security -------------------------------------------------
    # The API reaches Postgres as the owner role, which bypasses RLS, so these
    # policies exist to protect the tables from anything using a Supabase
    # anon/authenticated key (e.g. a future direct-from-browser query). They
    # only add restrictions; no existing table's policies are touched.
    op.execute("ALTER TABLE investigator_profiles ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE case_presence ENABLE ROW LEVEL SECURITY")

    # Collaboration requires seeing colleagues' names, so profiles are readable
    # by any signed-in investigator...
    op.execute("""
        CREATE POLICY investigator_profiles_read_authenticated
        ON investigator_profiles FOR SELECT TO authenticated USING (true)
    """)
    # ...but only the account holder may create or change their own profile.
    op.execute("""
        CREATE POLICY investigator_profiles_write_self
        ON investigator_profiles FOR INSERT TO authenticated
        WITH CHECK (user_id = auth.uid())
    """)
    op.execute("""
        CREATE POLICY investigator_profiles_update_self
        ON investigator_profiles FOR UPDATE TO authenticated
        USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid())
    """)

    # Presence is visible to all investigators (that is the point), but an
    # investigator may only assert or clear their *own* presence.
    op.execute("""
        CREATE POLICY case_presence_read_authenticated
        ON case_presence FOR SELECT TO authenticated USING (true)
    """)
    op.execute("""
        CREATE POLICY case_presence_write_self
        ON case_presence FOR INSERT TO authenticated
        WITH CHECK (user_id = auth.uid())
    """)
    op.execute("""
        CREATE POLICY case_presence_update_self
        ON case_presence FOR UPDATE TO authenticated
        USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid())
    """)
    op.execute("""
        CREATE POLICY case_presence_delete_self
        ON case_presence FOR DELETE TO authenticated USING (user_id = auth.uid())
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS case_presence_delete_self ON case_presence")
    op.execute("DROP POLICY IF EXISTS case_presence_update_self ON case_presence")
    op.execute("DROP POLICY IF EXISTS case_presence_write_self ON case_presence")
    op.execute("DROP POLICY IF EXISTS case_presence_read_authenticated ON case_presence")
    op.execute("DROP POLICY IF EXISTS investigator_profiles_update_self ON investigator_profiles")
    op.execute("DROP POLICY IF EXISTS investigator_profiles_write_self ON investigator_profiles")
    op.execute(
        "DROP POLICY IF EXISTS investigator_profiles_read_authenticated ON investigator_profiles"
    )

    op.drop_index("ix_investigation_cases_investigator_id", table_name="investigation_cases")
    op.drop_constraint(
        "fk_investigation_cases_investigator", "investigation_cases", type_="foreignkey",
    )
    op.drop_column("investigation_cases", "investigator_id")

    op.drop_index("ix_case_presence_last_seen_at", table_name="case_presence")
    op.drop_index("ix_case_presence_user_id", table_name="case_presence")
    op.drop_index("ix_case_presence_case_id", table_name="case_presence")
    op.drop_table("case_presence")

    op.drop_index("ix_investigator_profiles_email", table_name="investigator_profiles")
    op.drop_table("investigator_profiles")
