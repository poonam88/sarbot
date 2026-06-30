from typing import Any

from pydantic import BaseModel, Field


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
