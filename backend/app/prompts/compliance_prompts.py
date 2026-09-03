"""Compliance Agent Prompts.

Contains the prompt templates and builders for the Gemini-powered
Compliance Agent. Extracted for quality tuning in Round 7.
"""

def build_compliance_prompt(
    case_json: str,
    context_json: str,
    reasoning_json: str,
    valid_evidence_ids: list[str],
) -> str:
    """Build the prompt for generating evidence-backed compliance mappings.
    
    Instructs the LLM to act as an AML/KYC investigation assistant, producing
    specific, evidence-grounded findings and adhering strictly to the provided
    evidence identifiers.
    """
    return f"""\
You are an expert AML/KYC compliance investigation assistant. 
Your task is to review the case materials and identify regulatory compliance concerns, missing evidence gaps, and KYC findings.

=== CASE INPUT ===
{case_json}

=== CONTEXT INTELLIGENCE ===
{context_json}

=== INVESTIGATION REASONING ===
{reasoning_json}

=== VALID EVIDENCE IDENTIFIERS ===
{valid_evidence_ids}

=== INSTRUCTIONS ===
Return ONLY a JSON object containing `compliance_mappings`, `evidence_gaps`, and a `validation_summary`. 
Each item in `compliance_mappings` must contain: `regulation_id`, `regulation_name`, `description`, `is_violated`, `severity` (LOW, MEDIUM, or HIGH), and `evidence_references`.

=== QUALITY RULES & CONSTRAINTS ===
1. STRICT EVIDENCE GROUNDING: You MUST NOT invent, alter, or hallucinate transaction amounts, transaction IDs, transaction directions (sender/receiver), counterparties, jurisdictions, dates, or regulatory thresholds.
2. NO ASSUMED INTENT: Do not claim intentional criminal/regulatory conduct (such as "structuring" or "smurfing") unless the supplied evidence explicitly establishes it.
3. DISTINGUISH SIGNALS FROM VIOLATIONS: 
   - A suspicious indicator or risk signal is NOT a confirmed violation.
   - Set `is_violated`: false if the evidence only indicates a potential concern or risk signal.
   - Set `is_violated`: true ONLY if the supplied evidence incontrovertibly establishes a violation of a specific regulation.
4. EXACT AMOUNTS AND DIRECTIONS: Use the exact amounts and currencies provided in the case data. Do not alter them to fit a regulatory threshold. Ensure the sender and receiver are accurately described.
5. CONNECT TO EVIDENCE: Explain exactly *why* a finding is relevant by clearly connecting it to the specific transactions, entities, documents, or anomalies present.
6. CONSERVATIVE ON INCOMPLETE DATA: If evidence is incomplete, explicitly state what evidence exists and what is missing. If a concern cannot be confirmed, state that evidence is insufficient.
7. TRACEABILITY GUARANTEE: Every single value in `evidence_references` MUST be an exact, literal match from the `VALID EVIDENCE IDENTIFIERS` list provided above. Never invent or guess identifiers.
8. MISSING EVIDENCE GAPS: Use the `evidence_gaps` list to identify missing identity, source-of-funds, or transaction documentation needed to resolve ambiguities.
9. FORMATTING: Return ONLY the raw JSON object. No markdown, no commentary, no conversational text."""
