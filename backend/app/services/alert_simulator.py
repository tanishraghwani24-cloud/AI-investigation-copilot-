"""Mock Bank incoming-transaction and fraud-alert simulator.

A bank officer's inbox fills up because transactions keep arriving, so the demo
needs the same shape: new Mock Bank transactions land periodically, and the ones
that trip the existing risk thresholds raise alerts.

Design notes:

* Transactions are written to the existing ``mock_bank_transactions`` table on
  the existing seeded accounts, so every alert points at a real row that the
  existing Mock Bank API can already serve. Seeded data is never modified.
* Alerting reuses the Context agent's ``_LARGE_TXN_THRESHOLD`` and the
  generator's ``generate_alert`` wording rather than inventing a second rule
  engine, so the inbox agrees with what an investigation will later conclude.
* No LLM is involved at any point.
* One alert per transaction is enforced by a unique constraint on
  ``transaction_id``, not by in-process bookkeeping.
* Simulated rows are bounded: each tick prunes the oldest simulated
  transactions and resolved alerts beyond a cap, so a long-running demo cannot
  grow the database without limit. Seeded rows are outside the cap.
"""

from __future__ import annotations

import asyncio
import logging
import random
import secrets
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.context_agent import _LARGE_TXN_THRESHOLD
from app.mock_bank.generator import generate_alert
from app.mock_bank.models import Transaction as MockTransaction
from app.models.mock_bank import MockBankAccount, MockBankAlert, MockBankTransaction

logger = logging.getLogger(__name__)

# Simulated rows carry this prefix so they are always distinguishable from the
# seeded fixtures, which pruning must never touch.
SIMULATED_TXN_PREFIX = "TXN-SIM-"
ALERT_PREFIX = "ALERT-"

# Bounds: how many simulated transactions and resolved alerts to retain.
MAX_SIMULATED_TRANSACTIONS = 300
MAX_RESOLVED_ALERTS = 100

_TRANSACTION_TYPES = ("WIRE", "ACH", "P2P", "CARD")
_CHANNELS = ("ONLINE", "MOBILE", "ATM", "BRANCH")
_LOCATIONS = (
    "New York, US", "London, UK", "Dubai, AE", "Singapore, SG",
    "Lagos, NG", "Bucharest, RO", "George Town, KY", "Panama City, PA",
)
_DESCRIPTIONS = (
    "Cross-border settlement", "Vendor payment", "Investment deposit",
    "Consulting fee", "Equipment purchase", "Intra-group transfer",
)

# Roughly one in three simulated transactions is large enough to alert, so the
# inbox gains work steadily without every transaction being suspicious.
_LARGE_TRANSACTION_PROBABILITY = 0.34


def _severity_for(amount: float) -> str:
    if amount >= _LARGE_TXN_THRESHOLD * 5:
        return "HIGH"
    if amount >= _LARGE_TXN_THRESHOLD * 2:
        return "MEDIUM"
    return "LOW"


def _risk_score_for(amount: float) -> float:
    """Scale the amount onto 0-1 using the same threshold the agents use."""
    return round(min(1.0, amount / (_LARGE_TXN_THRESHOLD * 10)), 4)


class AlertSimulator:
    """Generates Mock Bank transactions and the alerts they trigger."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()

    async def _pick_account(self, session: AsyncSession) -> MockBankAccount | None:
        """Choose one of the existing seeded accounts to receive activity."""
        accounts = (await session.execute(select(MockBankAccount))).scalars().all()
        if not accounts:
            return None
        return self._rng.choice(list(accounts))

    def _build_transaction(self, account: MockBankAccount) -> MockBankTransaction:
        """Build one realistic, uniquely identified incoming transaction."""
        large = self._rng.random() < _LARGE_TRANSACTION_PROBABILITY
        amount = (
            round(self._rng.uniform(_LARGE_TXN_THRESHOLD + 500, 95_000.0), 2)
            if large
            else round(self._rng.uniform(25.0, 9_500.0), 2)
        )
        return MockBankTransaction(
            # token_hex, not a counter: unique even across restarts and workers.
            transaction_id=f"{SIMULATED_TXN_PREFIX}{secrets.token_hex(5).upper()}",
            account_id=account.account_id,
            receiver_account_id=f"ACC-{self._rng.randint(100000, 999999)}",
            amount=amount,
            currency="USD",
            transaction_type=self._rng.choice(_TRANSACTION_TYPES),
            channel=self._rng.choice(_CHANNELS),
            timestamp=datetime.now(timezone.utc),
            description=self._rng.choice(_DESCRIPTIONS),
            location=self._rng.choice(_LOCATIONS),
            status="COMPLETED",
        )

    @staticmethod
    def _should_alert(transaction: MockBankTransaction) -> bool:
        """Apply the same large-transaction threshold the Context agent uses."""
        return transaction.amount > _LARGE_TXN_THRESHOLD

    def _build_alert(
        self,
        transaction: MockBankTransaction,
        account: MockBankAccount,
    ) -> MockBankAlert:
        """Describe the alert using the existing generator wording."""
        reason = generate_alert(0, [MockTransaction(
            transaction_id=transaction.transaction_id,
            sender_account_id=transaction.account_id,
            receiver_account_id=transaction.receiver_account_id or "",
            amount=transaction.amount,
            currency=transaction.currency,
            transaction_type=transaction.transaction_type,
            channel=transaction.channel,
            timestamp=transaction.timestamp,
            description=transaction.description,
            location=transaction.location,
            status=transaction.status,
        )])
        return MockBankAlert(
            alert_id=f"{ALERT_PREFIX}{secrets.token_hex(4).upper()}",
            transaction_id=transaction.transaction_id,
            account_id=transaction.account_id,
            customer_id=account.customer_id,
            reason=reason,
            severity=_severity_for(transaction.amount),
            risk_score=_risk_score_for(transaction.amount),
            status="OPEN",
        )

    async def _prune(self, session: AsyncSession) -> None:
        """Keep simulated rows bounded so a long demo cannot fill the database."""
        total = await session.scalar(
            select(func.count())
            .select_from(MockBankTransaction)
            .where(MockBankTransaction.transaction_id.like(f"{SIMULATED_TXN_PREFIX}%"))
        ) or 0
        if total > MAX_SIMULATED_TRANSACTIONS:
            # Oldest simulated transactions that no alert still points at.
            stale = (await session.execute(
                select(MockBankTransaction.transaction_id)
                .where(MockBankTransaction.transaction_id.like(f"{SIMULATED_TXN_PREFIX}%"))
                .where(~MockBankTransaction.transaction_id.in_(select(MockBankAlert.transaction_id)))
                .order_by(MockBankTransaction.created_at.asc())
                .limit(total - MAX_SIMULATED_TRANSACTIONS)
            )).scalars().all()
            if stale:
                await session.execute(
                    delete(MockBankTransaction)
                    .where(MockBankTransaction.transaction_id.in_(stale))
                )

        resolved = await session.scalar(
            select(func.count()).select_from(MockBankAlert)
            .where(MockBankAlert.status != "OPEN")
        ) or 0
        if resolved > MAX_RESOLVED_ALERTS:
            old = (await session.execute(
                select(MockBankAlert.alert_id)
                .where(MockBankAlert.status != "OPEN")
                .order_by(MockBankAlert.created_at.asc())
                .limit(resolved - MAX_RESOLVED_ALERTS)
            )).scalars().all()
            if old:
                await session.execute(
                    delete(MockBankAlert).where(MockBankAlert.alert_id.in_(old))
                )

    async def simulate_once(
        self,
        session: AsyncSession,
    ) -> tuple[MockBankTransaction | None, MockBankAlert | None]:
        """Generate one transaction, and an alert if it trips the threshold.

        Returns the created transaction and alert (either may be ``None``: no
        seeded accounts to post against, or an amount below the threshold).
        """
        account = await self._pick_account(session)
        if account is None:
            logger.warning("alert-simulator: no Mock Bank accounts to simulate against")
            return None, None

        transaction = self._build_transaction(account)
        session.add(transaction)

        alert: MockBankAlert | None = None
        if self._should_alert(transaction):
            alert = self._build_alert(transaction, account)
            session.add(alert)

        try:
            await self._prune(session)
            await session.commit()
        except IntegrityError:
            # Unique constraint on transaction_id/alert_id: another worker got
            # there first. Drop this tick rather than raising a duplicate alert.
            await session.rollback()
            logger.info("alert-simulator: tick collided with a concurrent insert; skipped")
            return None, None

        if alert is not None:
            logger.info(
                "alert-simulator: raised %s for %s (%.2f USD)",
                alert.alert_id, transaction.transaction_id, transaction.amount,
            )
        return transaction, alert


async def run_simulator_loop(
    session_factory,
    *,
    min_interval: float,
    max_interval: float,
    simulator: AlertSimulator | None = None,
) -> None:
    """Run ticks forever at a randomised interval.

    The interval is jittered between the bounds so alerts do not arrive in a
    visibly mechanical rhythm. Cancellation is propagated so application
    shutdown is clean; every other error is logged and the loop continues,
    because a transient database blip must not silently stop the inbox.
    """
    simulator = simulator or AlertSimulator()
    while True:
        try:
            await asyncio.sleep(random.uniform(min_interval, max_interval))
            async with session_factory() as session:
                await simulator.simulate_once(session)
        except asyncio.CancelledError:
            logger.info("alert-simulator: stopped")
            raise
        except Exception:
            logger.exception("alert-simulator: tick failed; continuing")
