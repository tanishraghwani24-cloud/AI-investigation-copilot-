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
1. BE SPECIFIC AND EVIDENCE-GROUNDED: Do not use generic boilerplate like "Potential suspicious activity was identified." Instead, explicitly state the facts: "A structured wire transfer of $9,900 from entity X to high-risk jurisdiction Y bypasses the $10,000 reporting threshold (Structuring/Smurfing)."
2. CONNECT TO EVIDENCE: Explain exactly *why* a finding is relevant by clearly connecting it to the specific transactions, entities, documents, or anomalies present in the investigation.
3. CONSERVATIVE ON INCOMPLETE DATA: If evidence is incomplete or missing (e.g., missing documents, low-information alerts):
   - Explicitly distinguish what evidence exists from what is missing.
   - State what conclusion can safely be made without inventing facts.
   - If a concern cannot be confirmed, explicitly state that evidence is insufficient, use no evidence references, and do not call it a violation (`is_violated`: false).
4. TRACEABILITY GUARANTEE: Every single value in `evidence_references` MUST be an exact, literal match from the `VALID EVIDENCE IDENTIFIERS` list provided above. Never invent, hallucinate, or guess identifiers.
5. NO HALLUCINATION: Do not claim a regulatory breach, sanctions hit, KYC failure, or fact that the case materials do not establish. 
6. MISSING EVIDENCE GAPS: Use the `evidence_gaps` list to identify missing identity, source-of-funds, transaction, or beneficial-owner documentation that would be needed to resolve ambiguities. Do not claim that supplied evidence is missing.
7. FORMATTING: Return ONLY the raw JSON object. No markdown, no commentary, no conversational text.
"""
