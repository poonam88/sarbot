"""
agent.py - SARBot investigation agent
OpenAI gpt-4o function-calling agentic loop
"""

import time
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from tools import (
    get_customer_kyc,
    get_transaction_history,
    search_typology_database,
    draft_sar_narrative,
    calculate_risk_score,
)

# ---------------------------------------------------------------------------
# OpenAI client
# ---------------------------------------------------------------------------
load_dotenv(Path(__file__).parent / ".env")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
MODEL = "gpt-4o"

# ---------------------------------------------------------------------------
# Tool definitions in OpenAI function-calling format
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_customer_kyc",
            "description": (
                "Retrieve KYC profile for a customer: name, nationality, PEP status, "
                "occupation, account opening date, risk tier, and any adverse media flags."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The unique customer identifier, e.g. CUST-MERIDIAN-001",
                    }
                },
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_transaction_history",
            "description": (
                "Retrieve recent transaction history for a customer. Returns a list of "
                "transactions with date, amount, currency, counterparty, and jurisdiction."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The unique customer identifier",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of history to retrieve (default 90)",
                    },
                },
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_typology_database",
            "description": (
                "Search the FATF/FCA typology database for money laundering patterns. "
                "Returns matching typologies with red-flag indicators."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Search keywords such as 'structuring', 'TBML', 'cash', 'layering'",
                    }
                },
                "required": ["keywords"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_sar_narrative",
            "description": (
                "Draft a Suspicious Activity Report (SAR) narrative based on KYC data, "
                "transaction history, and matched typologies. Returns a regulatory-grade narrative."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "case_summary": {
                        "type": "object",
                        "description": "Case summary with customer_info, transactions, and typologies",
                        "properties": {
                            "customer_info": {"type": "object"},
                            "transactions": {"type": "array", "items": {"type": "object"}},
                            "typologies": {"type": "array", "items": {"type": "object"}},
                        },
                        "required": ["customer_info", "transactions", "typologies"],
                    }
                },
                "required": ["case_summary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_risk_score",
            "description": (
                "Calculate an AML risk score (0-100) based on KYC risk tier, transaction "
                "velocity, jurisdiction count, PEP status, and prior alerts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "factors": {
                        "type": "object",
                        "description": "Risk scoring factors",
                        "properties": {
                            "velocity": {"type": "string", "enum": ["low", "medium", "high"]},
                            "structuring": {"type": "boolean"},
                            "jurisdiction_count": {"type": "integer"},
                            "kyc_tier": {"type": "string"},
                            "prior_alerts": {"type": "integer"},
                        },
                        "required": ["velocity", "structuring", "jurisdiction_count", "kyc_tier", "prior_alerts"],
                    }
                },
                "required": ["factors"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------
TOOL_DISPATCH = {
    "get_customer_kyc": get_customer_kyc,
    "get_transaction_history": get_transaction_history,
    "search_typology_database": search_typology_database,
    "draft_sar_narrative": draft_sar_narrative,
    "calculate_risk_score": calculate_risk_score,
}

SYSTEM_PROMPT = """You are SARBot, an expert AML/financial crime investigation agent working for a regulated UK financial institution.

Your job is to investigate a suspicious activity alert by calling tools in this order:
1. get_customer_kyc - retrieve the customer profile
2. get_transaction_history - review recent transactions
3. search_typology_database - pass keywords derived from the alert type
4. draft_sar_narrative - pass a case_summary with customer_info, transactions, typologies
5. calculate_risk_score - pass factors with velocity, structuring, jurisdiction_count, kyc_tier, prior_alerts

After all tools have been called, return ONLY a valid JSON object (no markdown, no preamble):
{
  "sar_narrative": "<full SAR narrative text>",
  "risk_score": <integer 0-100>,
  "recommendation": "<SUBMIT SAR | ESCALATE | MONITOR | DISMISS>",
  "red_flags": ["<flag1>", "<flag2>"],
  "summary": "<2-3 sentence executive summary>"
}"""


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _log_tool(log: list, name: str, input_: dict, fn, **kwargs) -> dict:
    start = time.time()
    try:
        output = fn(**kwargs)
    except Exception as e:
        output = {"error": str(e)}
    log.append({
        "name": name,
        "input": input_,
        "output": output,
        "duration": round(time.time() - start, 3),
    })
    return output


# ---------------------------------------------------------------------------
# Main agentic loop
# ---------------------------------------------------------------------------
def run_investigation(case_id: str, customer_id: str, alert_type: str) -> dict:
    start_time = time.time()
    tool_call_log: list = []
    api_key = os.environ.get("OPENAI_API_KEY")

    # -----------------------------------------------------------------------
    # Real OpenAI gpt-4o agentic loop
    # -----------------------------------------------------------------------
    if api_key:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Investigate the following alert:\n\n"
                    f"Case ID: {case_id}\n"
                    f"Customer ID: {customer_id}\n"
                    f"Alert type: {alert_type}\n\n"
                    f"Use all available tools to complete the investigation, "
                    f"then return your final JSON result."
                ),
            },
        ]

        while True:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            message = response.choices[0].message
            messages.append(message)

            if not message.tool_calls:
                break

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)
                tool_fn = TOOL_DISPATCH.get(tool_name)

                t_start = time.time()
                try:
                    output = tool_fn(**tool_input) if tool_fn else {"error": f"Unknown tool: {tool_name}"}
                except Exception as e:
                    output = {"error": str(e)}

                tool_call_log.append({
                    "name": tool_name,
                    "input": tool_input,
                    "output": output,
                    "duration": round(time.time() - t_start, 3),
                })

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(output),
                })

        final_text = message.content or ""
        try:
            clean = final_text.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            result = json.loads(clean.strip())
        except Exception:
            result = {
                "sar_narrative": final_text or "Agent did not produce a narrative.",
                "risk_score": 0,
                "recommendation": "ESCALATE",
                "red_flags": ["Agent response parsing failed"],
                "summary": "Investigation completed but result parsing failed.",
            }

        result["tool_call_log"] = tool_call_log
        result["total_time_seconds"] = round(time.time() - start_time, 2)
        return result

    # -----------------------------------------------------------------------
    # Demo mode fallback (no API key)
    # -----------------------------------------------------------------------
    kyc = _log_tool(tool_call_log, "get_customer_kyc", {"customer_id": customer_id},
                    get_customer_kyc, customer_id=customer_id)

    txns = _log_tool(tool_call_log, "get_transaction_history", {"customer_id": customer_id, "days": 90},
                     get_transaction_history, customer_id=customer_id, days=90)

    keywords = [w for w in alert_type.replace("_", " ").split() if len(w) > 3]
    typologies = _log_tool(tool_call_log, "search_typology_database", {"keywords": keywords},
                           search_typology_database, keywords=keywords)

    sar_result = _log_tool(
        tool_call_log, "draft_sar_narrative",
        {"case_summary": {"customer_info": kyc, "transactions": txns, "typologies": typologies}},
        draft_sar_narrative,
        case_summary={"customer_info": kyc, "transactions": txns, "typologies": typologies},
    )

    has_structuring = any(t.get("flag_type") in ("structuring", "cash_deposit") for t in txns)
    jurisdictions = list({t.get("jurisdiction", "GB") for t in txns})
    score_result = _log_tool(
        tool_call_log, "calculate_risk_score",
        {"factors": {"velocity": "high", "structuring": has_structuring,
                     "jurisdiction_count": len(jurisdictions),
                     "kyc_tier": kyc.get("kyc_tier", "standard_due_diligence"),
                     "prior_alerts": kyc.get("prior_alerts", 0)}},
        calculate_risk_score,
        factors={"velocity": "high", "structuring": has_structuring,
                 "jurisdiction_count": len(jurisdictions),
                 "kyc_tier": kyc.get("kyc_tier", "standard_due_diligence"),
                 "prior_alerts": kyc.get("prior_alerts", 0)},
    )

    risk_score = score_result.get("score", 50)
    rec_map = {"MLRO": "SUBMIT SAR", "Financial Crime Investigations": "ESCALATE"}
    recommendation = rec_map.get(score_result.get("escalation_target", ""), "MONITOR")

    red_flags = []
    for t in txns:
        if t.get("flag_type") == "structuring":
            red_flags.append(f"Structuring: £{t['amount_gbp']:,.0f} to {t['counterparty']} ({t['jurisdiction']})")
        elif not t.get("invoice_on_file"):
            red_flags.append(f"Missing invoice: £{t['amount_gbp']:,.0f} — {t['counterparty']}")
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
        "summary": (
            f"{kyc.get('name', customer_id)} — risk score {risk_score}/100. "
            f"{len(txns)} transactions reviewed across {len(jurisdictions)} jurisdiction(s). "
            f"Recommendation: {recommendation}."
        ),
        "tool_call_log": tool_call_log,
        "total_time_seconds": round(time.time() - start_time, 2),
    }
