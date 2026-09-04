"""Assign Officer IDs to existing investigator profiles.

Officers sign in with an Officer ID (OFF-001, OFF-002, ...) instead of an email
address. This backfills IDs for accounts that already exist, and creates a
profile row for any Supabase user that has not signed in yet so they can be
issued an ID before their first login.

No credential is created, read, or stored: Supabase remains the only holder of
passwords.

Usage (from backend/):
    python scripts/assign_officer_ids.py            # show current mapping
    python scripts/assign_officer_ids.py --apply    # assign missing IDs
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402
from sqlalchemy import select, text  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import app.db.session  # noqa: E402,F401  (import order, see reset script)

from app.models import InvestigatorProfile  # noqa: E402


async def run(apply: bool) -> None:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as session:
            # Supabase Auth is the source of truth for who exists.
            users = (await session.execute(text(
                "SELECT id, email, raw_user_meta_data->>'full_name' AS full_name "
                "FROM auth.users ORDER BY created_at"
            ))).fetchall()

            profiles = {
                p.user_id: p for p in
                (await session.execute(select(InvestigatorProfile))).scalars().all()
            }
            taken = {p.officer_id for p in profiles.values() if p.officer_id}
            next_number = 1

            def allocate() -> str:
                nonlocal next_number
                while f"OFF-{next_number:03d}" in taken:
                    next_number += 1
                officer_id = f"OFF-{next_number:03d}"
                taken.add(officer_id)
                return officer_id

            print(f"{'Officer ID':<12} {'Name':<20} {'Sign-in email (internal)':<34} status")
            for user in users:
                profile = profiles.get(user.id)
                name = user.full_name or (user.email or "").split("@")[0]

                if profile is None:
                    officer_id = allocate()
                    status = "new profile"
                    if apply:
                        session.add(InvestigatorProfile(
                            user_id=user.id, officer_id=officer_id,
                            full_name=name, email=user.email, role="INVESTIGATOR",
                        ))
                elif profile.officer_id is None:
                    officer_id = allocate()
                    status = "id assigned"
                    if apply:
                        profile.officer_id = officer_id
                        if not profile.email:
                            profile.email = user.email
                else:
                    officer_id = profile.officer_id
                    status = "unchanged"

                # Administrative label for the Supabase dashboard. full_name is
                # deliberately left alone — the UI reads it for the officer's
                # name and derives the avatar initial from it, so prefixing it
                # with an Officer ID would turn every avatar into "O".
                display_name = f"{officer_id} - {name}"
                if apply:
                    await session.execute(
                        text(
                            "UPDATE auth.users SET raw_user_meta_data = "
                            "  coalesce(raw_user_meta_data, '{}'::jsonb) "
                            "  || jsonb_build_object('display_name', cast(:label as text)) "
                            "WHERE id = :uid"
                        ),
                        {"label": display_name, "uid": user.id},
                    )

                print(f"{officer_id:<12} {name:<20} {str(user.email):<34} {status}")

            if apply:
                await session.commit()
                print(
                    "\nOfficer IDs and Auth display names saved. No users were "
                    "created, deleted, or had credentials changed."
                )
            else:
                print("\nDry run. Re-run with --apply to save.")
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Persist the assignments.")
    asyncio.run(run(parser.parse_args().apply))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
