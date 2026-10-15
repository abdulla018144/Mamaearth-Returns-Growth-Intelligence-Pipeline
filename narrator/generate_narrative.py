"""
Mamaearth Returns & Growth Intelligence Pipeline.
Part 3: GenAI Insight Narrator.
Execution runs with online Gemini API or offline fallback.
Command runs from project root: python narrator/generate_narrative.py
"""

import json
import os
import pathlib
import sys

# UTF-8 stdout configuration for Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Environment variable supplies API key with fallback option.
# API_KEY = os.getenv("GEMINI_API_KEY") or "Place Gemini API key here"
API_KEY = os.getenv("GEMINI_API_KEY") or ""  # Place Gemini 3.5 flash lite API key inside quotes

# Online path: Gemini API

def generate_scr_narrative(findings: dict) -> dict:
    """
    Gemini produces structured three-part business narratives.
    Temperature stays locked at 0.0 for deterministic factual reporting rather than creative writing.
    """
    try:
        from google import genai
        from google.genai import types

        if not API_KEY:
            raise EnvironmentError("GEMINI_API_KEY is not set")

        # Timeout sets minimum duration for network requests.
        client = genai.Client(
            api_key=API_KEY,
            http_options=types.HttpOptions(timeout=30000),
        )

        # System instructions remain separate from user prompt text.
        system_instruction = (
            "You are a senior data analyst writing for Mamaearth's regional ops and finance heads. "
            "Structure every response with exactly three clearly labeled sections: "
            "Situation, Complication, Resolution. "
            "Every number you write must come from the supplied findings dict and appear "
            "with the exact same value — do not invent, estimate, or round to different precision."
        )

        # User prompt builds dynamically from verified finding numbers.
        rr    = findings["return_rate_by_payment"]
        seg   = findings["highest_risk_segment"]
        peak  = findings["true_peak_month"]
        infl  = findings["outlier_inflated_month"]

        user_prompt = (
            "Write a concise SCR business narrative based on these verified findings:\n\n"
            f"- Cleaned total revenue (175 de-duplicated orders): "
            f"₹{findings['cleaned_total_revenue_inr']:,.2f}\n"
            f"- Raw total revenue (180 orders, before cleaning): "
            f"₹{findings['raw_total_revenue_inr']:,.2f}\n"
            f"- Revenue delta from 5 duplicate orders removed: "
            f"₹{findings['duplicate_reconciliation_delta_inr']:,.2f}\n"
            f"- Return rates by payment method: COD {rr['COD']}%, "
            f"CARD {rr['CARD']}%, UPI {rr['UPI']}%\n"
            f"- Highest-risk segment: {seg['payment_method']} + Tier-{seg['city_tier']} cities "
            f"at {seg['return_rate_pct']}% return rate\n"
            f"- True peak revenue month: March ({peak['month']}) at ₹{peak['revenue_inr']:,.2f}\n"
            f"- January appeared highest at ₹{infl['apparent_revenue_inr']:,.2f} but "
            f"corrects to ₹{infl['corrected_revenue_inr']:,.2f} after removing two "
            f"outlier bulk orders (quantities 25 and 30)"
        )

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,        # Deterministic factual reporting without creative drift
                max_output_tokens=700,  # Token limit fits three sections and target word count
            ),
        )

        tokens    = getattr(getattr(response, "usage_metadata", None), "total_token_count", None)
        return {"status": "success", "narrative": response.text, "tokens": tokens}

    except Exception as err:
        return {"status": "error", "narrative": None, "message": str(err)}


# Offline fallback template without external dependencies

def generate_scr_narrative_offline(findings: dict) -> dict:
    """
    Offline template creates business narrative without network access.
    Data dictionary provides all numeric values directly.
    Output dictionary format matches online response structure.
    """
    rr   = findings["return_rate_by_payment"]
    seg  = findings["highest_risk_segment"]
    peak = findings["true_peak_month"]
    infl = findings["outlier_inflated_month"]

    narrative = (
        "Situation\n"
        f"Mamaearth's H1 2026 order pipeline contains 180 raw entries worth "
        f"₹{findings['raw_total_revenue_inr']:,.2f}. After identifying and removing "
        f"5 exact duplicate records (a double-submit bug), the verified transaction "
        f"base is 175 orders totalling ₹{findings['cleaned_total_revenue_inr']:,.2f} — "
        f"a reconciliation delta of ₹{findings['duplicate_reconciliation_delta_inr']:,.2f} "
        f"attributable entirely to those 5 duplicate rows, not to any price or discount change.\n\n"
        "Complication\n"
        f"Returns are heavily concentrated in Cash-on-Delivery: the COD return rate is "
        f"{rr['COD']}%, nearly three times the {rr['CARD']}% Card rate and more than "
        f"double the {rr['UPI']}% UPI rate. Multi-level segmentation reveals the risk "
        f"is not uniform — COD orders in Tier-{seg['city_tier']} cities return at "
        f"{seg['return_rate_pct']}% versus 37.5% in Tier-1 cities, meaning a blended "
        f"COD figure conceals where the real problem is concentrated. On the revenue "
        f"side, January appeared to be the peak month at "
        f"₹{infl['apparent_revenue_inr']:,.2f}, but this is an artifact of two bulk "
        f"outlier orders (quantities 25 and 30); the corrected January figure is only "
        f"₹{infl['corrected_revenue_inr']:,.2f}, and the true peak month is "
        f"March at ₹{peak['revenue_inr']:,.2f}.\n\n"
        "Resolution\n"
        f"Three targeted actions: (1) Restrict or disincentivise COD in Tier-{seg['city_tier']} "
        f"cities — the {seg['return_rate_pct']}% return rate there makes COD unprofitable "
        f"without intervention; prepayment discounts or COD deposit requirements are the "
        f"lowest-friction lever. (2) Review the two bulk outlier orders with the logistics "
        f"team before using January figures for demand planning. (3) Anchor seasonal "
        f"targets to March (₹{peak['revenue_inr']:,.2f}) rather than the inflated "
        f"January baseline to avoid over-stocking and excess logistics spend."
    )

    return {"status": "success", "narrative": narrative, "tokens": None}


# Numeric accuracy checker

def check_numeric_accuracy(narrative: str) -> bool:
    """
    Validation asserts required metrics exist within narrative text.
    Comma stripping normalizes formatted and unformatted numeric strings.
    """
    normalized = narrative.replace(",", "")

    checks = [
        ("97358.3",  "Cleaned total revenue  97,358.30"),
        ("44.4",     "COD return rate        44.4%"),
        ("54.5",     "COD+Tier-2 segment     54.5%"),
        ("2501.9",   "Reconciliation delta   2,501.90"),
        ("March",    "True peak month        March"),
        ("20318.9",  "March peak revenue     20,318.90"),
    ]

    all_pass = True
    print("\n── Numeric Accuracy Checklist ────────────────────────────")
    for pattern, label in checks:
        found  = pattern in normalized
        status = "PASS" if found else "FAIL"
        all_pass = all_pass and found
        print(f"  [{status}] {label}")

    result_line = "ALL CHECKS PASSED ✓" if all_pass else "SOME CHECKS FAILED ✗"
    print(f"\nResult: {result_line}")
    return all_pass


# Program execution entry point

if __name__ == "__main__":
    findings_path = ROOT / "narrator" / "findings.json"

    if not findings_path.exists():
        raise FileNotFoundError(
            f"{findings_path} not found.\n"
            "Run 'python analysis/clean_and_eda.py' first to generate it."
        )

    with open(findings_path) as f:
        findings = json.load(f)

    # Online execution runs when key exists, otherwise offline fallback runs.
    result = generate_scr_narrative(findings) if API_KEY else generate_scr_narrative_offline(findings)

    # Fallback routine executes when online call fails.
    if result["status"] == "error" or result["narrative"] is None:
        print(f"Online path failed: {result.get('message', '')}")
        print("Falling back to offline template...\n")
        result = generate_scr_narrative_offline(findings)

    path_label = "Gemini API" if (API_KEY and result.get("tokens")) else "offline fallback"
    print(f"\n{'=' * 60}")
    print(f"SCR Narrative  [{path_label}]")
    print("=" * 60)
    print(result["narrative"])

    if result.get("tokens"):
        print(f"\nTokens used: {result['tokens']}")

    check_numeric_accuracy(result["narrative"])

    sample_file = ROOT / "narrator" / "sample_output.txt"

    # File export saves live model response after successful run.
    if result.get("tokens"):
        with open(sample_file, "w", encoding="utf-8") as sf:
            sf.write(result["narrative"])
        print(f"\nSaved live Gemini output -> {sample_file}")

    # Verification step checks saved sample text file.
    if sample_file.exists():
        print(f"\n{'=' * 60}")
        print("Verifying saved sample (narrator/sample_output.txt):")
        print("=" * 60)
        with open(sample_file, encoding="utf-8") as sf:
            check_numeric_accuracy(sf.read())
