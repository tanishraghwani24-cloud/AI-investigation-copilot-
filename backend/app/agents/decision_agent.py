"""Decision Agent — Gemini-powered decision option generation.

Takes ``case_input``, ``context_intelligence``, and
``investigation_reasoning`` from the current ``InvestigationState``,
sends the investigation data to Gemini via the existing
``GeminiClient``, and produces exactly FOUR validated
``DecisionOption`` objects — one for each ``DecisionAction``.

Round 3: Option generation only.
Recommendation selection (recommended_decision) belongs to Round 4.
"""

import json as _json
import logging

from pydantic import BaseModel

from app.schemas.investigation_state import (
    AgentStatus,
    DecisionAction,
    DecisionOptimization,
    DecisionOption,
    InvestigationState,
)
from app.services.gemini_client import GeminiClientError, get_reasoning_client

logger = logging.getLogger(__name__)


# ── Private response container ───────────────────────────────────────


class _DecisionOptionsResponse(BaseModel):
    """Container for Gemini structured output.

    This is a module-local helper used exclusively as the
    ``response_schema`` for ``GeminiClient.generate()``.  It is NOT
    part of the shared investigation schema.
    """

    options: list[DecisionOption]
    recommended_decision: DecisionAction
    decision_rationale: str


# ── Prompt construction ──────────────────────────────────────────────



def _build_compact_case_context(state: InvestigationState) -> str:
    """Build a compact JSON summary of case facts and context findings.

    Includes only the fields the Decision Agent needs to evaluate
    risk/action trade-offs.  Full investigative analysis is already
    captured in the ``investigation_reasoning`` output which is passed
    separately.

    Preserved for traceability:
    - Transaction IDs, amounts, currencies, types, sender/receiver accounts
    - Customer ID, name, risk rating
    - Merchant ID, name, category, country, risk level
    - Beneficiary ID, name, country, is_new flag
    - Alert reason
    - Context risk score
    - Anomaly IDs, types, severities, descriptions, related transactions
    - Key indicators

    Note: compliance data is handled separately by
    ``_build_compact_compliance()``.
    """
    case_input = state.case_input
    context = state.context_intelligence

    compact: dict = {"alert_reason": case_input.alert_reason}

    # Transactions: keep all fact fields needed for traceability
    compact["transactions"] = [
        {
            "transaction_id": t.transaction_id,
            "amount": t.amount,
            "currency": t.currency,
            "transaction_type": t.transaction_type,
            "sender_account": t.sender_account,
            "receiver_account": t.receiver_account,
            "timestamp": t.timestamp.isoformat(),
            "channel": t.channel,
        }
        for t in case_input.transactions
    ]

    # Customer: identity + risk rating only
    customer = case_input.customer_profile
    if customer:
        compact["customer"] = {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "risk_rating": customer.risk_rating,
        }

    # Merchant: identity + risk indicators
    merchant = case_input.merchant_info
    if merchant:
        compact["merchant"] = {
            "merchant_id": merchant.merchant_id,
            "name": merchant.name,
            "category": merchant.category,
            "country": merchant.country,
            "risk_level": merchant.risk_level.value if merchant.risk_level else None,
        }

    # Beneficiary: identity + risk indicators
    beneficiary = case_input.beneficiary_info
    if beneficiary:
        compact["beneficiary"] = {
            "beneficiary_id": beneficiary.beneficiary_id,
            "name": beneficiary.name,
            "country": beneficiary.country,
            "is_new": beneficiary.is_new,
        }

    # Context intelligence: risk score, indicators, anomaly summaries
    if context:
        compact["risk_score"] = context.risk_score
        compact["key_indicators"] = context.key_indicators
        compact["anomalies"] = [
            {
                "anomaly_id": a.anomaly_id,
                "anomaly_type": a.anomaly_type.value,
                "severity": a.severity.value,
                "description": a.description,
                "related_transactions": a.related_transactions,
            }
            for a in context.anomalies
        ]

    return _json.dumps(compact, indent=2, default=str)


def _build_compact_compliance(state: InvestigationState) -> str:
    """Build a compact JSON summary of compliance findings.

    Extracts only the fields the Decision Agent needs from the
    ``EvidenceComplianceValidation`` output:

    Per compliance mapping:
    - regulation_id, regulation_name (traceability)
    - is_violated (violation status — critical for action selection)
    - severity (risk level)
    - evidence_references (supporting evidence IDs)

    Top-level:
    - evidence_gaps (missing evidence items)
    - validation_summary (concise compliance review result)

    Excluded:
    - status (agent lifecycle, not decision-relevant)
    - description (verbose text already processed upstream)
    """
    compliance = state.evidence_compliance_validation
    if compliance is None:
        return "{}"

    compact: dict = {}

    compact["compliance_mappings"] = [
        {
            "regulation_id": m.regulation_id,
            "regulation_name": m.regulation_name,
            "is_violated": m.is_violated,
            "severity": m.severity.value,
            "evidence_references": m.evidence_references,
        }
        for m in compliance.compliance_mappings
    ]

    compact["evidence_gaps"] = compliance.evidence_gaps

    if compliance.validation_summary:
        compact["validation_summary"] = compliance.validation_summary

    return _json.dumps(compact, indent=2, default=str)


def _build_prompt(state: InvestigationState) -> str:
    """Build a Gemini prompt from the investigation state.

    Uses a compact case+context summary (essential facts only) combined
    with the full investigation reasoning output and a compact compliance
    summary.  This avoids sending duplicated or unnecessary data to the
    LLM while preserving all transaction IDs, evidence references, and
    risk indicators needed for grounded decision-making.
    """
    compact_context = _build_compact_case_context(state)
    compact_compliance = _build_compact_compliance(state)

    if state.investigation_reasoning is not None:
        reasoning_json = state.investigation_reasoning.model_dump_json(indent=2)
    else:
        reasoning_json = "{}"

    prompt = f"""\
You are a senior financial crime decision analyst.  Given the
investigation data below, generate exactly FOUR decision options —
one for each possible action. Then, select exactly ONE recommended decision
from these options and provide a detailed rationale comparing it to the alternatives.

=== CASE SUMMARY AND CONTEXT ===
{compact_context}

=== INVESTIGATION REASONING ===
{reasoning_json}

=== COMPLIANCE FINDINGS ===
{compact_compliance}

=== INSTRUCTIONS ===
Respond with a single JSON object (no markdown fences, no extra text)
that conforms to the following schema:

{{
  "options": [
    {{
      "option_id": "<string – e.g. OPT-ALLOW>",
      "action": "<one of: ALLOW, HOLD, BLOCK, ESCALATE>",
      "rationale": "<string – case-specific explanation of why this action could be appropriate>",
      "confidence": <float between 0.0 and 1.0>,
      "risk_score": <float between 0.0 and 1.0>,
      "pros": ["<at least two distinct case-specific advantages>"],
      "cons": ["<at least two distinct case-specific disadvantages>"],
      "risks": ["<at least two distinct named risks>"],
      "mitigation": ["<at least two distinct mitigation steps>"]
    }}
  ],
  "recommended_decision": "<one of: ALLOW, HOLD, BLOCK, ESCALATE>",
  "decision_rationale": "<string – explanation of why the recommended action is best for this specific case, comparing it against the alternatives>"
}}

Rules:
- You MUST produce exactly 4 options, one for each action: ALLOW, HOLD, BLOCK, ESCALATE.
- Each action value MUST appear exactly once in the options array.
- The recommended_decision MUST be one of the four actions.
- The decision_rationale MUST compare the recommended decision to the other options based on the case facts.
- All rationales MUST reference specific data from the case summary, context, compliance findings, or reasoning above.
- pros, cons, risks, and mitigation MUST each have AT LEAST TWO entries. Do not use generic boilerplate.
- confidence and risk_score MUST be between 0.0 and 1.0 inclusive.
- Use option_id values: OPT-ALLOW, OPT-HOLD, OPT-BLOCK, OPT-ESCALATE.
- Return ONLY the raw JSON object.  No markdown, no commentary.
"""
    return prompt


# ── Validation ───────────────────────────────────────────────────────


_REQUIRED_ACTIONS = frozenset(DecisionAction)


def _validate_options(options: list[DecisionOption]) -> None:
    """Validate that Gemini returned exactly 4 distinct action options.

    Raises:
        GeminiClientError: If the count is wrong or actions are
            missing / duplicated.
    """
    if len(options) != 4:
        raise GeminiClientError(
            f"Expected exactly 4 decision options, got {len(options)}"
        )

    found_actions = {opt.action for opt in options}
    if found_actions != _REQUIRED_ACTIONS:
        missing = _REQUIRED_ACTIONS - found_actions
        extra = found_actions - _REQUIRED_ACTIONS
        raise GeminiClientError(
            f"Decision options have wrong actions. "
            f"Missing: {missing}, Extra/Duplicate: {extra}"
        )


# ── Public API ────────────────────────────────────────────────────────


def decision_agent(state: InvestigationState) -> dict:
    """Execute the Decision Agent.

    Reads case data, context intelligence, and investigation
    reasoning from *state*, constructs a prompt, calls Gemini via
    ``GeminiClient.generate()``, and wraps the validated
    ``DecisionOption`` objects in a ``DecisionOptimization``.

    Round 3 produces the four options only.
    ``recommended_decision`` and ``decision_rationale`` are not
    set — recommendation selection belongs to Round 4.

    Args:
        state: The current investigation state.

    Returns:
        A dict containing ``decision_optimization`` — compatible
        with LangGraph node update conventions.
    """
    prompt = _build_prompt(state)

    client = get_reasoning_client()

    try:
        response: _DecisionOptionsResponse = client.generate(
            prompt,
            response_schema=_DecisionOptionsResponse,
        )
    except GeminiClientError:
        logger.exception("Gemini call failed in decision_agent")
        raise

    _validate_options(response.options)

    decision = DecisionOptimization(
        status=AgentStatus.COMPLETED,
        decision_options=response.options,
        recommended_decision=response.recommended_decision,
        decision_rationale=response.decision_rationale,
    )

    return {
        "decision_optimization": decision,
    }
