"""Deterministic offline stand-in for the reasoning LLM (``DEMO_MODE=true``).

Live Gemini/Groq quota exhaustion must not be able to stall a demo, so this
client returns the *same* Pydantic structures the production Gemini -> Groq path
returns, without any network call.  It is never constructed unless
``settings.DEMO_MODE`` is true.  Every provider-client factory in
``gemini_client`` -- ``get_reasoning_client``, ``get_gemini_client`` and
``get_groq_client`` -- hands this back under demo mode, so the agent chain and
the document-OCR path are both covered; with the flag off they all return the
real provider chain untouched.

The responses are derived from the identifiers and figures already present in
the caller's prompt rather than from fixed placeholder text, so hypotheses,
compliance findings and decision options cite the case actually under
investigation.  That matters for more than cosmetics: the agents strip evidence
references that do not resolve against the investigation state, so only
genuinely case-derived identifiers survive normalisation and reach the report
and its graphs.

Output is a pure function of the prompt — the same case always produces the same
report, which is what makes a demo repeatable.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from pydantic import BaseModel

from app.schemas.investigation_state import (
    AgentStatus,
    ComplianceMapping,
    DecisionAction,
    DecisionOption,
    Hypothesis,
    SeverityLevel,
)
from app.services.gemini_client import GeminiClientError

logger = logging.getLogger(__name__)


# Identifier families the agents emit into evidence lists. Kept deliberately
# broad: the agents themselves decide which of these survive grounding checks.
_IDENTIFIER_PATTERN = re.compile(r"\b(?:TXN|DOC|CUST|ACC|ANOM|DEV|MERCH|BEN|EVID)-[A-Z0-9][A-Z0-9-]*\b")

# The compliance prompt lists the only references that survive normalisation.
_VALID_ID_SECTION = re.compile(
    r"=== VALID EVIDENCE IDENTIFIERS ===\s*(.*?)\s*===", re.DOTALL
)

_AMOUNT_PATTERN = re.compile(r'"amount":\s*([0-9]+(?:\.[0-9]+)?)')
_CURRENCY_PATTERN = re.compile(r'"currency":\s*"([A-Z]{3})"')
_RISK_SCORE_PATTERN = re.compile(r'"risk_score":\s*([0-9]*\.?[0-9]+)')
_ALERT_REASON_PATTERN = re.compile(r'"alert_reason":\s*"([^"]{4,300})"')

# Risk thresholds separating the recommended action in demo output.
_ESCALATE_ABOVE = 0.75
_HOLD_ABOVE = 0.45


def _ordered_unique(values: list[str]) -> list[str]:
    """De-duplicate *values* while preserving first-seen order."""
    return list(dict.fromkeys(values))


@dataclass
class _CaseFacts:
    """Concrete facts recovered from an agent prompt."""

    transaction_ids: list[str] = field(default_factory=list)
    document_ids: list[str] = field(default_factory=list)
    anomaly_ids: list[str] = field(default_factory=list)
    customer_ids: list[str] = field(default_factory=list)
    valid_evidence_ids: list[str] = field(default_factory=list)
    top_amount: float | None = None
    currency: str = "USD"
    risk_score: float = 0.5
    alert_reason: str | None = None

    @property
    def primary_transaction(self) -> str | None:
        return self.transaction_ids[0] if self.transaction_ids else None

    @property
    def amount_phrase(self) -> str:
        """Render the largest observed amount, or a neutral phrase if none."""
        if self.top_amount is None:
            return "the flagged amount"
        return f"{self.top_amount:,.2f} {self.currency}"


def _extract_facts(prompt: str) -> _CaseFacts:
    """Recover the concrete case facts embedded in *prompt*."""
    identifiers = _IDENTIFIER_PATTERN.findall(prompt.upper())
    facts = _CaseFacts(
        transaction_ids=_ordered_unique([i for i in identifiers if i.startswith("TXN-")]),
        document_ids=_ordered_unique([i for i in identifiers if i.startswith("DOC-")]),
        anomaly_ids=_ordered_unique([i for i in identifiers if i.startswith("ANOM-")]),
        customer_ids=_ordered_unique([i for i in identifiers if i.startswith("CUST-")]),
    )

    # The compliance prompt states its own allow-list; prefer it verbatim so
    # references match the agent's available-id set exactly (case included).
    section = _VALID_ID_SECTION.search(prompt)
    if section:
        facts.valid_evidence_ids = _ordered_unique(
            _IDENTIFIER_PATTERN.findall(section.group(1).upper())
        )
    if not facts.valid_evidence_ids:
        facts.valid_evidence_ids = _ordered_unique(identifiers)

    amounts = [float(value) for value in _AMOUNT_PATTERN.findall(prompt)]
    if amounts:
        facts.top_amount = max(amounts)
    currency = _CURRENCY_PATTERN.search(prompt)
    if currency:
        facts.currency = currency.group(1)
    risk = _RISK_SCORE_PATTERN.search(prompt)
    if risk:
        try:
            facts.risk_score = min(1.0, max(0.0, float(risk.group(1))))
        except ValueError:  # pragma: no cover - regex already constrains this
            pass
    alert = _ALERT_REASON_PATTERN.search(prompt)
    if alert:
        facts.alert_reason = alert.group(1)
    return facts


def _severity_for(risk_score: float) -> SeverityLevel:
    if risk_score >= _ESCALATE_ABOVE:
        return SeverityLevel.HIGH
    if risk_score >= _HOLD_ABOVE:
        return SeverityLevel.MEDIUM
    return SeverityLevel.LOW


class DemoLLMClient:
    """Deterministic ``generate()`` implementation used only in demo mode."""

    def generate(self, prompt: str, response_schema: type[BaseModel] | None = None):
        """Mirror the provider contract: plain text, or a validated model."""
        if response_schema is None:
            return (
                "Demo mode is active; this narrative is generated deterministically "
                "from the supplied case data without contacting an LLM provider."
            )

        facts = _extract_facts(prompt)
        builder = {
            "HypothesesResponse": self._hypotheses,
            "EvidenceComplianceValidation": self._compliance,
            "_DecisionOptionsResponse": self._decision_options,
        }.get(response_schema.__name__)

        if builder is None:
            # Surfacing the provider error type keeps demo-mode failures on the
            # same handling path the agents already implement for live calls.
            raise GeminiClientError(
                f"Demo mode has no deterministic response for schema "
                f"{response_schema.__name__!r}."
            )

        logger.info(
            "provider=demo schema=%s transactions=%d",
            response_schema.__name__, len(facts.transaction_ids),
        )
        return builder(response_schema, facts)

    def generate_with_image(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/png",
    ) -> str:
        """Stand in for Gemini Vision OCR (document processing path).

        Document OCR reaches a provider through ``get_gemini_client()`` rather
        than the agent chain, so demo mode has to answer here too or an uploaded
        scan would still spend live quota. The text is a clearly-labelled
        placeholder: inventing plausible document contents would put words into
        an investigator's evidence file that nobody actually extracted.
        """
        logger.info("provider=demo generate_with_image bytes=%d mime=%s", len(image_bytes), mime_type)
        return (
            "[DEMO MODE] Document text extraction is simulated; no OCR provider "
            f"was contacted for this {mime_type} upload."
        )

    # ── Reasoning ────────────────────────────────────────────────────

    @staticmethod
    def _hypotheses(schema: type[BaseModel], facts: _CaseFacts) -> BaseModel:
        """Two competing, evidence-cited hypotheses, as the prompt demands.

        Evidence strings embed real identifiers so they survive the reasoning
        agent's ``_evidence_is_available`` filter instead of being stripped.
        """
        evidence: list[str] = []
        if facts.primary_transaction:
            evidence.append(
                f"Transaction {facts.primary_transaction} recorded for {facts.amount_phrase}"
            )
        evidence += [f"Anomaly {anomaly} raised on this account" for anomaly in facts.anomaly_ids[:2]]
        evidence += [
            f"Supporting document {document} attached to the case"
            for document in facts.document_ids[:1]
        ]
        if not evidence and facts.customer_ids:
            evidence.append(f"Customer record {facts.customer_ids[0]} under review")

        counter_evidence = [
            f"Transaction {txn} is consistent with the account's ordinary settlement pattern"
            for txn in facts.transaction_ids[1:3]
        ]

        elevated = round(min(0.85, max(0.35, facts.risk_score)), 2)
        benign = round(min(0.6, max(0.1, 1.0 - facts.risk_score)), 2)

        return schema(hypotheses=[
            Hypothesis(
                hypothesis_id="HYP-001",
                title="Unauthorised third-party use of the account",
                description=(
                    f"It is possible that the activity totalling {facts.amount_phrase} was "
                    "initiated by a party other than the account holder. The flagged "
                    "movement departs from the account's established pattern, which is "
                    "consistent with control of the account having passed to a third "
                    "party. Recommend confirming the instruction directly with the "
                    "account holder before releasing further funds."
                ),
                confidence=elevated,
                supporting_evidence=evidence[:3],
                contradicting_evidence=counter_evidence[:2],
            ),
            Hypothesis(
                hypothesis_id="HYP-002",
                title="Customer-authorised activity flagged by threshold rules",
                description=(
                    f"It is possible that the account holder genuinely authorised the "
                    f"{facts.amount_phrase} movement and that the alert reflects a "
                    "monitoring threshold rather than misuse. A legitimate one-off "
                    "settlement can exceed a routine profile without any irregularity. "
                    "Recommend verifying the stated purpose of the payment with the "
                    "customer to close or confirm the alert."
                ),
                confidence=benign,
                supporting_evidence=evidence[:2],
                contradicting_evidence=counter_evidence[:1],
            ),
        ])

    # ── Compliance ───────────────────────────────────────────────────

    @staticmethod
    def _compliance(schema: type[BaseModel], facts: _CaseFacts) -> BaseModel:
        """Evidence-referenced compliance findings drawn from the case ids."""
        references = facts.valid_evidence_ids[:3]
        severity = _severity_for(facts.risk_score)

        mappings = [
            ComplianceMapping(
                regulation_id="BSA-1020.320",
                regulation_name="Bank Secrecy Act — Suspicious Activity Reporting",
                description=(
                    f"Activity of {facts.amount_phrase} meets the internal review "
                    "threshold for suspicious activity reporting. The evidence "
                    "indicates a reportable concern rather than an established "
                    "violation, so escalation for analyst review is warranted."
                ),
                is_violated=False,
                severity=severity,
                evidence_references=references,
            ),
            ComplianceMapping(
                regulation_id="FATF-R16",
                regulation_name="FATF Recommendation 16 — Wire Transfer Information",
                description=(
                    "Originator and beneficiary details accompanying the flagged "
                    "movement should be confirmed complete before the funds are "
                    "released. No shortfall is established on the present evidence."
                ),
                is_violated=False,
                severity=SeverityLevel.LOW,
                evidence_references=references[:2],
            ),
            ComplianceMapping(
                regulation_id="AMLD5-ART18",
                regulation_name="5AMLD Article 18 — Enhanced Due Diligence",
                description=(
                    "The risk profile attached to this activity supports applying "
                    "enhanced due diligence to the counterparty before the "
                    "relationship continues."
                ),
                is_violated=False,
                severity=severity,
                evidence_references=references[:1],
            ),
        ]

        return schema(
            status=AgentStatus.COMPLETED,
            compliance_mappings=mappings,
            evidence_gaps=[
                "Customer confirmation of the payment purpose has not been obtained",
                "Counterparty ownership details are not evidenced in the case file",
            ],
            validation_summary=(
                f"Deterministic demo review mapped {len(mappings)} regulatory "
                f"considerations to {len(references)} case evidence reference(s); "
                "no confirmed violation is established on the available evidence."
            ),
        )

    # ── Decision ─────────────────────────────────────────────────────

    @staticmethod
    def _decision_options(schema: type[BaseModel], facts: _CaseFacts) -> BaseModel:
        """All four actions the decision agent requires, plus a recommendation."""
        risk = facts.risk_score
        if risk >= _ESCALATE_ABOVE:
            recommended = DecisionAction.ESCALATE
        elif risk >= _HOLD_ABOVE:
            recommended = DecisionAction.HOLD
        else:
            recommended = DecisionAction.ALLOW

        options = [
            DecisionOption(
                option_id="OPT-ESCALATE",
                action=DecisionAction.ESCALATE,
                rationale=(
                    f"Refer the {facts.amount_phrase} activity to the financial crime "
                    "team for a full review and a reporting determination."
                ),
                confidence=round(min(0.92, 0.55 + risk * 0.4), 2),
                risk_score=round(min(1.0, risk + 0.05), 2),
                pros=["Preserves the reporting window", "Places the judgement with trained reviewers"],
                cons=["Consumes specialist analyst capacity", "Delays resolution for the customer"],
                risks=["Alert backlog grows if escalation volume is high"],
                mitigation=["Attach the assembled evidence pack so review starts from a complete file"],
            ),
            DecisionOption(
                option_id="OPT-HOLD",
                action=DecisionAction.HOLD,
                rationale=(
                    "Suspend settlement pending direct confirmation of the payment "
                    "purpose from the account holder."
                ),
                confidence=round(min(0.88, 0.5 + risk * 0.35), 2),
                risk_score=round(min(1.0, max(0.0, risk)), 2),
                pros=["Prevents loss while the facts are confirmed", "Reversible once contact succeeds"],
                cons=["Customer experiences an unexplained delay"],
                risks=["A legitimate time-critical payment may miss its value date"],
                mitigation=["Attempt customer contact on a verified channel within one business day"],
            ),
            DecisionOption(
                option_id="OPT-BLOCK",
                action=DecisionAction.BLOCK,
                rationale=(
                    "Reject the activity outright and restrict the account pending "
                    "a full investigation."
                ),
                confidence=round(min(0.8, 0.3 + risk * 0.45), 2),
                risk_score=round(min(1.0, risk + 0.1), 2),
                pros=["Removes further exposure immediately"],
                cons=["Severe customer impact if the activity proves legitimate"],
                risks=["Complaint or regulatory challenge where the block is unfounded"],
                mitigation=["Require a documented second-line approval before the block is applied"],
            ),
            DecisionOption(
                option_id="OPT-ALLOW",
                action=DecisionAction.ALLOW,
                rationale=(
                    "Release the activity and close the alert as consistent with "
                    "expected account behaviour."
                ),
                confidence=round(min(0.75, max(0.15, 1.0 - risk)), 2),
                risk_score=round(max(0.0, risk - 0.25), 2),
                pros=["No customer friction", "Keeps the review queue focused on stronger signals"],
                cons=["Accepts the residual risk that the concern was genuine"],
                risks=["A reportable event could go unreported"],
                mitigation=["Retain the case file and re-review if further alerts follow"],
            ),
        ]

        return schema(
            options=options,
            recommended_decision=recommended,
            decision_rationale=(
                f"With an assessed risk score of {risk:.2f}, {recommended.value} balances "
                "containment against customer impact on the evidence currently available."
            ),
        )
