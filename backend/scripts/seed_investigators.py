"""Create demo investigator accounts through the real Supabase Auth flow.

Development/demo helper only. It does not bypass authentication: each account is
created with Supabase's own ``/auth/v1/signup`` endpoint using the public anon
key, so the resulting users are ordinary Supabase Auth users who sign in with a
password like anyone else. No credentials are stored in application tables and
no service-role key is used.

The one administrative step is marking the address confirmed, because this
project requires email confirmation and demo mailboxes do not exist. That is
done with the database credentials the application already holds — the same
thing an operator would click in the dashboard.

Usage (from backend/):
    python scripts/seed_investigators.py

Requires SUPABASE_URL and SUPABASE_ANON_KEY in the environment or backend/.env.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Shared demo password. Fine for throwaway demo accounts on a demo project;
# never reuse this pattern for real users.
DEMO_PASSWORD = "HollaDemo!2026"

DEMO_INVESTIGATORS = [
    {"email": "rahul.sharma@hollabank.com", "full_name": "Rahul Sharma"},
    {"email": "priya.nair@hollabank.com", "full_name": "Priya Nair"},
    {"email": "daniel.okafor@hollabank.com", "full_name": "Daniel Okafor"},
]


def _post(url: str, anon_key: str, payload: dict) -> tuple[int, dict]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "apikey": anon_key,
            "Authorization": f"Bearer {anon_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        try:
            return error.code, json.loads(error.read().decode() or "{}")
        except json.JSONDecodeError:
            return error.code, {}


async def _confirm_emails(database_url: str, emails: list[str]) -> int:
    """Mark demo addresses confirmed so the accounts can sign in."""
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text(
                    "UPDATE auth.users SET email_confirmed_at = now() "
                    "WHERE email = ANY(:emails) AND email_confirmed_at IS NULL"
                ),
                {"emails": emails},
            )
            return result.rowcount or 0
    finally:
        await engine.dispose()


def main() -> int:
    supabase_url = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    anon_key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get(
        "NEXT_PUBLIC_SUPABASE_ANON_KEY", ""
    )
    database_url = os.environ.get("DATABASE_URL", "")

    if not supabase_url or not anon_key:
        print(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set "
            "(the anon key is the public browser key from the Supabase dashboard).",
            file=sys.stderr,
        )
        return 1

    created = 0
    for investigator in DEMO_INVESTIGATORS:
        status, body = _post(
            f"{supabase_url}/auth/v1/signup",
            anon_key,
            {
                "email": investigator["email"],
                "password": DEMO_PASSWORD,
                "data": {"full_name": investigator["full_name"]},
            },
        )
        if status == 200:
            created += 1
            print(f"  created  {investigator['full_name']:<16} {investigator['email']}")
        elif body.get("error_code") in {"user_already_exists", "email_exists"}:
            print(f"  exists   {investigator['full_name']:<16} {investigator['email']}")
        else:
            print(
                f"  FAILED   {investigator['email']}: "
                f"{body.get('msg') or body.get('error_code') or status}",
                file=sys.stderr,
            )

    if database_url:
        confirmed = asyncio.run(
            _confirm_emails(database_url, [i["email"] for i in DEMO_INVESTIGATORS])
        )
        print(f"  confirmed {confirmed} address(es)")
    else:
        print("  DATABASE_URL unset — confirm the addresses manually before signing in.")

    print(f"\n{len(DEMO_INVESTIGATORS)} demo investigator(s) ready. Password: {DEMO_PASSWORD}")
    print(f"  ({created} newly created this run)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
