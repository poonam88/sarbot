"""
api/index.py — SARBot consolidated for Vercel serverless deployment.

Vercel's Python runtime expects a single ASGI/WSGI app per function file.
This file merges main.py + agent.py + tools.py + models.py into one module
so it can be deployed as api/index.py with zero relative-import issues.
"""

import os
import time
import json
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class InvestigationRequest(BaseModel):
    case_id: str = Field(..., examples=["CASE-1001"])
    customer_id: str = Field(..., examples=["CUST-7781"])
    alert_type: str = Field(..., examples=["rapid_movement_of_funds"])


class InvestigationResult(BaseModel):
    sar_narrative: str
    risk_score: int = Field(..., ge=0, le=100)
    recommendation: str
    red_flags: list[str] = Field(default_factory=list)
    tool_call_log: list[dict[str, Any]] = Field(default_factory=list)
    total_time_seconds: float


class CaseRecord(BaseModel):
    request: InvestigationRequest
    result: InvestigationResult


# ---------------------------------------------------------------------------
# Mock data (tools.py contents)
# ---------------------------------------------------------------------------
MOCK_CUSTOMERS: dict[str, dict[str, Any]] = {
    "CUST-7781": {
        "name": "Aarav Mehta", "kyc_tier": "enhanced_due_diligence", "risk_rating": "medium-high",
        "pep_flag": False, "sanctions_flag": False, "last_review_date": "2026-03-14",
        "declared_turnover": 950000, "prior_alerts": 2,
    },
    "CUST-3390": {
        "name": "Priya Shah", "kyc_tier": "standard_due_diligence", "risk_rating": "high",
        "pep_flag": False, "sanctions_flag": False, "last_review_date": "2026-01-29",
        "declared_turnover": 185000, "prior_alerts": 4,
    },
    "CUST-MERIDIAN-001": {
        "name": "Meridian Trading Ltd", "kyc_tier": "enhanced_due_diligence", "risk_rating": "high",
        "pep_flag": False, "sanctions_flag": False, "last_review_date": "2024-09-18",
        "declared_turnover": 1200000, "prior_alerts": 3,
    },
    "CUST-OSEI-039": {
        "name": "K. Osei-Mensah", "kyc_tier": "standard_due_diligence", "risk_rating": "medium-high",
        "pep_flag": False, "sanctions_flag": False, "last_review_date": "2024-10-02",
        "declared_turnover": 92000, "prior_alerts": 2,
    },
    "CUST-BLUEWAVE-035": {
        "name": "BlueWave Capital LP", "kyc_tier": "enhanced_due_diligence", "risk_rating": "low",
        "pep_flag": False, "sanctions_flag": False, "last_review_date": "2024-11-21",
        "declared_turnover": 8500000, "prior_alerts": 0,
    },
}

MOCK_TRANSACTIONS: dict[str, list[dict[str, Any]]] = {
    "CUST-7781": [
        {"tx_id": "TX-GB-9001", "date": "2026-06-20", "amount_gbp": 9850.0, "counterparty": "Northbridge Imports Ltd", "jurisdiction": "GB", "flag_type": "large_inbound", "invoice_on_file": True},
        {"tx_id": "TX-GB-9002", "date": "2026-06-21", "amount_gbp": 9630.0, "counterparty": "Blue Harbor Trading FZE", "jurisdiction": "AE", "flag_type": "rapid_movement_of_funds", "invoice_on_file": False},
        {"tx_id": "TX-GB-9003", "date": "2026-06-24", "amount_gbp": 7200.0, "counterparty": "Dover Freight Services", "jurisdiction": "GB", "flag_type": "trade_payment", "invoice_on_file": True},
    ],
    "CUST-3390": [
        {"tx_id": "TX-GB-9101", "date": "2026-06-18", "amount_gbp": 7900.0, "counterparty": "Branch Cash Deposit", "jurisdiction": "GB", "flag_type": "cash_deposit", "invoice_on_file": False},
        {"tx_id": "TX-GB-9102", "date": "2026-06-19", "amount_gbp": 7850.0, "counterparty": "Branch Cash Deposit", "jurisdiction": "GB", "flag_type": "structuring", "invoice_on_file": False},
        {"tx_id": "TX-GB-9103", "date": "2026-06-21", "amount_gbp": 8100.0, "counterparty": "Branch Cash Deposit", "jurisdiction": "GB", "flag_type": "structuring", "invoice_on_file": False},
    ],
    "CUST-MERIDIAN-001": [
        {"tx_id": "TX-MER-8841-01", "date": "2024-12-03", "amount_gbp": 9850.0, "counterparty": "Al Noor General Trading FZE", "jurisdiction": "UAE", "flag_type": "structuring", "invoice_on_file": False},
        {"tx_id": "TX-MER-8841-02", "date": "2024-12-04", "amount_gbp": 9975.0, "counterparty": "Rotterdam Commodities BV", "jurisdiction": "NL", "flag_type": "trade_payment", "invoice_on_file": True},
        {"tx_id": "TX-MER-8841-03", "date": "2024-12-05", "amount_gbp": 9615.0, "counterparty": "Kyrenia Holdings Ltd", "jurisdiction": "Cyprus", "flag_type": "structuring", "invoice_on_file": False},
        {"tx_id": "TX-MER-8841-04", "date": "2024-12-06", "amount_gbp": 18400.0, "counterparty": "Al Noor General Trading FZE", "jurisdiction": "UAE", "flag_type": "rapid_movement_of_funds", "invoice_on_file": False},
    ],
    "CUST-OSEI-039": [
        {"tx_id": "TX-OSE-8839-01", "date": "2024-12-02", "amount_gbp": 4900.0, "counterparty": "Branch Cash Deposit", "jurisdiction": "UK", "flag_type": "cash_deposit", "invoice_on_file": False},
        {"tx_id": "TX-OSE-8839-02", "date": "2024-12-04", "amount_gbp": 4750.0, "counterparty": "Branch Cash Deposit", "jurisdiction": "UK", "flag_type": "structuring", "invoice_on_file": False},
        {"tx_id": "TX-OSE-8839-03", "date": "2024-12-06", "amount_gbp": 4825.0, "counterparty": "Branch Cash Deposit", "jurisdiction": "UK", "flag_type": "structuring", "invoice_on_file": False},
    ],
    "CUST-BLUEWAVE-035": [
        {"tx_id": "TX-BLU-8835-01", "date": "2024-12-01", "amount_gbp": 62500.0, "counterparty": "Harbor Street Securities LLC", "jurisdiction": "US", "flag_type": "wire_transfer", "invoice_on_file": True},
        {"tx_id": "TX-BLU-8835-02", "date": "2024-12-08", "amount_gbp": 62500.0, "counterparty": "Harbor Street Securities LLC", "jurisdiction": "US", "flag_type": "wire_transfer", "invoice_on_file": True},
    ],
}

TYPOLOGIES = [
    {
        "typology_name": "FATF Typology 12 (TBML)", "source": "Financial Action Task Force",
        "description": "Trade-based money laundering involving mispriced goods, false invoicing, or trade payments with limited commercial rationale.",
        "red_flags": ["Payments inconsistent with declared business activity", "Missing or weak invoice documentation", "Use of overseas trading counterparties without a clear relationship"],
    },
    {
        "typology_name": "FCA \u00a72.4 structuring", "source": "Financial Conduct Authority",
        "description": "Repeated transactions arranged to avoid scrutiny, internal thresholds, or expected monitoring triggers.",
        "red_flags": ["Multiple similar-value transactions over a short period", "Amounts clustered below review thresholds", "Activity inconsistent with expected customer profile"],
    },
    {
        "typology_name": "FATF Typology 26 (bulk cash)", "source": "Financial Action Task Force",
        "description": "Bulk cash smuggling or repeated cash deposits used to introduce illicit funds into the financial system.",
        "red_flags": ["Frequent cash deposits below reporting thresholds", "No clear source of cash income", "Rapid withdrawal or transfer after deposit"],
    },
]


def get_customer_kyc(customer_id: str) -> dict[str, Any]:
    return MOCK_CUSTOMERS.get(customer_id, {
        "name": "Unknown Customer", "kyc_tier": "standard_due_diligence", "risk_rating": "unknown",
        "pep_flag": False, "sanctions_flag": False, "last_review_date": "unknown",
        "declared_turnover": 0, "prior_alerts": 0,
    })


def get_transaction_history(customer_id: str, days: int = 90) -> list[dict[str, Any]]:
    return MOCK_TRANSACTIONS.get(customer_id, [])


def search_typology_database(keywords: list[str]) -> list[dict[str, Any]]:
    normalized_keywords = [k.lower() for k in keywords]
    if not normalized_keywords:
        return TYPOLOGIES
    matches = []
    for typology in TYPOLOGIES:
        searchable = " ".join([typology["typology_name"], typology["source"], typology["description"], " ".join(typology["red_flags"])]).lower()
        if any(k in searchable for k in normalized_keywords):
            matches.append(typology)
    return matches or TYPOLOGIES


def draft_sar_narrative(case_summary: dict[str, Any]) -> dict[str, Any]:
    customer = case_summary.get("customer_info", {})
    transactions = case_summary.get("transactions", [])
    typologies = case_summary.get("typologies", [])
    name = customer.get("name", "the subject")
    risk = customer.get("risk_rating", "unknown")
    tx_count = len(transactions)
    total_amount = sum(t.get("amount_gbp", 0) for t in transactions)
    typology_names = ", ".join(t.get("typology_name", "") for t in typologies if t.get("typology_name"))

    narrative_text = (
        f"This SAR relates to {name}, a customer rated {risk} risk. "
        f"A total of {tx_count} transactions amounting to \u00a3{total_amount:,.2f} were reviewed. "
        f"The activity displays characteristics consistent with the following typologies: {typology_names or 'unspecified patterns'}. "
        "Transactions lack supporting documentation and involve multiple high-risk jurisdictions, "
        "which is inconsistent with the customer's declared business profile. "
        "The financial crime team recommends escalation to the MLRO for SAR filing consideration "
        "under Part 7 of the Proceeds of Crime Act 2002."
    )
    return {"narrative_text": narrative_text, "regulatory_basis": "UK Proceeds of Crime Act 2002; FCA financial crime systems and controls expectations", "word_count": len(narrative_text.split())}


def calculate_risk_score(factors: dict[str, Any]) -> dict[str, Any]:
    score = 20
    velocity = str(factors.get("velocity", "medium")).lower()
    structuring = bool(factors.get("structuring", False))
    jurisdiction_count = int(factors.get("jurisdiction_count", 1) or 1)
    kyc_tier = str(factors.get("kyc_tier", "standard_due_diligence")).lower()
    prior_alerts = int(factors.get("prior_alerts", 0) or 0)

    if velocity == "high":
        score += 25
    elif velocity == "medium":
        score += 12
    if structuring:
        score += 25
    score += min(jurisdiction_count * 5, 15)
    if "enhanced" in kyc_tier:
        score += 10
    elif "simplified" in kyc_tier:
        score -= 5
    score += min(prior_alerts * 6, 18)
    score = max(0, min(score, 100))

    if score >= 75:
        recommendation, escalation_target, confidence = "Escalate for MLRO review and consider SAR submission.", "MLRO", "high"
    elif score >= 50:
        recommendation, escalation_target, confidence = "Escalate to financial crime investigations for enhanced review.", "Financial Crime Investigations", "medium"
    else:
        recommendation, escalation_target, confidence = "Document rationale and continue routine monitoring.", "Level 1 AML Operations", "medium"

    return {"score": score, "recommendation": recommendation, "confidence": confidence, "escalation_target": escalation_target, "estimated_hours_saved": 2.5}


TOOL_DISPATCH = {
    "get_customer_kyc": get_customer_kyc,
    "get_transaction_history": get_transaction_history,
    "search_typology_database": search_typology_database,
    "draft_sar_narrative": draft_sar_narrative,
    "calculate_risk_score": calculate_risk_score,
}

TOOLS = [
    {"name": "get_customer_kyc", "description": "Retrieve KYC profile for a customer.", "input_schema": {"type": "object", "properties": {"customer_id": {"type": "string"}}, "required": ["customer_id"]}},
    {"name": "get_transaction_history", "description": "Retrieve transaction history for a customer.", "input_schema": {"type": "object", "properties": {"customer_id": {"type": "string"}, "days": {"type": "integer", "default": 90}}, "required": ["customer_id"]}},
    {"name": "search_typology_database", "description": "Search FATF/FCA typology database by keyword.", "input_schema": {"type": "object", "properties": {"keywords": {"type": "array", "items": {"type": "string"}}}, "required": ["keywords"]}},
    {"name": "draft_sar_narrative", "description": "Draft a SAR narrative from case summary.", "input_schema": {"type": "object", "properties": {"case_summary": {"type": "object", "properties": {"customer_info": {"type": "object"}, "transactions": {"type": "array", "items": {"type": "object"}}, "typologies": {"type": "array", "items": {"type": "object"}}}, "required": ["customer_info", "transactions", "typologies"]}}, "required": ["case_summary"]}},
    {"name": "calculate_risk_score", "description": "Calculate AML risk score from factors.", "input_schema": {"type": "object", "properties": {"factors": {"type": "object", "properties": {"velocity": {"type": "string", "enum": ["low", "medium", "high"]}, "structuring": {"type": "boolean"}, "jurisdiction_count": {"type": "integer"}, "kyc_tier": {"type": "string"}, "prior_alerts": {"type": "integer"}}, "required": ["velocity", "structuring", "jurisdiction_count", "kyc_tier", "prior_alerts"]}}, "required": ["factors"]}},
]

SYSTEM_PROMPT = """You are SARBot, an expert AML/financial crime investigation agent working for a regulated UK financial institution.

Call tools in this order:
1. get_customer_kyc
2. get_transaction_history
3. search_typology_database (keywords derived from alert_type)
4. draft_sar_narrative (case_summary: customer_info, transactions, typologies)
5. calculate_risk_score (factors: velocity, structuring, jurisdiction_count, kyc_tier, prior_alerts)

Then return ONLY valid JSON (no markdown):
{
  "sar_narrative": "<text>",
  "risk_score": <0-100>,
  "recommendation": "<SUBMIT SAR | ESCALATE | MONITOR | DISMISS>",
  "red_flags": ["<flag1>"],
  "summary": "<2-3 sentence summary>"
}"""


def run_investigation(case_id: str, customer_id: str, alert_type: str) -> dict:
    start_time = time.time()
    tool_call_log: list = []
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if api_key:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        messages = [{"role": "user", "content": (
            f"Investigate the following alert:\n\nCase ID: {case_id}\nCustomer ID: {customer_id}\n"
            f"Alert type: {alert_type}\n\nUse all available tools, then return your final JSON result."
        )}]
        response = None
        for _ in range(8):  # safety cap on loop iterations for serverless time limits
            response = client.messages.create(model="claude-sonnet-4-6", max_tokens=4096, system=SYSTEM_PROMPT, tools=TOOLS, messages=messages)
            messages.append({"role": "assistant", "content": response.content})
            if response.stop_reason != "tool_use":
                break
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                fn = TOOL_DISPATCH.get(block.name)
                t0 = time.time()
                try:
                    output = fn(**block.input) if fn else {"error": f"Unknown tool: {block.name}"}
                except Exception as e:
                    output = {"error": str(e)}
                tool_call_log.append({"name": block.name, "input": block.input, "output": output, "duration": round(time.time() - t0, 3)})
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(output)})
            messages.append({"role": "user", "content": tool_results})

        final_text = "".join(getattr(b, "text", "") for b in (response.content if response else []))
        try:
            clean = final_text.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            result = json.loads(clean.strip())
        except Exception:
            result = {"sar_narrative": final_text or "Agent did not produce a narrative.", "risk_score": 0, "recommendation": "ESCALATE", "red_flags": ["Agent response parsing failed"], "summary": "Parsing failed."}
        result["tool_call_log"] = tool_call_log
        result["total_time_seconds"] = round(time.time() - start_time, 2)
        return result

    # Demo-mode fallback (no API key) — deterministic, no LLM reasoning
    def log_tool(name, input_, fn, **kwargs):
        t0 = time.time()
        try:
            output = fn(**kwargs)
        except Exception as e:
            output = {"error": str(e)}
        tool_call_log.append({"name": name, "input": input_, "output": output, "duration": round(time.time() - t0, 3)})
        return output

    kyc = log_tool("get_customer_kyc", {"customer_id": customer_id}, get_customer_kyc, customer_id=customer_id)
    txns = log_tool("get_transaction_history", {"customer_id": customer_id, "days": 90}, get_transaction_history, customer_id=customer_id, days=90)
    keywords = [w for w in alert_type.replace("_", " ").split() if len(w) > 3]
    typologies = log_tool("search_typology_database", {"keywords": keywords}, search_typology_database, keywords=keywords)
    sar_result = log_tool("draft_sar_narrative", {"case_summary": {"customer_info": kyc, "transactions": txns, "typologies": typologies}}, draft_sar_narrative, case_summary={"customer_info": kyc, "transactions": txns, "typologies": typologies})

    has_structuring = any(t.get("flag_type") in ("structuring", "cash_deposit") for t in txns)
    jurisdictions = list({t.get("jurisdiction", "GB") for t in txns})
    factors = {"velocity": "high", "structuring": has_structuring, "jurisdiction_count": len(jurisdictions), "kyc_tier": kyc.get("kyc_tier", "standard_due_diligence"), "prior_alerts": kyc.get("prior_alerts", 0)}
    score_result = log_tool("calculate_risk_score", {"factors": factors}, calculate_risk_score, factors=factors)

    risk_score = score_result.get("score", 50)
    rec_map = {"MLRO": "SUBMIT SAR", "Financial Crime Investigations": "ESCALATE"}
    recommendation = rec_map.get(score_result.get("escalation_target", ""), "MONITOR")

    red_flags = []
    for t in txns:
        if t.get("flag_type") == "structuring":
            red_flags.append(f"Structuring: \u00a3{t['amount_gbp']:,.0f} to {t['counterparty']} ({t['jurisdiction']})")
        elif not t.get("invoice_on_file"):
            red_flags.append(f"Missing invoice: \u00a3{t['amount_gbp']:,.0f} \u2014 {t['counterparty']}")
    if kyc.get("pep_flag"):
        red_flags.append("Customer is a Politically Exposed Person (PEP)")
    if len(jurisdictions) > 2:
        red_flags.append(f"Transactions span {len(jurisdictions)} jurisdictions: {', '.join(jurisdictions)}")
    red_flags = red_flags or ["Unusual transaction pattern detected"]

    return {
        "sar_narrative": sar_result.get("narrative_text", ""),
        "risk_score": risk_score,
        "recommendation": recommendation,
        "red_flags": red_flags,
        "summary": f"{kyc.get('name', customer_id)} \u2014 risk score {risk_score}/100. {len(txns)} transactions reviewed across {len(jurisdictions)} jurisdiction(s). Recommendation: {recommendation}.",
        "tool_call_log": tool_call_log,
        "total_time_seconds": round(time.time() - start_time, 2),
    }


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="SARBot", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

CASE_RESULTS: dict[str, CaseRecord] = {}

SAMPLE_CASES = [
    {"case_id": "CASE-2024-8841", "customer_id": "CUST-MERIDIAN-001", "customer_name": "Meridian Trading Ltd", "alert_type": "structuring_pattern", "summary": "High-risk structuring across UAE/NL/Cyprus", "risk_score": 86, "recommendation": "SUBMIT SAR", "red_flags": ["Structuring", "Multiple high-risk jurisdictions"]},
    {"case_id": "CASE-2024-8839", "customer_id": "CUST-OSEI-039", "customer_name": "K. Osei-Mensah", "alert_type": "structuring_pattern", "summary": "Cash deposits below threshold", "risk_score": 64, "recommendation": "ESCALATE", "red_flags": ["Structuring", "Cash deposits"]},
    {"case_id": "CASE-2024-8835", "customer_id": "CUST-BLUEWAVE-035", "customer_name": "BlueWave Capital LP", "alert_type": "wire_transfer", "summary": "Lower-risk wire transfer case", "risk_score": 28, "recommendation": "MONITOR", "red_flags": ["Repeat wire amounts"]},
]


@app.get("/api")
@app.get("/api/")
def root() -> dict[str, Any]:
    return {"service": "SARBot API", "status": "ok", "docs": "/api/docs"}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/investigate", response_model=InvestigationResult)
def investigate(request: InvestigationRequest) -> InvestigationResult:
    result = run_investigation(request.case_id, request.customer_id, request.alert_type)
    record = CaseRecord(request=request, result=InvestigationResult(**result))
    CASE_RESULTS[request.case_id] = record
    return record.result


@app.post("/api/cases/seed")
def seed_cases() -> dict[str, Any]:
    CASE_RESULTS.clear()
    for sample in SAMPLE_CASES:
        request = InvestigationRequest(case_id=sample["case_id"], customer_id=sample["customer_id"], alert_type=sample["alert_type"])
        result = InvestigationResult(
            sar_narrative=f"Seeded demo case for {sample['customer_name']}: {sample['summary']}",
            risk_score=sample["risk_score"], recommendation=sample["recommendation"],
            red_flags=sample["red_flags"], tool_call_log=[], total_time_seconds=0.0,
        )
        CASE_RESULTS[request.case_id] = CaseRecord(request=request, result=result)
    return {"seeded": len(CASE_RESULTS), "case_ids": list(CASE_RESULTS.keys())}


@app.get("/api/case/{case_id}", response_model=CaseRecord)
def get_case(case_id: str) -> CaseRecord:
    record = CASE_RESULTS.get(case_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Case result not found.")
    return record
