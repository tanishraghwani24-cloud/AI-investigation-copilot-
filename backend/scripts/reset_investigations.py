"""Reset investigation history, leaving everything else intact.

Clears the investigation records built up during development so a demo starts
from an empty Investigations page. Uses the project's ORM models so foreign
keys and dependent rows are handled the same way the application would.

Removed:
  * investigation_cases      — the investigations themselves
  * case_presence            — live "working on this case" rows, which are
                               meaningless once their case is gone
  * document_records         — evidence uploaded against a removed case

Preserved:
  * mock_bank_customers / _accounts / _transactions   (bank seed data)
  * mock_bank_alerts                                   (reset to OPEN, see below)
  * investigator_profiles                              (officer identities)
  * Supabase auth.users                                (never touched)

Alerts are kept but any that were escalated to a now-deleted investigation are
returned to OPEN with their case link cleared, so the Officer Box still has
actionable work immediately after a reset.

Usage (from backend/):
    python scripts/reset_investigations.py            # show what would change
    python scripts/reset_investigations.py --apply    # perform the reset
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402
from sqlalchemy import delete, func, select, update  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# app.db.session must be imported before the models package: app.db.__init__
# pulls in the repositories, which import the models, and importing the models
# first leaves that cycle half-resolved. app.main does the same thing.
import app.db.session  # noqa: E402,F401

from app.models import (  # noqa: E402
    CasePresence,
    DocumentRecord,
    InvestigationCase,
    InvestigatorProfile,
    MockBankAccount,
    MockBankAlert,
    MockBankCustomer,
    MockBankTransaction,
)


async def _counts(session) -> dict[str, int]:
    async def count(model) -> int:
        return await session.scalar(select(func.count()).select_from(model)) or 0

    return {
        "investigation_cases": await count(InvestigationCase),
        "case_presence": await count(CasePresence),
        "document_records": await count(DocumentRecord),
        "mock_bank_alerts": await count(MockBankAlert),
        "mock_bank_transactions": await count(MockBankTransaction),
        "mock_bank_customers": await count(MockBankCustomer),
        "mock_bank_accounts": await count(MockBankAccount),
        "investigator_profiles": await count(InvestigatorProfile),
    }


async def reset(apply: bool) -> None:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as session:
            before = await _counts(session)
            escalated = await session.scalar(
                select(func.count())
                .select_from(MockBankAlert)
                .where(MockBankAlert.case_id.is_not(None))
            ) or 0

            print("Before:")
            for name, value in before.items():
                print(f"  {name:26s} {value}")
            print(f"  {'alerts linked to a case':26s} {escalated}")

            if not apply:
                print(
                    "\nDry run. Would delete investigation_cases, case_presence and "
                    "document_records, and return escalated alerts to OPEN.\n"
                    "Re-run with --apply to perform the reset."
                )
                return

            # Children first: presence and documents reference a case.
            await session.execute(delete(CasePresence))
            await session.execute(delete(DocumentRecord))
            await session.execute(delete(InvestigationCase))
            # Make previously-escalated alerts actionable again.
            await session.execute(
                update(MockBankAlert)
                .where(MockBankAlert.case_id.is_not(None))
                .values(case_id=None, status="OPEN")
            )
            await session.commit()

            after = await _counts(session)
            open_alerts = await session.scalar(
                select(func.count())
                .select_from(MockBankAlert)
                .where(MockBankAlert.status == "OPEN")
            ) or 0

            print("\nAfter:")
            for name, value in after.items():
                print(f"  {name:26s} {value}")
            print(f"  {'OPEN alerts (actionable)':26s} {open_alerts}")

            assert after["investigation_cases"] == 0
            assert after["case_presence"] == 0
            # Everything that must survive, did.
            for preserved in (
                "mock_bank_customers", "mock_bank_accounts",
                "mock_bank_transactions", "mock_bank_alerts",
                "investigator_profiles",
            ):
                assert after[preserved] == before[preserved], preserved
            print("\nInvestigation history reset; bank data, alerts and officers preserved.")
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true",
        help="Actually perform the reset (otherwise a dry run is printed).",
    )
    args = parser.parse_args()
    asyncio.run(reset(args.apply))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
