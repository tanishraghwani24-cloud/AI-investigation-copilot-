"""Tests for DEMO_MODE: deterministic agent responses with no live provider.

Two properties matter and are covered here:

1. With ``DEMO_MODE`` off, the production Gemini -> Groq chain is returned
   unchanged — demo mode must be invisible in production.
2. With it on, every LLM-backed agent gets a structurally valid, case-derived
   response, so the pipeline reaches DONE and the report carries real graph data.
"""

import asyncio

import pytest

from app.agents.decision_agent import _DecisionOptionsResponse, _validate_options
from app.agents.reasoning_agent import HypothesesResponse
from app.schemas.investigation_state import (
    BeneficiaryInfo,
    CaseInput,
    CustomerProfile,
    EvidenceComplianceValidation,
    Transaction,
    create_initial_state,
)
from app.services.demo_client import DemoLLMClient
from app.services.demo_data import enrich_case_for_demo
from app.services.gemini_client import GeminiClientError, get_reasoning_client
from app.services.llm_client import FallbackClient


_PROMPT = """
=== CASE DATA ===
{
  "alert_reason": "Rapid cross-border transfers from a cash-intensive account",
  "transactions": [
    {"transaction_id": "TXN-2042-001", "amount": 67500.0, "currency": "USD",
     "sender_account": "ACC-100200", "receiver_account": "ACC-917843"}
  ],
  "customer": {"customer_id": "CUST-13278", "risk_rating": "HIGH"},
  "supporting_documents": [{"document_id": "DOC-0001"}]
}

=== CONTEXT INTELLIGENCE ===
{"risk_score": 0.88, "anomalies": [{"anomaly_id": "ANOM-001"}, {"anomaly_id": "ANOM-002"}]}
"""

_COMPLIANCE_PROMPT = _PROMPT + """
=== VALID EVIDENCE IDENTIFIERS ===
['TXN-2042-001', 'CUST-13278', 'DOC-0001']

=== INSTRUCTIONS ===
"""


# ── Provider selection ───────────────────────────────────────────────


def test_demo_mode_off_returns_production_provider_chain(monkeypatch) -> None:
    """The Gemini -> Groq path must be untouched when the flag is off."""
    from app.core import config

    monkeypatch.setattr(config.settings, "DEMO_MODE", False, raising=False)
    monkeypatch.setattr(config.settings, "GEMINI_API_KEY", "unit-test-key", raising=False)

    assert isinstance(get_reasoning_client(), FallbackClient)


def test_demo_mode_on_returns_deterministic_client(monkeypatch) -> None:
    from app.core import config

    monkeypatch.setattr(config.settings, "DEMO_MODE", True, raising=False)

    assert isinstance(get_reasoning_client(), DemoLLMClient)


@pytest.mark.parametrize("flag", ["true", "TRUE", "1", "yes", "on"])
def test_demo_mode_accepts_string_env_values(monkeypatch, flag: str) -> None:
    """A .env value arrives as a string; it must still enable demo mode."""
    from app.core import config

    monkeypatch.setattr(config.settings, "DEMO_MODE", flag, raising=False)

    assert isinstance(get_reasoning_client(), DemoLLMClient)


@pytest.mark.parametrize("flag", ["false", "", "0", "no"])
def test_demo_mode_string_off_values_use_production_chain(monkeypatch, flag: str) -> None:
    from app.core import config

    monkeypatch.setattr(config.settings, "DEMO_MODE", flag, raising=False)
    monkeypatch.setattr(config.settings, "GEMINI_API_KEY", "unit-test-key", raising=False)

    assert isinstance(get_reasoning_client(), FallbackClient)


def test_demo_mode_fails_closed_on_a_non_boolean_flag(monkeypatch) -> None:
    """An unrecognised value must never swap production for canned answers."""
    from unittest.mock import MagicMock

    from app.core import config

    monkeypatch.setattr(config.settings, "GEMINI_API_KEY", "unit-test-key", raising=False)
    for value in (MagicMock(), object(), None, 2):
        monkeypatch.setattr(config.settings, "DEMO_MODE", value, raising=False)
        assert isinstance(get_reasoning_client(), FallbackClient), value


# ── Structured responses ─────────────────────────────────────────────


def test_demo_hypotheses_are_valid_and_cite_the_case() -> None:
    response = DemoLLMClient().generate(_PROMPT, response_schema=HypothesesResponse)

    assert isinstance(response, HypothesesResponse)
    assert len(response.hypotheses) == 2
    assert len({h.title for h in response.hypotheses}) == 2
    cited = " ".join(
        item for h in response.hypotheses for item in h.supporting_evidence
    )
    assert "TXN-2042-001" in cited
    assert "ANOM-001" in cited


def test_demo_hypotheses_avoid_terms_the_grounding_check_rejects() -> None:
    """Reasoning rejects hypotheses naming data categories the pipeline lacks."""
    response = DemoLLMClient().generate(_PROMPT, response_schema=HypothesesResponse)
    text = " ".join(
        h.title + h.description + " ".join(h.supporting_evidence) + " ".join(h.contradicting_evidence)
        for h in response.hypotheses
    ).lower()

    for forbidden in ("biometric", "facial", "demographic", "kyc", "passport", "invoice"):
        assert forbidden not in text


def test_demo_compliance_references_only_valid_evidence_ids() -> None:
    response = DemoLLMClient().generate(
        _COMPLIANCE_PROMPT, response_schema=EvidenceComplianceValidation
    )

    assert isinstance(response, EvidenceComplianceValidation)
    assert response.compliance_mappings
    allowed = {"TXN-2042-001", "CUST-13278", "DOC-0001"}
    for mapping in response.compliance_mappings:
        assert mapping.evidence_references
        assert set(mapping.evidence_references) <= allowed
    assert response.evidence_gaps


def test_demo_decision_options_satisfy_the_agents_own_validator() -> None:
    response = DemoLLMClient().generate(_PROMPT, response_schema=_DecisionOptionsResponse)

    assert isinstance(response, _DecisionOptionsResponse)
    _validate_options(response.options)  # raises if not exactly the 4 distinct actions
    assert response.recommended_decision is not None
    assert response.decision_rationale
    for option in response.options:
        assert option.pros and option.cons and option.risks and option.mitigation


def test_demo_plain_text_generation_needs_no_schema() -> None:
    assert isinstance(DemoLLMClient().generate(_PROMPT), str)


def test_demo_client_rejects_unknown_schema() -> None:
    class Unknown(CaseInput):
        pass

    with pytest.raises(GeminiClientError, match="no deterministic response"):
        DemoLLMClient().generate(_PROMPT, response_schema=Unknown)


def test_demo_responses_are_deterministic() -> None:
    first = DemoLLMClient().generate(_PROMPT, response_schema=HypothesesResponse)
    second = DemoLLMClient().generate(_PROMPT, response_schema=HypothesesResponse)

    assert first.model_dump() == second.model_dump()


def test_demo_client_tolerates_a_prompt_with_no_identifiers() -> None:
    """A sparse case must still yield a schema-valid response, not an exception."""
    response = DemoLLMClient().generate("no identifiers here", response_schema=HypothesesResponse)

    assert len(response.hypotheses) == 2


# ── Case enrichment ──────────────────────────────────────────────────


def _mock_bank_like_case() -> CaseInput:
    return CaseInput(
        alert_reason="Rapid cross-border transfers",
        customer_profile=CustomerProfile(customer_id="CUST-13278", name="William Vasquez"),
        transactions=[
            Transaction(
                transaction_id="TXN-2042-001", amount=48000.0, currency="USD",
                timestamp="2025-07-15T09:00:00", sender_account="ACC-100200",
                receiver_account="ACC-917843", transaction_type="WIRE", channel="ONLINE",
            ),
            Transaction(
                transaction_id="TXN-2042-003", amount=67500.0, currency="USD",
                timestamp="2025-07-15T11:00:00", sender_account="ACC-100200",
                receiver_account="ACC-421110", transaction_type="WIRE", channel="ONLINE",
            ),
        ],
    )


def test_enrichment_adds_the_entities_the_graph_needs() -> None:
    enriched = enrich_case_for_demo(_mock_bank_like_case())

    assert enriched.beneficiary_info is not None
    assert enriched.merchant_info is not None
    assert enriched.device_info is not None and enriched.device_info.device_id
    # Derived from the largest transaction, not the first.
    assert enriched.beneficiary_info.account_number == "ACC-421110"


def test_enrichment_is_deterministic() -> None:
    assert enrich_case_for_demo(_mock_bank_like_case()).model_dump() == (
        enrich_case_for_demo(_mock_bank_like_case()).model_dump()
    )


def test_enrichment_never_overwrites_supplied_entities() -> None:
    case = _mock_bank_like_case().model_copy(update={
        "beneficiary_info": BeneficiaryInfo(
            beneficiary_id="BEN-REAL", name="Real Counterparty", account_number="ACC-REAL",
        ),
    })

    assert enrich_case_for_demo(case).beneficiary_info.beneficiary_id == "BEN-REAL"


def test_enrichment_leaves_a_case_without_transactions_alone() -> None:
    case = CaseInput(alert_reason="No transactions attached")

    assert enrich_case_for_demo(case) is case


# ── Full pipeline ────────────────────────────────────────────────────


@pytest.fixture()
def mock_gemini_boundary():
    """Override the global boundary mock so the real demo client is exercised."""
    yield


def test_demo_mode_pipeline_reaches_done_with_a_populated_entity_graph(
    monkeypatch, mock_gemini_boundary,
) -> None:
    from app.core import config
    from app.graph.workflow import run_investigation

    monkeypatch.setattr(config.settings, "DEMO_MODE", True, raising=False)
    # No usable credential: the run must not depend on a live provider.
    monkeypatch.setattr(config.settings, "GEMINI_API_KEY", "", raising=False)
    monkeypatch.setattr(config.settings, "GROQ_API_KEY", "", raising=False)

    state = create_initial_state(
        case_id="CASE-DEMO-MODE-001",
        case_input=enrich_case_for_demo(_mock_bank_like_case()),
    )
    result = asyncio.run(run_investigation(state))

    assert result.current_stage.value == "DONE"
    assert result.errors == []
    assert result.investigation_reasoning.hypotheses
    assert result.evidence_compliance_validation.compliance_mappings
    assert len(result.decision_optimization.decision_options) == 4

    graphs = result.investigation_report.graphs
    assert graphs is not None
    entity_graph = graphs.entity_relationship_graph
    assert len(entity_graph.nodes) >= 4
    assert len(entity_graph.edges) >= 3
    assert {node.node_type for node in entity_graph.nodes} >= {
        "PERSON", "MERCHANT", "BENEFICIARY", "DEVICE",
    }
    assert graphs.reasoning_graph.nodes
    assert len(graphs.decision_comparison_graph.nodes) == 4
    assert graphs.investigation_timeline


# ── Global enforcement: no live provider anywhere in demo mode ───────


@pytest.fixture()
def forbid_live_providers(monkeypatch):
    """Turn any real provider construction or request into an immediate failure.

    Covers both layers: the vendor SDK entry points, and the request methods of
    our own client wrappers. If demo mode leaks anywhere, a test using this
    fixture fails loudly instead of quietly spending quota.
    """
    import google.genai as genai_module
    import groq as groq_module

    from app.services.gemini_client import GeminiClient
    from app.services.groq_client import GroqClient

    attempted: list[str] = []

    def _forbid(name: str):
        def _fail(*_args, **_kwargs):
            attempted.append(name)
            raise AssertionError(f"DEMO_MODE must not reach {name}")
        return _fail

    monkeypatch.setattr(genai_module, "Client", _forbid("google.genai.Client"))
    monkeypatch.setattr(groq_module, "Groq", _forbid("groq.Groq"))
    monkeypatch.setattr(GeminiClient, "_request", _forbid("GeminiClient._request"))
    monkeypatch.setattr(GroqClient, "_request", _forbid("GroqClient._request"))
    return attempted


@pytest.fixture()
def demo_mode(monkeypatch):
    """Enable demo mode with credentials that would fail if they were ever used."""
    from app.core import config

    monkeypatch.setattr(config.settings, "DEMO_MODE", True, raising=False)
    monkeypatch.setattr(config.settings, "GEMINI_API_KEY", "must-not-be-used", raising=False)
    monkeypatch.setattr(config.settings, "GROQ_API_KEY", "must-not-be-used", raising=False)


def test_every_provider_factory_returns_the_demo_client(demo_mode, forbid_live_providers) -> None:
    """Enforcement is central: all three factories, not just the agent one."""
    from app.services.gemini_client import get_gemini_client, get_groq_client

    assert isinstance(get_reasoning_client(), DemoLLMClient)
    assert isinstance(get_gemini_client(), DemoLLMClient)
    assert isinstance(get_groq_client(), DemoLLMClient)
    assert forbid_live_providers == []


def test_full_pipeline_touches_no_provider_at_any_stage(
    demo_mode, forbid_live_providers, mock_gemini_boundary,
) -> None:
    """Context, Reasoning, Compliance, Decision and Reporting all stay offline."""
    from app.graph.workflow import run_investigation

    state = create_initial_state(
        case_id="CASE-DEMO-NO-PROVIDER-001",
        case_input=enrich_case_for_demo(_mock_bank_like_case()),
    )
    result = asyncio.run(run_investigation(state))

    assert result.current_stage.value == "DONE"
    assert result.errors == []
    # Every LLM-backed stage produced a valid, populated structure.
    assert result.context_intelligence.status.value == "COMPLETED"
    assert result.investigation_reasoning.hypotheses
    assert result.evidence_compliance_validation.compliance_mappings
    assert len(result.decision_optimization.decision_options) == 4
    assert result.investigation_report.graphs.entity_relationship_graph.nodes
    # The point of the test: nothing tried to reach a provider.
    assert forbid_live_providers == []


def test_document_ocr_path_stays_offline(demo_mode, forbid_live_providers) -> None:
    """Document OCR reaches a provider outside the agent chain, so cover it too."""
    from app.services.document_service import _ocr_via_gemini

    text = _ocr_via_gemini(b"not-a-real-image", "image/png")

    assert "DEMO MODE" in text
    assert forbid_live_providers == []


def test_demo_mode_off_still_builds_real_provider_clients(monkeypatch) -> None:
    """The production path must be entirely unaffected by any of the above."""
    from app.core import config
    from app.services.gemini_client import GeminiClient, get_gemini_client, get_groq_client
    from app.services.groq_client import GroqClient

    monkeypatch.setattr(config.settings, "DEMO_MODE", False, raising=False)
    monkeypatch.setattr(config.settings, "GEMINI_API_KEY", "unit-test-key", raising=False)
    monkeypatch.setattr(config.settings, "GROQ_API_KEY", "unit-test-key", raising=False)
    monkeypatch.setattr("google.genai.Client", lambda **_kwargs: object())
    monkeypatch.setattr("groq.Groq", lambda **_kwargs: object())

    assert isinstance(get_gemini_client(), GeminiClient)
    assert isinstance(get_groq_client(), GroqClient)
    assert isinstance(get_reasoning_client(), FallbackClient)


def test_the_provider_guard_is_not_vacuous(monkeypatch, forbid_live_providers) -> None:
    """Guard against the enforcement tests above silently passing for free.

    With demo mode off, building a client must trip the same guard — otherwise
    ``forbid_live_providers == []`` would prove nothing.
    """
    from app.core import config
    from app.services.gemini_client import get_gemini_client

    monkeypatch.setattr(config.settings, "DEMO_MODE", False, raising=False)
    monkeypatch.setattr(config.settings, "GEMINI_API_KEY", "unit-test-key", raising=False)

    with pytest.raises(AssertionError, match="google.genai.Client"):
        get_gemini_client()
    assert forbid_live_providers == ["google.genai.Client"]


def test_persisted_workflow_path_touches_no_provider(
    demo_mode, forbid_live_providers, mock_gemini_boundary,
) -> None:
    """Cover the path the API actually runs, not just ``run_investigation``.

    ``/investigations/{id}/run`` reaches the pipeline through
    ``run_investigation_with_persistence``; testing only the unpersisted
    entry point would leave the real execution path unproven.
    """
    from unittest.mock import AsyncMock, MagicMock

    from app.graph.workflow import run_investigation_with_persistence

    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    session.add = MagicMock()
    session.flush = AsyncMock()

    state = create_initial_state(
        case_id="CASE-DEMO-PERSISTED-001",
        case_input=enrich_case_for_demo(_mock_bank_like_case()),
    )
    result = asyncio.run(run_investigation_with_persistence(state, session))

    assert result.current_stage.value == "DONE"
    assert result.errors == []
    assert result.investigation_reasoning.hypotheses
    assert result.evidence_compliance_validation.compliance_mappings
    assert len(result.decision_optimization.decision_options) == 4
    assert result.investigation_report.graphs.entity_relationship_graph.nodes
    assert forbid_live_providers == []


def test_health_reports_demo_mode_of_the_running_process(demo_mode) -> None:
    """Lets an operator tell a stale server from a current one."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        body = client.get("/api/health").json()

    assert body["status"] == "ok"
    assert body["demo_mode"] is True
