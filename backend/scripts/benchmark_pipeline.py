"""Pipeline Performance Benchmark.

Runs a realistic investigation case through each pipeline stage
individually, measuring wall-clock time, prompt sizes, output sizes,
and Ollama timing data for each LLM call.

Usage:
    python scripts/benchmark_pipeline.py

Does NOT modify any production code or settings.
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure backend root on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from app.schemas import (
    BeneficiaryInfo,
    CaseInput,
    CustomerProfile,
    DeviceInfo,
    MerchantInfo,
    SeverityLevel,
    SupportingDocument,
    Transaction,
    create_initial_state,
)
from app.schemas.investigation_state import InvestigationState


# ── Build the same realistic demo case as run_demo.py ────────────────

def build_demo_case():
    transaction = Transaction(
        transaction_id="TXN-2025-0819-00347",
        amount=48_500.00,
        currency="USD",
        timestamp=datetime(2025, 8, 19, 14, 32, 11),
        sender_account="ACC-US-8821004",
        receiver_account="ACC-KY-5529183",
        transaction_type="WIRE",
        channel="ONLINE",
        description="Investment deposit - CryptoVault Holdings",
        location="New York, US",
    )
    customer = CustomerProfile(
        customer_id="CUST-90215",
        name="James Whitfield",
        email="j.whitfield@email.com",
        phone="+1-212-555-0173",
        address="350 Park Avenue, New York, NY 10022",
        date_of_birth="1983-04-12",
        account_open_date="2019-06-15",
        risk_rating="MEDIUM",
        occupation="Portfolio Manager",
        nationality="US",
    )
    merchant = MerchantInfo(
        merchant_id="MERCH-KY-7741",
        name="CryptoVault Holdings Ltd.",
        category="Cryptocurrency Exchange",
        country="KY",
        risk_level=SeverityLevel.HIGH,
        registered_date="2023-01-20",
    )
    device = DeviceInfo(
        device_id="DEV-UNKNOWN-8812",
        device_type="MOBILE",
        ip_address="185.220.101.34",
        geolocation="Bucharest, Romania",
        is_known_device=False,
        os="Android 14",
        browser="Chrome Mobile 126",
    )
    beneficiary = BeneficiaryInfo(
        beneficiary_id="BEN-KY-3319",
        name="CryptoVault Holdings Ltd.",
        account_number="ACC-KY-5529183",
        bank_name="Cayman National Bank",
        country="KY",
        is_new=True,
        relationship="Investment Platform",
    )
    supporting_doc = SupportingDocument(
        document_id="DOC-2025-0441",
        document_type="BANK_STATEMENT",
        file_name="whitfield_aug2025_statement.pdf",
        uploaded_at=datetime(2025, 8, 19, 15, 0, 0),
        summary="Monthly statement showing irregular outbound transfers.",
    )
    case_input = CaseInput(
        transactions=[transaction],
        customer_profile=customer,
        merchant_info=merchant,
        device_info=device,
        beneficiary_info=beneficiary,
        supporting_documents=[supporting_doc],
        alert_reason=(
            "Large wire transfer to a first-time beneficiary in a high-risk "
            "jurisdiction, initiated from an unknown device with geolocation "
            "mismatch (device in Romania, customer based in New York)."
        ),
    )
    return "CASE-BENCH-001", case_input


# ── Isolated Ollama call with timing capture ─────────────────────────

def ollama_generate_with_timing(prompt, format_schema=None):
    """Make a raw Ollama API call and capture all timing data."""
    from app.core.config import settings

    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": int(getattr(settings, "OLLAMA_NUM_CTX", 2048)),
            "num_predict": int(getattr(settings, "OLLAMA_NUM_PREDICT", 1024)),
            "temperature": float(getattr(settings, "OLLAMA_TEMPERATURE", 0.0)),
        },
    }
    keep_alive = getattr(settings, "OLLAMA_KEEP_ALIVE", "5m")
    if keep_alive:
        payload["keep_alive"] = keep_alive
    if format_schema is not None:
        payload["format"] = format_schema

    timeout = float(getattr(settings, "OLLAMA_TIMEOUT_SECONDS", 600.0))

    wall_start = time.perf_counter()
    with httpx.Client(base_url=settings.OLLAMA_BASE_URL, timeout=timeout) as client:
        response = client.post("/api/generate", json=payload)
        response.raise_for_status()
    wall_end = time.perf_counter()

    data = response.json()
    return {
        "response_text": data.get("response", ""),
        "wall_time_s": wall_end - wall_start,
        # Ollama timing fields (nanoseconds)
        "total_duration_ns": data.get("total_duration", 0),
        "load_duration_ns": data.get("load_duration", 0),
        "prompt_eval_count": data.get("prompt_eval_count", 0),
        "prompt_eval_duration_ns": data.get("prompt_eval_duration", 0),
        "eval_count": data.get("eval_count", 0),
        "eval_duration_ns": data.get("eval_duration", 0),
    }


def ns_to_s(ns):
    return ns / 1_000_000_000 if ns else 0.0


def print_ollama_timing(label, prompt_chars, result):
    """Print detailed timing for one Ollama call."""
    total_s = ns_to_s(result["total_duration_ns"])
    load_s = ns_to_s(result["load_duration_ns"])
    prefill_s = ns_to_s(result["prompt_eval_duration_ns"])
    gen_s = ns_to_s(result["eval_duration_ns"])
    prompt_tokens = result["prompt_eval_count"]
    gen_tokens = result["eval_count"]
    output_chars = len(result["response_text"])

    prefill_tps = prompt_tokens / prefill_s if prefill_s > 0 else 0
    gen_tps = gen_tokens / gen_s if gen_s > 0 else 0

    print(f"\n  --- {label} ---")
    print(f"  Wall-clock time:       {result['wall_time_s']:>8.2f}s")
    print(f"  Ollama total:          {total_s:>8.2f}s")
    print(f"  Model load:            {load_s:>8.2f}s")
    print(f"  Prompt eval (prefill): {prefill_s:>8.2f}s  ({prompt_tokens} tokens @ {prefill_tps:.1f} tok/s)")
    print(f"  Generation (decode):   {gen_s:>8.2f}s  ({gen_tokens} tokens @ {gen_tps:.1f} tok/s)")
    print(f"  Input chars:           {prompt_chars:>8d}")
    print(f"  Input tokens (actual): {prompt_tokens:>8d}")
    print(f"  Output chars:          {output_chars:>8d}")
    print(f"  Output tokens (actual):{gen_tokens:>8d}")

    return {
        "label": label,
        "wall_s": result["wall_time_s"],
        "total_s": total_s,
        "load_s": load_s,
        "prefill_s": prefill_s,
        "gen_s": gen_s,
        "prompt_tokens": prompt_tokens,
        "gen_tokens": gen_tokens,
        "prompt_chars": prompt_chars,
        "output_chars": output_chars,
        "prefill_tps": prefill_tps,
        "gen_tps": gen_tps,
    }


# ── Main Benchmark ───────────────────────────────────────────────────

async def main():
    print("=" * 70)
    print("  INVESTIGATION PIPELINE PERFORMANCE BENCHMARK")
    print("=" * 70)

    from app.core.config import settings
    print(f"\n  Model:    {settings.OLLAMA_MODEL}")
    print(f"  Provider: {settings.REASONING_LLM_PROVIDER}")
    print(f"  Timeout:  {settings.OLLAMA_TIMEOUT_SECONDS}s")
    print(f"  num_ctx:  {getattr(settings, 'OLLAMA_NUM_CTX', 2048)}")
    print(f"  num_predict: {getattr(settings, 'OLLAMA_NUM_PREDICT', 1024)}")

    case_id, case_input = build_demo_case()
    state = create_initial_state(case_id=case_id, case_input=case_input)

    results = []
    stage_times = {}

    # ── Stage 1: Context Intelligence (deterministic) ────────────────
    print("\n\n[1/5] Context Intelligence (deterministic)...")
    from app.agents.context_agent import context_agent

    t0 = time.perf_counter()
    context_result = await context_agent(state)
    t1 = time.perf_counter()
    context_time = t1 - t0

    state = state.model_copy(update=context_result)
    stage_times["Context"] = context_time
    print(f"  Time: {context_time:.3f}s (no LLM)")

    # ── Stage 2: Reasoning Agent (LLM) ───────────────────────────────
    print("\n[2/5] Reasoning Agent (LLM)...")
    from app.agents.reasoning_agent import reasoning_agent, HypothesesResponse
    from app.agents.reasoning_agent import _build_prompt as reasoning_build_prompt

    # Build the prompt to measure its size
    reasoning_prompt = reasoning_build_prompt(state)
    reasoning_prompt_chars = len(reasoning_prompt)

    t0 = time.perf_counter()
    reasoning_result = reasoning_agent(state)
    t1 = time.perf_counter()
    reasoning_wall = t1 - t0

    state = state.model_copy(update=reasoning_result)
    stage_times["Reasoning"] = reasoning_wall

    print(f"  Wall-clock time: {reasoning_wall:.2f}s")
    print(f"  Prompt chars: {reasoning_prompt_chars}")

    # Isolated Ollama call to get detailed timing
    print("  Running isolated Ollama timing call for Reasoning prompt...")
    r_timing = ollama_generate_with_timing(
        reasoning_prompt,
        format_schema=HypothesesResponse.model_json_schema(),
    )
    r_detail = print_ollama_timing("Reasoning (isolated)", reasoning_prompt_chars, r_timing)
    results.append(r_detail)

    # ── Stage 3: Compliance Agent (LLM) ──────────────────────────────
    print("\n[3/5] Compliance Agent (LLM)...")
    from app.agents.compliance_agent import compliance_agent
    from app.agents.compliance_agent import _build_prompt as compliance_build_prompt
    from app.schemas.investigation_state import EvidenceComplianceValidation

    compliance_prompt = compliance_build_prompt(state)
    compliance_prompt_chars = len(compliance_prompt)

    t0 = time.perf_counter()
    compliance_result = compliance_agent(state)
    t1 = time.perf_counter()
    compliance_wall = t1 - t0

    state = state.model_copy(update=compliance_result)
    stage_times["Compliance"] = compliance_wall

    print(f"  Wall-clock time: {compliance_wall:.2f}s")
    print(f"  Prompt chars: {compliance_prompt_chars}")

    # Isolated Ollama call
    print("  Running isolated Ollama timing call for Compliance prompt...")
    c_timing = ollama_generate_with_timing(
        compliance_prompt,
        format_schema=EvidenceComplianceValidation.model_json_schema(),
    )
    c_detail = print_ollama_timing("Compliance (isolated)", compliance_prompt_chars, c_timing)
    results.append(c_detail)

    # ── Stage 4: Decision Agent (LLM) ────────────────────────────────
    print("\n[4/5] Decision Agent (LLM)...")
    from app.agents.decision_agent import decision_agent
    from app.agents.decision_agent import _build_prompt as decision_build_prompt, _DecisionOptionsResponse

    decision_prompt = decision_build_prompt(state)
    decision_prompt_chars = len(decision_prompt)

    t0 = time.perf_counter()
    decision_result = decision_agent(state)
    t1 = time.perf_counter()
    decision_wall = t1 - t0

    state = state.model_copy(update=decision_result)
    stage_times["Decision"] = decision_wall

    print(f"  Wall-clock time: {decision_wall:.2f}s")
    print(f"  Prompt chars: {decision_prompt_chars}")

    # Isolated Ollama call
    print("  Running isolated Ollama timing call for Decision prompt...")
    d_timing = ollama_generate_with_timing(
        decision_prompt,
        format_schema=_DecisionOptionsResponse.model_json_schema(),
    )
    d_detail = print_ollama_timing("Decision (isolated)", decision_prompt_chars, d_timing)
    results.append(d_detail)

    # ── Stage 5: Reporting (deterministic) ────────────────────────────
    print("\n[5/5] Reporting (deterministic)...")
    from app.agents.reporting_agent import reporting_agent

    t0 = time.perf_counter()
    reporting_result = reporting_agent(state)
    t1 = time.perf_counter()
    reporting_time = t1 - t0

    stage_times["Reporting"] = reporting_time
    print(f"  Time: {reporting_time:.3f}s (no LLM)")

    # ── Summary Table ────────────────────────────────────────────────
    total_pipeline = sum(stage_times.values())
    total_llm = stage_times["Reasoning"] + stage_times["Compliance"] + stage_times["Decision"]

    print("\n\n" + "=" * 70)
    print("  PIPELINE TIMING SUMMARY (wall-clock, actual agent calls)")
    print("=" * 70)
    print(f"\n  {'Stage':<20} {'Time (s)':>10} {'% of Total':>12}")
    print(f"  {'-'*20} {'-'*10} {'-'*12}")
    for stage, t in stage_times.items():
        pct = 100 * t / total_pipeline if total_pipeline > 0 else 0
        print(f"  {stage:<20} {t:>10.2f} {pct:>11.1f}%")
    print(f"  {'-'*20} {'-'*10} {'-'*12}")
    print(f"  {'TOTAL':<20} {total_pipeline:>10.2f} {'100.0%':>12}")
    print(f"  {'LLM stages only':<20} {total_llm:>10.2f} {100*total_llm/total_pipeline:>11.1f}%")

    # ── Detailed LLM Breakdown ───────────────────────────────────────
    print("\n\n" + "=" * 70)
    print("  ISOLATED OLLAMA CALL DETAIL (repeated call for timing accuracy)")
    print("=" * 70)

    print(f"\n  {'Stage':<15} {'Prompt':>7} {'Output':>7} {'Prefill':>8} {'Gen':>8} {'Total':>8} {'PF t/s':>7} {'Gen t/s':>8}")
    print(f"  {'':.<15} {'Tokens':>7} {'Tokens':>7} {'(s)':>8} {'(s)':>8} {'(s)':>8} {'':>7} {'':>8}")
    print(f"  {'-'*15} {'-'*7} {'-'*7} {'-'*8} {'-'*8} {'-'*8} {'-'*7} {'-'*8}")
    for r in results:
        label = r["label"].split(" (")[0]
        print(f"  {label:<15} {r['prompt_tokens']:>7} {r['gen_tokens']:>7} "
              f"{r['prefill_s']:>8.2f} {r['gen_s']:>8.2f} {r['total_s']:>8.2f} "
              f"{r['prefill_tps']:>7.1f} {r['gen_tps']:>7.1f}")

    total_prefill = sum(r["prefill_s"] for r in results)
    total_gen = sum(r["gen_s"] for r in results)
    total_ollama = sum(r["total_s"] for r in results)

    if total_ollama > 0:
        print(f"\n  Prefill (prompt eval) total:  {total_prefill:.2f}s  ({100*total_prefill/total_ollama:.0f}% of Ollama time)")
        print(f"  Generation (decode) total:    {total_gen:.2f}s  ({100*total_gen/total_ollama:.0f}% of Ollama time)")
    print(f"  Model load overhead total:    {sum(r['load_s'] for r in results):.2f}s")

    # ── Bottleneck Analysis ──────────────────────────────────────────
    print("\n\n" + "=" * 70)
    print("  BOTTLENECK ANALYSIS")
    print("=" * 70)

    sorted_stages = sorted(stage_times.items(), key=lambda x: x[1], reverse=True)
    print(f"\n  Slowest stage:       {sorted_stages[0][0]} ({sorted_stages[0][1]:.2f}s)")
    print(f"  Second slowest:      {sorted_stages[1][0]} ({sorted_stages[1][1]:.2f}s)")

    if total_ollama > 0:
        if total_prefill > total_gen:
            print(f"\n  Latency is primarily PREFILL-DOMINATED ({100*total_prefill/total_ollama:.0f}% prefill vs {100*total_gen/total_ollama:.0f}% generation)")
            print("  -> Reducing input token count will have a significant impact.")
            print("  -> A smaller model with faster prefill would help substantially.")
        elif total_gen > total_prefill:
            print(f"\n  Latency is primarily GENERATION-DOMINATED ({100*total_gen/total_ollama:.0f}% generation vs {100*total_prefill/total_ollama:.0f}% prefill)")
            print("  -> Reducing output token count or using a smaller model for faster decoding would help.")
        else:
            print("\n  Latency is roughly balanced between prefill and generation.")

    # Verdict on smaller model
    print("\n\n" + "=" * 70)
    print("  MODEL SIZE ASSESSMENT")
    print("=" * 70)
    total_prompt_tokens = sum(r["prompt_tokens"] for r in results)
    total_gen_tokens = sum(r["gen_tokens"] for r in results)
    print(f"\n  Total input tokens across 3 LLM calls:  {total_prompt_tokens}")
    print(f"  Total output tokens across 3 LLM calls: {total_gen_tokens}")
    if total_ollama > 0:
        print(f"  Total Ollama time across 3 LLM calls:   {total_ollama:.2f}s")
    print(f"  Deterministic stages time:              {stage_times['Context'] + stage_times['Reporting']:.3f}s")
    if total_pipeline > 0:
        print(f"  LLM % of total pipeline:                {100*total_llm/total_pipeline:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
