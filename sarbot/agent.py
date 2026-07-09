"""
agent.py — SARBot investigation agent
Migrated from OpenAI Responses API → Anthropic Claude tool-use API
"""

import time
import json
import anthropic
from tools import (
    get_customer_kyc,
    get_transaction_history,
    search_typology_database,
    draft_sar_narrative,
    calculate_risk_score,
)

# ---------------------------------------------------------------------------
# Anthropic client (reads ANTHROPIC_API_KEY from environment automatically)
# ---------------------------------------------------------------------------
client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"

# ---------------------------------------------------------------------------
# Tool definitions in Anthropic's format
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "get_customer_kyc",
        "description": (
            "Retrieve KYC profile for a customer: name, nationality, PEP status, "
            "occupation, account opening date, risk tier, and any adverse media flags."
        ),
        "input_schema": {
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
    {
        "name": "get_transaction_history",
        "description": (
            "Retrieve recent transaction history for a customer. Returns a list of "
            "transactions with date, amount, currency, counterparty, and jurisdiction."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The unique customer identifier",
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days of history to retrieve (default 90)",
                    "default": 90,
                },
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "search_typology_database",
        "description": (
            "Search the FATF/FCA typology database for money laundering patterns "
            "matching a given alert type. Returns matching typologies with red-flag indicators."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "alert_type": {
                    "type": "string",
                    "description": "Alert type such as structuring_pattern, layering, smurfing, trade_based_ml",
                }
            },
            "required": ["alert_type"],
        },
    },
    {
        "name": "draft_sar_narrative",
        "description": (
            "Draft a Suspicious Activity Report (SAR) narrative based on KYC data, "
            "transaction history, and matched typologies. Returns a regulatory-grade narrative."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "kyc_summary": {"type": "string", "description": "Summary of KYC findings"},
                "transaction_summary": {"type": "string", "description": "Summary of suspicious transactions"},
                "typology_match": {"type": "string", "description": "Matched FATF/FCA typology description"},
            },
            "required": ["customer_id", "kyc_summary", "transaction_summary", "typology_match"],
        },
    },
    {
        "name": "calculate_risk_score",
        "description": (
            "Calculate an AML risk score (0–100) based on KYC risk tier, transaction "
            "volume/frequency, jurisdiction risk, PEP status, and typology severity."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "pep_status": {"type": "boolean"},
                "high_risk_jurisdictions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of high-risk jurisdictions involved in transactions",
                },
                "total_suspicious_amount": {
                    "type": "number",
                    "description": "Total value of suspicious transactions in GBP",
                },
                "typology_severity": {
                    "type": "string",
                    "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                },
            },
            "required": ["customer_id", "typology_severity"],
        },
    },
]

# ---------------------------------------------------------------------------
# Tool dispatcher — maps tool name → Python function
# ---------------------------------------------------------------------------
TOOL_DISPATCH = {
    "get_customer_kyc": get_customer_kyc,
    "get_transaction_history": get_transaction_history,
    "search_typology_database": search_typology_database,
    "draft_sar_narrative": draft_sar_narrative,
    "calculate_risk_score": calculate_risk_score,
}

SYSTEM_PROMPT = """You are SARBot, an expert AML/financial crime investigation agent working for a regulated UK financial institution.

Your job is to investigate a suspicious activity alert by:
1. Calling get_customer_kyc to retrieve the customer profile
2. Calling get_transaction_history to review recent transactions
3. Calling search_typology_database to match the alert against known typologies
4. Calling draft_sar_narrative to produce a regulatory SAR narrative
5. Calling calculate_risk_score to produce a final risk score

Call the tools in order. After all tools have been called, return ONLY a valid JSON object (no markdown, no preamble) with this exact structure:
{
  "sar_narrative": "<full SAR narrative text>",
  "risk_score": <integer 0-100>,
  "recommendation": "<SUBMIT SAR | ESCALATE | MONITOR | DISMISS>",
  "red_flags": ["<flag1>", "<flag2>"],
  "summary": "<2-3 sentence executive summary>"
}"""


# ---------------------------------------------------------------------------
# Main agentic loop
# ---------------------------------------------------------------------------
def run_investigation(case_id: str, customer_id: str, alert_type: str) -> dict:
    """
    Run the full SARBot investigation using Claude's tool-use agentic loop.
    Returns a structured result dict matching InvestigationResult in models.py.
    """
    start_time = time.time()
    tool_call_log = []

    messages = [
        {
            "role": "user",
            "content": (
                f"Investigate the following alert:\n\n"
                f"Case ID: {case_id}\n"
                f"Customer ID: {customer_id}\n"
                f"Alert type: {alert_type}\n\n"
                f"Use all available tools to complete the investigation, then return your final JSON result."
            ),
        }
    ]

    # Agentic loop — keep going until Claude stops calling tools
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Append assistant turn to history
        messages.append({"role": "assistant", "content": response.content})

        # Check stop reason
        if response.stop_reason == "end_turn":
            # Claude is done — extract the final JSON text block
            break

        if response.stop_reason != "tool_use":
            # Unexpected stop — break anyway
            break

        # Process all tool_use blocks in this response
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            tool_name = block.name
            tool_input = block.input
            tool_id = block.id

            # Execute the tool
            tool_fn = TOOL_DISPATCH.get(tool_name)
            tool_start = time.time()
            try:
                output = tool_fn(**tool_input) if tool_fn else {"error": f"Unknown tool: {tool_name}"}
            except Exception as e:
                output = {"error": str(e)}
            duration = round(time.time() - tool_start, 3)

            # Log the call
            tool_call_log.append({
                "name": tool_name,
                "input": tool_input,
                "output": output,
                "duration": duration,
            })

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": json.dumps(output),
            })

        # Feed tool results back to Claude
        messages.append({"role": "user", "content": tool_results})

    # -----------------------------------------------------------------------
    # Extract final JSON from last assistant message
    # -----------------------------------------------------------------------
    final_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_text += block.text

    try:
        clean = final_text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(clean)
    except Exception:
        # Fallback if Claude didn't return valid JSON
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
