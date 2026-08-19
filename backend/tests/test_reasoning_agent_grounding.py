import pytest
from datetime import datetime

from app.schemas.investigation_state import (
    InvestigationState,
    CaseInput,
    Transaction,
    InvestigationReasoning
)
from app.agents.reasoning_agent import reasoning_agent

def test_reasoning_agent_grounding_no_hallucination():
    """
    Ensure the reasoning agent does not hallucinate unavailable information.
    A. No customer profile
    B. No transaction history beyond what's supplied
    C. No biometrics
    D. No documents
    E. No alerts/risk indicators
    F. Known anomaly ($950 vs normal <$100) must remain usable
    G. Hypotheses explicitly investigative possibilities
    """
    
    # Setup sparse state exactly like the failing grounding test
    case_input = CaseInput(
        description=(
            "Only the following facts are known: Account A normally transfers less than $100. "
            "Transaction TX-001 transfers exactly $950 from Account A to Account B. "
            "No other facts, documents, alerts, biometrics, customer profile information, "
            "or transaction history are available."
        ),
        transactions=[
            Transaction(
                transaction_id='TX-001',
                timestamp=datetime(2026, 8, 19, 12, 0, 0),
                amount=950.0,
                currency='USD',
                sender_account='Account A',
                receiver_account='Account B',
                transaction_type='transfer'
            )
        ]
    )
    
    state = InvestigationState(
        case_id='TEST-OLLAMA-GROUNDING-001',
        case_input=case_input
    )
    
    # Run the reasoning agent (which hits the real model via Ollama)
    result = reasoning_agent(state)
    
    assert 'investigation_reasoning' in result
    reasoning = result['investigation_reasoning']
    assert isinstance(reasoning, InvestigationReasoning)
    
    # Must have competing hypotheses
    assert len(reasoning.hypotheses) >= 2
    
    forbidden_terms = [
        "biometric", "face", "facial", 
        "history", "past behavior", "previous transactions", "historical",
        "profile", "demographic", "kyc",
        "document", "passport", "id card", "invoice",
        "alert", "risk indicator",
        "channel", "mobile", "web", "ip address", "device"
    ]
    
    for hyp in reasoning.hypotheses:
        text_to_check = (hyp.title + " " + hyp.description).lower()
        
        # split by recommendation to avoid failing when the model rightly recommends verifying these things
        text_parts = text_to_check.split("recommend")
        factual_claims = text_parts[0]
        
        # A, B, C, D, E: Ensure none of the forbidden hallucinated concepts are mentioned in the factual claims
        for term in forbidden_terms:
            assert term not in factual_claims, f"Hallucinated forbidden term '{term}' found in factual claims of hypothesis: {factual_claims}"
            
        # G: Hypotheses must remain explicitly investigative possibilities
        # In sparse cases, confidence is capped and uncertainty text is appended by `_normalise_hypotheses`
        # But we also instructed the LLM to explicitly state evidence is limited.
        assert "evidence is limited" in text_to_check or "possibility" in text_to_check
        assert hyp.confidence <= 0.5
        
        # Ensure that no invented evidence slipped into supporting/contradicting evidence
        for ev in hyp.supporting_evidence + hyp.contradicting_evidence:
            ev_lower = ev.lower()
            for term in forbidden_terms:
                assert term not in ev_lower, f"Hallucinated forbidden term '{term}' found in evidence item: {ev}"

    # F: The known anomaly must remain usable. It should be mentioned somewhere.
    all_text = " ".join([h.title + " " + h.description for h in reasoning.hypotheses]).lower()
    assert "950" in all_text or "100" in all_text or "account a" in all_text or "account b" in all_text
