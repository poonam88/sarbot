import os
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv


load_dotenv(Path(__file__).parent / ".env")


MOCK_CUSTOMERS: dict[str, dict[str, Any]] = {
    "CUST-7781": {
        "name": "Aarav Mehta",
        "kyc_tier": "enhanced_due_diligence",
        "risk_rating": "medium-high",
        "pep_flag": False,
        "sanctions_flag": False,
        "last_review_date": "2026-03-14",
        "declared_turnover": 950000,
        "prior_alerts": 2,
    },
    "CUST-3390": {
        "name": "Priya Shah",
        "kyc_tier": "standard_due_diligence",
        "risk_rating": "high",
        "pep_flag": False,
        "sanctions_flag": False,
        "last_review_date": "2026-01-29",
        "declared_turnover": 185000,
        "prior_alerts": 4,
    },
    "CUST-MERIDIAN-001": {
        "name": "Meridian Trading Ltd",
        "kyc_tier": "enhanced_due_diligence",
        "risk_rating": "high",
        "pep_flag": False,
        "sanctions_flag": False,
        "last_review_date": "2024-09-18",
        "declared_turnover": 1200000,
        "prior_alerts": 3,
    },
    "CUST-OSEI-039": {
        "name": "K. Osei-Mensah",
        "kyc_tier": "standard_due_diligence",
        "risk_rating": "medium-high",
        "pep_flag": False,
        "sanctions_flag": False,
        "last_review_date": "2024-10-02",
        "declared_turnover": 92000,
        "prior_alerts": 2,
    },
    "CUST-BLUEWAVE-035": {
        "name": "BlueWave Capital LP",
        "kyc_tier": "enhanced_due_diligence",
        "risk_rating": "low",
        "pep_flag": False,
        "sanctions_flag": False,
        "last_review_date": "2024-11-21",
        "declared_turnover": 8500000,
        "prior_alerts": 0,
    },
}


MOCK_TRANSACTIONS: dict[str, list[dict[str, Any]]] = {
    "CUST-7781": [
        {
            "tx_id": "TX-GB-9001",
            "date": "2026-06-20",
            "amount_gbp": 9850.0,
            "counterparty": "Northbridge Imports Ltd",
            "jurisdiction": "GB",
            "flag_type": "large_inbound",
            "invoice_on_file": True,
        },
        {
            "tx_id": "TX-GB-9002",
            "date": "2026-06-21",
            "amount_gbp": 9630.0,
            "counterparty": "Blue Harbor Trading FZE",
            "jurisdiction": "AE",
            "flag_type": "rapid_movement_of_funds",
            "invoice_on_file": False,
        },
        {
            "tx_id": "TX-GB-9003",
            "date": "2026-06-24",
            "amount_gbp": 7200.0,
            "counterparty": "Dover Freight Services",
            "jurisdiction": "GB",
            "flag_type": "trade_payment",
            "invoice_on_file": True,
        },
    ],
    "CUST-3390": [
        {
            "tx_id": "TX-GB-9101",
            "date": "2026-06-18",
            "amount_gbp": 7900.0,
            "counterparty": "Branch Cash Deposit",
            "jurisdiction": "GB",
            "flag_type": "cash_deposit",
            "invoice_on_file": False,
        },
        {
            "tx_id": "TX-GB-9102",
            "date": "2026-06-19",
            "amount_gbp": 7850.0,
            "counterparty": "Branch Cash Deposit",
            "jurisdiction": "GB",
            "flag_type": "structuring",
            "invoice_on_file": False,
        },
        {
            "tx_id": "TX-GB-9103",
            "date": "2026-06-21",
            "amount_gbp": 8100.0,
            "counterparty": "Branch Cash Deposit",
            "jurisdiction": "GB",
            "flag_type": "structuring",
            "invoice_on_file": False,
        },
    ],
    "CUST-MERIDIAN-001": [
        {
            "tx_id": "TX-MER-8841-01",
            "date": "2024-12-03",
            "amount_gbp": 9850.0,
            "counterparty": "Al Noor General Trading FZE",
            "jurisdiction": "UAE",
            "flag_type": "structuring",
            "invoice_on_file": False,
        },
        {
            "tx_id": "TX-MER-8841-02",
            "date": "2024-12-04",
            "amount_gbp": 9975.0,
            "counterparty": "Rotterdam Commodities BV",
            "jurisdiction": "NL",
            "flag_type": "trade_payment",
            "invoice_on_file": True,
        },
        {
            "tx_id": "TX-MER-8841-03",
            "date": "2024-12-05",
            "amount_gbp": 9615.0,
            "counterparty": "Kyrenia Holdings Ltd",
            "jurisdiction": "Cyprus",
            "flag_type": "structuring",
            "invoice_on_file": False,
        },
        {
            "tx_id": "TX-MER-8841-04",
            "date": "2024-12-06",
            "amount_gbp": 18400.0,
            "counterparty": "Al Noor General Trading FZE",
            "jurisdiction": "UAE",
            "flag_type": "rapid_movement_of_funds",
            "invoice_on_file": False,
        },
    ],
    "CUST-OSEI-039": [
        {
            "tx_id": "TX-OSE-8839-01",
            "date": "2024-12-02",
            "amount_gbp": 4900.0,
            "counterparty": "Branch Cash Deposit",
            "jurisdiction": "UK",
            "flag_type": "cash_deposit",
            "invoice_on_file": False,
        },
        {
            "tx_id": "TX-OSE-8839-02",
            "date": "2024-12-04",
            "amount_gbp": 4750.0,
            "counterparty": "Branch Cash Deposit",
            "jurisdiction": "UK",
            "flag_type": "structuring",
            "invoice_on_file": False,
        },
        {
            "tx_id": "TX-OSE-8839-03",
            "date": "2024-12-06",
            "amount_gbp": 4825.0,
            "counterparty": "Branch Cash Deposit",
            "jurisdiction": "UK",
            "flag_type": "structuring",
            "invoice_on_file": False,
        },
    ],
    "CUST-BLUEWAVE-035": [
        {
            "tx_id": "TX-BLU-8835-01",
            "date": "2024-12-01",
            "amount_gbp": 62500.0,
            "counterparty": "Harbor Street Securities LLC",
            "jurisdiction": "US",
            "flag_type": "wire_transfer",
            "invoice_on_file": True,
        },
        {
            "tx_id": "TX-BLU-8835-02",
            "date": "2024-12-08",
            "amount_gbp": 62500.0,
            "counterparty": "Harbor Street Securities LLC",
            "jurisdiction": "US",
            "flag_type": "wire_transfer",
            "invoice_on_file": True,
        },
    ],
}


TYPOLOGIES = [
    {
        "typology_name": "FATF Typology 12 (TBML)",
        "source": "Financial Action Task Force",
        "description": "Trade-based money laundering involving mispriced goods, false invoicing, or trade payments with limited commercial rationale.",
        "red_flags": [
            "Payments inconsistent with declared business activity",
            "Missing or weak invoice documentation",
            "Use of overseas trading counterparties without a clear relationship",
        ],
    },
    {
        "typology_name": "FCA §2.4 structuring",
        "source": "Financial Conduct Authority",
        "description": "Repeated transactions arranged to avoid scrutiny, internal thresholds, or expected monitoring triggers.",
        "red_flags": [
            "Multiple similar-value transactions over a short period",
            "Amounts clustered below review thresholds",
            "Activity inconsistent with expected customer profile",
        ],
    },
    {
        "typology_name": "FATF Typology 26 (bulk cash)",
        "source": "Financial Action Task Force",
        "description": "Movement or placement of cash proceeds through repeated deposits, couriers, or cash-intensive channels.",
        "red_flags": [
            "Frequent cash deposits with limited economic rationale",
            "Cash activity not aligned to declared turnover",
            "Rapid onward movement after cash placement",
        ],
    },
]


def get_customer_kyc(customer_id: str) -> dict[str, Any]:
    """Return mock customer KYC data."""
    return MOCK_CUSTOMERS.get(
        customer_id,
        {
            "name": "Unknown Customer",
            "kyc_tier": "standard_due_diligence",
            "risk_rating": "medium",
            "pep_flag": False,
            "sanctions_flag": False,
            "last_review_date": "2026-02-01",
            "declared_turnover": 250000,
            "prior_alerts": 1,
        },
    )


def get_transaction_history(customer_id: str, days: int) -> list[dict[str, Any]]:
    """Return mock transaction history for the requested lookback period."""
    _ = days
    return MOCK_TRANSACTIONS.get(customer_id, MOCK_TRANSACTIONS["CUST-7781"])


def search_typology_database(keywords: list[str]) -> list[dict[str, Any]]:
    """Return hardcoded typologies matching any supplied keyword."""
    normalized_keywords = [keyword.lower() for keyword in keywords]
    if not normalized_keywords:
        return TYPOLOGIES

    matches = []
    for typology in TYPOLOGIES:
        searchable_text = " ".join(
            [
                typology["typology_name"],
                typology["source"],
                typology["description"],
                " ".join(typology["red_flags"]),
            ]
        ).lower()
        if any(keyword in searchable_text for keyword in normalized_keywords):
            matches.append(typology)

    return matches or TYPOLOGIES


def draft_sar_narrative(case_summary: dict[str, Any]) -> dict[str, Any]:
    """Draft an FCA-style SAR narrative from case summary data."""
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
        f"A total of {tx_count} transactions amounting to £{total_amount:,.2f} were reviewed. "
        f"The activity displays characteristics consistent with the following typologies: {typology_names or 'unspecified patterns'}. "
        "Transactions lack supporting documentation and involve multiple high-risk jurisdictions, "
        "which is inconsistent with the customer's declared business profile. "
        "The financial crime team recommends escalation to the MLRO for SAR filing consideration "
        "under Part 7 of the Proceeds of Crime Act 2002."
    )

    return {
        "narrative_text": narrative_text,
        "regulatory_basis": "UK Proceeds of Crime Act 2002; FCA financial crime systems and controls expectations",
        "word_count": len(narrative_text.split()),
    }


def calculate_risk_score(factors: dict[str, Any]) -> dict[str, Any]:
    """Calculate a mock financial crime risk score from weighted factors."""
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
        recommendation = "Escalate for MLRO review and consider SAR submission."
        escalation_target = "MLRO"
        confidence = "high"
    elif score >= 50:
        recommendation = "Escalate to financial crime investigations for enhanced review."
        escalation_target = "Financial Crime Investigations"
        confidence = "medium"
    else:
        recommendation = "Document rationale and continue routine monitoring."
        escalation_target = "Level 1 AML Operations"
        confidence = "medium"

    return {
        "score": score,
        "recommendation": recommendation,
        "confidence": confidence,
        "escalation_target": escalation_target,
        "estimated_hours_saved": 2.5,
    }


TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": "get_customer_kyc",
        "description": "Fetch realistic mock KYC data for a customer.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Unique customer identifier.",
                }
            },
            "required": ["customer_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_transaction_history",
        "description": "Fetch realistic mock transaction history for a customer.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Unique customer identifier.",
                },
                "days": {
                    "type": "integer",
                    "description": "Lookback period in days.",
                    "minimum": 1,
                },
            },
            "required": ["customer_id", "days"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "search_typology_database",
        "description": "Search hardcoded financial crime typologies by keyword.",
        "parameters": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Typology search keywords such as TBML, structuring, or cash.",
                }
            },
            "required": ["keywords"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "draft_sar_narrative",
        "description": "Draft an FCA-compliant SAR narrative from case details using GPT-4o.",
        "parameters": {
            "type": "object",
            "properties": {
                "case_summary": {
                    "type": "object",
                    "description": "Case summary containing customer_info, transactions, and typologies.",
                    "properties": {
                        "customer_info": {"type": "object"},
                        "transactions": {
                            "type": "array",
                            "items": {"type": "object"},
                        },
                        "typologies": {
                            "type": "array",
                            "items": {"type": "object"},
                        },
                    },
                    "required": ["customer_info", "transactions", "typologies"],
                    "additionalProperties": True,
                }
            },
            "required": ["case_summary"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "calculate_risk_score",
        "description": "Calculate a mock risk score from financial crime factors.",
        "parameters": {
            "type": "object",
            "properties": {
                "factors": {
                    "type": "object",
                    "properties": {
                        "velocity": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                        },
                        "structuring": {"type": "boolean"},
                        "jurisdiction_count": {
                            "type": "integer",
                            "minimum": 1,
                        },
                        "kyc_tier": {"type": "string"},
                        "prior_alerts": {
                            "type": "integer",
                            "minimum": 0,
                        },
                    },
                    "required": [
                        "velocity",
                        "structuring",
                        "jurisdiction_count",
                        "kyc_tier",
                        "prior_alerts",
                    ],
                    "additionalProperties": False,
                }
            },
            "required": ["factors"],
            "additionalProperties": False,
        },
    },
]


TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    "get_customer_kyc": get_customer_kyc,
    "get_transaction_history": get_transaction_history,
    "search_typology_database": search_typology_database,
    "draft_sar_narrative": draft_sar_narrative,
    "calculate_risk_score": calculate_risk_score,
}
