"""Context & Evidence Intelligence Agent.

Pure-Python, deterministic agent that analyses the banking data
inside an ``InvestigationState`` and produces a populated
``ContextIntelligence`` object.

No LLM.  No Gemini.  No AI.  No database queries.
All logic is derived from the data already present in the state.
"""

from datetime import timedelta

from app.schemas.investigation_state import (
    AgentStatus,
    AnomalyType,
    ContextIntelligence,
    DetectedAnomaly,
    InvestigationState,
    SeverityLevel,
    Transaction,
)

# ── Thresholds ────────────────────────────────────────────────────────

_LARGE_TXN_THRESHOLD: float = 10_000.0
"""Transactions above this amount are considered large."""

_RAPID_TXN_WINDOW_MINUTES: int = 30
"""Two transactions within this window are considered rapid."""

_HIGH_RISK_SCORE_THRESHOLD: float = 0.7
_MEDIUM_RISK_SCORE_THRESHOLD: float = 0.4


# ── Internal helpers ─────────────────────────────────────────────────


def _compute_transaction_stats(
    transactions: list[Transaction],
) -> dict[str, float]:
    """Compute summary statistics for a list of transactions.

    Returns:
        Dict with keys: total, count, average, maximum, minimum.
    """
    if not transactions:
        return {
            "total": 0.0,
            "count": 0,
            "average": 0.0,
            "maximum": 0.0,
            "minimum": 0.0,
        }

    amounts = [t.amount for t in transactions]
    total = sum(amounts)
    count = len(amounts)

    return {
        "total": round(total, 2),
        "count": float(count),
        "average": round(total / count, 2),
        "maximum": round(max(amounts), 2),
        "minimum": round(min(amounts), 2),
    }


def _find_large_transactions(
    transactions: list[Transaction],
) -> list[Transaction]:
    """Return transactions exceeding the large-transaction threshold."""
    return [t for t in transactions if t.amount > _LARGE_TXN_THRESHOLD]


def _find_rapid_transaction_pairs(
    transactions: list[Transaction],
) -> list[tuple[Transaction, Transaction]]:
    """Return pairs of transactions occurring within the rapid window.

    Transactions must have a valid ``timestamp`` to be considered.
    """
    timed = sorted(
        [t for t in transactions if t.timestamp is not None],
        key=lambda t: t.timestamp,  # type: ignore[arg-type]
    )
    pairs: list[tuple[Transaction, Transaction]] = []
    for i in range(len(timed) - 1):
        t1, t2 = timed[i], timed[i + 1]
        delta = t2.timestamp - t1.timestamp  # type: ignore[operator]
        if delta <= timedelta(minutes=_RAPID_TXN_WINDOW_MINUTES):
            pairs.append((t1, t2))
    return pairs


def _compute_risk_score(
    stats: dict[str, float],
    large_count: int,
    rapid_pair_count: int,
    risk_rating: str | None,
) -> float:
    """Compute a deterministic risk score between 0.0 and 1.0.

    Factors:
      - Proportion of large transactions  (weight 0.30)
      - Rapid transaction pairs           (weight 0.25)
      - Average transaction amount         (weight 0.20)
      - Customer risk rating               (weight 0.25)
    """
    txn_count = int(stats["count"])

    # Factor 1: large-transaction ratio
    large_ratio = large_count / max(txn_count, 1)
    f_large = min(large_ratio, 1.0)

    # Factor 2: rapid pairs
    f_rapid = min(rapid_pair_count / max(txn_count - 1, 1), 1.0)

    # Factor 3: average amount normalised against threshold
    f_amount = min(stats["average"] / (_LARGE_TXN_THRESHOLD * 2), 1.0)

    # Factor 4: customer risk rating
    risk_map = {"HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.2}
    f_risk = risk_map.get((risk_rating or "").upper(), 0.3)

    score = (
        0.30 * f_large
        + 0.25 * f_rapid
        + 0.20 * f_amount
        + 0.25 * f_risk
    )

    return round(min(max(score, 0.0), 1.0), 2)


def _build_key_indicators(
    stats: dict[str, float],
    large_txns: list[Transaction],
    rapid_pairs: list[tuple[Transaction, Transaction]],
    customer_name: str | None,
    alert_reason: str | None,
) -> list[str]:
    """Build a list of human-readable key indicator strings."""
    indicators: list[str] = []

    txn_count = int(stats["count"])
    if txn_count > 0:
        indicators.append(
            f"{txn_count} transactions totalling ${stats['total']:,.2f}"
        )

    if large_txns:
        indicators.append(
            f"{len(large_txns)} large transaction(s) exceeding "
            f"${_LARGE_TXN_THRESHOLD:,.2f}"
        )

    if stats["maximum"] > 0:
        indicators.append(
            f"Largest single transaction: ${stats['maximum']:,.2f}"
        )

    if rapid_pairs:
        indicators.append(
            f"{len(rapid_pairs)} rapid successive transaction pair(s) "
            f"within {_RAPID_TXN_WINDOW_MINUTES} minutes"
        )

    if alert_reason:
        indicators.append(f"Alert: {alert_reason}")

    return indicators


def _build_anomalies(
    large_txns: list[Transaction],
    rapid_pairs: list[tuple[Transaction, Transaction]],
) -> list[DetectedAnomaly]:
    """Create DetectedAnomaly objects for detected patterns."""
    anomalies: list[DetectedAnomaly] = []
    anomaly_counter = 0

    # Large transactions
    for txn in large_txns:
        anomaly_counter += 1
        severity = (
            SeverityLevel.HIGH
            if txn.amount > _LARGE_TXN_THRESHOLD * 3
            else SeverityLevel.MEDIUM
        )
        anomalies.append(
            DetectedAnomaly(
                anomaly_id=f"ANOM-{anomaly_counter:03d}",
                anomaly_type=AnomalyType.POINT,
                severity=severity,
                description=(
                    f"Large {txn.transaction_type} transaction of "
                    f"${txn.amount:,.2f} exceeds ${_LARGE_TXN_THRESHOLD:,.2f} "
                    f"threshold."
                ),
                related_transactions=[txn.transaction_id],
            )
        )

    # Rapid transaction pairs
    for t1, t2 in rapid_pairs:
        anomaly_counter += 1
        combined = t1.amount + t2.amount
        anomalies.append(
            DetectedAnomaly(
                anomaly_id=f"ANOM-{anomaly_counter:03d}",
                anomaly_type=AnomalyType.BEHAVIORAL,
                severity=SeverityLevel.MEDIUM,
                description=(
                    f"Rapid successive transactions totalling "
                    f"${combined:,.2f} within {_RAPID_TXN_WINDOW_MINUTES} "
                    f"minutes."
                ),
                related_transactions=[
                    t1.transaction_id,
                    t2.transaction_id,
                ],
            )
        )

    return anomalies


def _build_context_summary(
    stats: dict[str, float],
    large_txns: list[Transaction],
    rapid_pairs: list[tuple[Transaction, Transaction]],
    customer_name: str | None,
    alert_reason: str | None,
    risk_score: float,
) -> str:
    """Compose a deterministic narrative summary."""
    parts: list[str] = []

    who = customer_name or "The customer"
    parts.append(
        f"{who} has {int(stats['count'])} transaction(s) totalling "
        f"${stats['total']:,.2f} under investigation."
    )

    if large_txns:
        parts.append(
            f"{len(large_txns)} transaction(s) exceed the "
            f"${_LARGE_TXN_THRESHOLD:,.2f} large-transaction threshold."
        )

    if rapid_pairs:
        parts.append(
            f"{len(rapid_pairs)} pair(s) of rapid successive transactions "
            f"were detected within {_RAPID_TXN_WINDOW_MINUTES}-minute windows."
        )

    if alert_reason:
        parts.append(f"Alert trigger: {alert_reason}")

    # Risk characterisation
    if risk_score >= _HIGH_RISK_SCORE_THRESHOLD:
        risk_label = "HIGH"
    elif risk_score >= _MEDIUM_RISK_SCORE_THRESHOLD:
        risk_label = "MEDIUM"
    else:
        risk_label = "LOW"
    parts.append(f"Overall contextual risk: {risk_label} ({risk_score:.2f}).")

    return " ".join(parts)


# ── Public API ────────────────────────────────────────────────────────


def context_agent(state: InvestigationState) -> dict:
    """Execute the Context & Evidence Intelligence Agent.

    Analyses the transactions and customer data inside *state* and
    produces a populated ``ContextIntelligence``.  All logic is pure
    deterministic Python — no LLM, no Gemini, no external services.

    Args:
        state: The current investigation state.

    Returns:
        A dict containing ``context_intelligence`` — compatible with
        LangGraph node update conventions.
    """
    transactions = state.case_input.transactions
    customer = state.case_input.customer_profile
    alert_reason = state.case_input.alert_reason

    customer_name: str | None = customer.name if customer else None
    customer_risk: str | None = customer.risk_rating if customer else None

    # Analyse
    stats = _compute_transaction_stats(transactions)
    large_txns = _find_large_transactions(transactions)
    rapid_pairs = _find_rapid_transaction_pairs(transactions)

    risk_score = _compute_risk_score(
        stats,
        large_count=len(large_txns),
        rapid_pair_count=len(rapid_pairs),
        risk_rating=customer_risk,
    )

    key_indicators = _build_key_indicators(
        stats, large_txns, rapid_pairs, customer_name, alert_reason,
    )

    anomalies = _build_anomalies(large_txns, rapid_pairs)

    context_summary = _build_context_summary(
        stats, large_txns, rapid_pairs, customer_name, alert_reason, risk_score,
    )

    context = ContextIntelligence(
        status=AgentStatus.COMPLETED,
        context_summary=context_summary,
        key_indicators=key_indicators,
        anomalies=anomalies,
        risk_score=risk_score,
    )

    return {
        "context_intelligence": context,
    }
