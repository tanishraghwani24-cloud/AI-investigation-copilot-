"""Context & Evidence Intelligence Agent.

Pure-Python, deterministic agent that analyses the banking data
inside an ``InvestigationState`` and produces a populated
``ContextIntelligence`` object.

No LLM.  No Gemini.  No AI.  No database queries.
All logic is derived from the data already present in the state.

Round 3: Incorporates extracted document evidence from
``state.case_input.supporting_documents`` into the context synthesis.
Documents with empty/None extracted_text are ignored.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import timedelta

from app.db.session import async_session_factory
from app.services.mock_bank_service import MockBankService

from app.schemas.investigation_state import (
    AgentStatus,
    AnomalyType,
    ContextIntelligence,
    DetectedAnomaly,
    HistoricalBaseline,
    InvestigationState,
    SeverityLevel,
    SupportingDocument,
    Transaction,
)

# ── Thresholds ────────────────────────────────────────────────────────

_LARGE_TXN_THRESHOLD: float = 10_000.0
"""Transactions above this amount are considered large."""

_RAPID_TXN_WINDOW_MINUTES: int = 30
"""Two transactions within this window are considered rapid."""

_HIGH_RISK_SCORE_THRESHOLD: float = 0.7
_MEDIUM_RISK_SCORE_THRESHOLD: float = 0.4

# ── Monetary amount pattern for document evidence extraction ─────────
_AMOUNT_PATTERN: re.Pattern[str] = re.compile(
    r"(?:USD|US\$|\$)\s*([\d,]+(?:\.\d{1,2})?)"
)

# ── Transfer type keywords ───────────────────────────────────────────
_TRANSFER_KEYWORDS: list[str] = [
    "wire transfer",
    "international wire",
    "domestic wire",
    "ach transfer",
    "bank transfer",
    "remittance",
]


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


# ── Round 3: Document evidence helpers ───────────────────────────────


def _has_meaningful_text(doc: SupportingDocument) -> bool:
    """Return True if the document has non-empty extracted text."""
    text = doc.extracted_text
    if text is None:
        return False
    return len(text.strip()) > 0


def _extract_document_evidence(doc: SupportingDocument) -> dict:
    """Extract investigation-relevant evidence from a document.

    Deterministically parses the extracted text for:
    - Monetary amounts (USD patterns)
    - Transfer type keywords
    - Document identification (filename, type)

    Returns a dict with keys:
        - ``doc_label``: Human-readable document identifier.
        - ``amounts``: List of monetary amount strings found.
        - ``transfer_types``: List of transfer type keywords found.
        - ``summary_snippet``: First 200 characters of extracted text.
    """
    text = (doc.extracted_text or "").strip()

    # Document label: prefer file_name, fall back to document_type + id
    doc_label = doc.file_name or f"{doc.document_type} ({doc.document_id})"

    # Extract monetary amounts
    amounts: list[str] = []
    for match in _AMOUNT_PATTERN.finditer(text):
        raw = match.group(1).replace(",", "")
        try:
            float(raw)
            amounts.append(f"USD {match.group(1)}")
        except ValueError:
            pass

    # Detect transfer type keywords (case-insensitive)
    text_lower = text.lower()
    transfer_types: list[str] = [
        kw for kw in _TRANSFER_KEYWORDS if kw in text_lower
    ]

    # Summary snippet (first 200 chars, collapsed whitespace)
    collapsed = " ".join(text.split())
    summary_snippet = collapsed[:200]

    return {
        "doc_label": doc_label,
        "amounts": amounts,
        "transfer_types": transfer_types,
        "summary_snippet": summary_snippet,
    }


def _build_document_evidence_summary(
    documents: list[SupportingDocument],
) -> str:
    """Build a summary paragraph from document evidence.

    Only documents with meaningful extracted text are included.
    Returns an empty string if no meaningful documents are available.
    """
    meaningful_docs = [d for d in documents if _has_meaningful_text(d)]
    if not meaningful_docs:
        return ""

    parts: list[str] = []
    parts.append(
        f"Supporting document evidence ({len(meaningful_docs)} "
        f"document(s)):"
    )

    for doc in meaningful_docs:
        evidence = _extract_document_evidence(doc)
        doc_parts: list[str] = [f"[{evidence['doc_label']}]"]

        if evidence["transfer_types"]:
            doc_parts.append(
                f"references {', '.join(evidence['transfer_types'])}"
            )

        if evidence["amounts"]:
            doc_parts.append(
                f"mentions amount(s): {', '.join(evidence['amounts'])}"
            )

        if not evidence["transfer_types"] and not evidence["amounts"]:
            # Fall back to a snippet of the extracted text
            doc_parts.append(
                f"contains: \"{evidence['summary_snippet']}\""
            )

        parts.append(" ".join(doc_parts))

    return " ".join(parts)


def _build_document_indicators(
    documents: list[SupportingDocument],
) -> list[str]:
    """Build key indicators derived from document evidence.

    Returns an empty list if no meaningful documents are available.
    """
    meaningful_docs = [d for d in documents if _has_meaningful_text(d)]
    if not meaningful_docs:
        return []

    indicators: list[str] = []
    indicators.append(
        f"{len(meaningful_docs)} supporting document(s) with extracted evidence"
    )

    for doc in meaningful_docs:
        evidence = _extract_document_evidence(doc)

        for transfer_type in evidence["transfer_types"]:
            indicators.append(
                f"Document evidence references {transfer_type}"
            )

        for amount in evidence["amounts"]:
            indicators.append(
                f"Document evidence mentions {amount}"
            )

    return indicators


# ── Public API ────────────────────────────────────────────────────────


async def context_agent(state: InvestigationState) -> dict:
    """Execute the Context & Evidence Intelligence Agent.

    Analyses the transactions and customer data inside *state* and
    produces a populated ``ContextIntelligence``.

    Round 5: Fetches historical transactions via MockBankService to
    establish a baseline and detect behavioral deviations.

    Args:
        state: The current investigation state.

    Returns:
        A dict containing ``context_intelligence`` — compatible with
        LangGraph node update conventions.
    """
    # ── Round 5: Defensive data access ───────────────────────────
    # Coalesce to empty lists if the field is unexpectedly None.
    transactions = state.case_input.transactions or []
    supporting_documents = state.case_input.supporting_documents or []

    customer = state.case_input.customer_profile
    alert_reason = state.case_input.alert_reason

    # Safely access optional customer fields — customer may be None
    # or present with only required fields populated.
    customer_name: str | None = getattr(customer, "name", None) if customer else None
    customer_risk: str | None = getattr(customer, "risk_rating", None) if customer else None

    # ── Historical Baseline & Deviation Detection ─────────────────
    historical_baseline: HistoricalBaseline | None = None
    account_id = None
    hist_txns = []

    if transactions:
        account_id = transactions[0].sender_account
        current_txn_ids = {t.transaction_id for t in transactions}
    else:
        current_txn_ids = set()

    if account_id:
        svc = MockBankService()
        async with async_session_factory() as session:
            try:
                raw_hist_txns = await svc.get_account_transactions(session, account_id)
                # Exclude current investigation transactions from the historical baseline
                hist_txns = [t for t in raw_hist_txns if t.transaction_id not in current_txn_ids]
            except Exception:
                pass

        if hist_txns:
            count = len(hist_txns)
            avg = sum(t.amount for t in hist_txns) / count
            max_amt = max(t.amount for t in hist_txns)

            top_types = [t[0] for t in Counter(t.transaction_type for t in hist_txns).most_common(3)]
            top_channels = [t[0] for t in Counter(t.channel for t in hist_txns).most_common(3)]

            locations = [t.location for t in hist_txns if t.location]
            top_locs = [t[0] for t in Counter(locations).most_common(3)] if locations else []

            receivers = [t.receiver_account_id for t in hist_txns if t.receiver_account_id]
            top_receivers = [t[0] for t in Counter(receivers).most_common(3)] if receivers else []

            historical_baseline = HistoricalBaseline(
                transaction_count=count,
                average_amount=round(avg, 2),
                maximum_amount=max_amt,
                common_types=top_types,
                common_channels=top_channels,
                common_locations=top_locs,
                common_counterparties=top_receivers,
            )
        else:
            historical_baseline = HistoricalBaseline()

    # Analyse transactions (unchanged Round 2 logic)
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

    # ── Append Historical Deviations ──────────────────────────────
    deviation_count = 0
    if historical_baseline and historical_baseline.transaction_count > 0:
        hist_types = set(t.transaction_type for t in hist_txns)
        hist_channels = set(t.channel for t in hist_txns)
        hist_locs = set(locations)
        hist_receivers = set(receivers)

        anomaly_counter = len(anomalies)

        for txn in transactions:
            dev_desc = []
            if txn.amount > historical_baseline.maximum_amount * 1.5:
                dev_desc.append(f"amount ${txn.amount:,.2f} is > 1.5x historical max (${historical_baseline.maximum_amount:,.2f})")

            if txn.transaction_type not in hist_types:
                dev_desc.append(f"type '{txn.transaction_type}' never seen in history")

            if txn.channel not in hist_channels:
                dev_desc.append(f"channel '{txn.channel}' never seen in history")

            if txn.location and txn.location not in hist_locs:
                dev_desc.append(f"location '{txn.location}' never seen in history")

            if txn.receiver_account and txn.receiver_account not in hist_receivers:
                dev_desc.append(f"counterparty '{txn.receiver_account}' never seen in history")

            if dev_desc:
                anomaly_counter += 1
                deviation_count += 1
                desc_str = ", ".join(dev_desc).capitalize()
                anomalies.append(
                    DetectedAnomaly(
                        anomaly_id=f"ANOM-{anomaly_counter:03d}",
                        anomaly_type=AnomalyType.BEHAVIORAL,
                        severity=SeverityLevel.MEDIUM,
                        description=f"Deviation: {desc_str}.",
                        related_transactions=[txn.transaction_id],
                    )
                )

    context_summary = _build_context_summary(
        stats, large_txns, rapid_pairs, customer_name, alert_reason, risk_score,
    )

    if historical_baseline and historical_baseline.transaction_count > 0:
        context_summary += f" Compared to a baseline of {historical_baseline.transaction_count} historical transactions (avg ${historical_baseline.average_amount:,.2f}), the current activity shows {deviation_count} notable behavioral deviation(s)."

    # ── Round 3: Document evidence integration ───────────────────
    doc_summary = _build_document_evidence_summary(supporting_documents)
    if doc_summary:
        context_summary = context_summary + " " + doc_summary

    doc_indicators = _build_document_indicators(supporting_documents)
    if doc_indicators:
        key_indicators = key_indicators + doc_indicators

    context = ContextIntelligence(
        status=AgentStatus.COMPLETED,
        context_summary=context_summary,
        key_indicators=key_indicators,
        historical_baseline=historical_baseline,
        anomalies=anomalies,
        risk_score=risk_score,
    )

    return {
        "context_intelligence": context,
    }
