import csv
import io
import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import agent
from models import CaseRecord, InvestigationRequest, InvestigationResult


load_dotenv(Path(__file__).parent / ".env")

app = FastAPI(title="Sarbot", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CASE_RESULTS: dict[str, CaseRecord] = {}
UPLOADED_CASES: dict[str, dict[str, Any]] = {}
DATA_PATH = Path(__file__).parent / "data" / "sample_cases.json"


def _normalize_case(raw_case: dict[str, Any], index: int) -> dict[str, Any]:
    case_id = str(raw_case.get("case_id") or f"UPLOAD-{index + 1:04d}")
    customer_id = str(raw_case.get("customer_id") or f"CUST-UPLOAD-{index + 1:04d}")
    alert_type = str(raw_case.get("alert_type") or "uploaded_alert")
    customer_name = str(
        raw_case.get("customer_name")
        or raw_case.get("name")
        or raw_case.get("customer")
        or "Uploaded Customer"
    )
    amount_gbp = raw_case.get("amount_gbp") or raw_case.get("amount") or 0
    summary = str(
        raw_case.get("summary")
        or f"Uploaded case for {customer_name} with alert type {alert_type}."
    )

    return {
        "case_id": case_id,
        "customer_id": customer_id,
        "alert_type": alert_type,
        "customer_name": customer_name,
        "date": str(raw_case.get("date") or raw_case.get("alert_date") or "Uploaded"),
        "status": str(raw_case.get("status") or "Uploaded"),
        "summary": summary,
        "amount_gbp": amount_gbp,
        "jurisdictions": raw_case.get("jurisdictions", []),
        "pattern": raw_case.get("pattern", alert_type),
        "risk_score": int(raw_case.get("risk_score") or 0),
        "recommendation": raw_case.get("recommendation", "Run investigation."),
        "red_flags": raw_case.get("red_flags", []),
    }


def _parse_uploaded_cases(filename: str, content: bytes) -> list[dict[str, Any]]:
    text = content.decode("utf-8-sig")
    lower_name = filename.lower()

    if lower_name.endswith(".json"):
        payload = json.loads(text)
        raw_cases = payload if isinstance(payload, list) else payload.get("cases", [payload])
        if not isinstance(raw_cases, list):
            raise ValueError("JSON upload must be an object, a list, or {'cases': [...]}.")
        return [_normalize_case(case, index) for index, case in enumerate(raw_cases)]

    if lower_name.endswith(".csv"):
        rows = list(csv.DictReader(io.StringIO(text)))
        if not rows:
            raise ValueError("CSV upload did not contain any case rows.")
        return [_normalize_case(row, index) for index, row in enumerate(rows)]

    raise ValueError("Upload must be a .json or .csv file.")


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "SARBot API",
        "status": "ok",
        "frontend": "http://127.0.0.1:3000",
        "docs": "http://127.0.0.1:8000/docs",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/investigate", response_model=InvestigationResult)
def investigate(request: InvestigationRequest) -> InvestigationResult:
    result = agent.run_investigation(
        request.case_id,
        request.customer_id,
        request.alert_type,
    )
    CASE_RESULTS[request.case_id] = CaseRecord(request=request, result=result)
    return result


@app.post("/cases/seed", response_model=dict[str, Any])
def seed_cases() -> dict[str, Any]:
    with DATA_PATH.open("r", encoding="utf-8") as file:
        sample_cases = json.load(file)

    CASE_RESULTS.clear()
    for sample_case in sample_cases[:3]:
        request = InvestigationRequest(
            case_id=sample_case["case_id"],
            customer_id=sample_case["customer_id"],
            alert_type=sample_case["alert_type"],
        )
        result = InvestigationResult(
            sar_narrative=(
                f"Seeded demo case for {sample_case['customer_name']}: "
                f"{sample_case['summary']}"
            ),
            risk_score=sample_case["risk_score"],
            recommendation=sample_case["recommendation"],
            red_flags=sample_case["red_flags"],
            tool_call_log=[],
            total_time_seconds=0.0,
        )
        CASE_RESULTS[request.case_id] = CaseRecord(request=request, result=result)

    return {
        "seeded": len(CASE_RESULTS),
        "case_ids": list(CASE_RESULTS.keys()),
    }


@app.post("/cases/upload", response_model=dict[str, Any])
async def upload_cases(file: UploadFile = File(...)) -> dict[str, Any]:
    try:
        uploaded_cases = _parse_uploaded_cases(
            file.filename or "uploaded.json",
            await file.read(),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    for uploaded_case in uploaded_cases:
        UPLOADED_CASES[uploaded_case["case_id"]] = uploaded_case

    return {
        "uploaded": len(uploaded_cases),
        "cases": uploaded_cases,
    }


@app.get("/case/{case_id}", response_model=CaseRecord)
def get_case(case_id: str) -> CaseRecord:
    record = CASE_RESULTS.get(case_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Case result not found.")
    return record
