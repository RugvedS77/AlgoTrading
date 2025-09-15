# backend/schemas/risk_schema.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Literal

# class RiskFilterRequest(BaseModel):
#     ticker: str
#     signal: str = Field(pattern="^(BUY|SELL|HOLD)$")
#     confidence: float
#     sources: Dict[str, Union[float, str]] = {}   # ✅ supports float OR string
#     current_price: float
#     predicted_price: float
#     # past_prices: Optional[List[float]] = None

class RiskFilterResponse(BaseModel):
    decision: str
    action: str
    reasons: List[str]
    metrics: Dict[str, float]
    message: str

# The new response schema for the LLM Supervisor
class RiskSupervisorResponse(BaseModel):
    final_verdict: Literal["PROCEED", "PROCEED WITH CAUTION", "REJECT"]
    summary_rationale: str
    key_positive_factors: List[str]
    key_risks_and_concerns: List[str]
    suggested_action: Literal["BUY", "SELL", "HOLD"]
