# backend/schemas/risk_schema.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union

class RiskFilterRequest(BaseModel):
    ticker: str
    signal: str = Field(pattern="^(BUY|SELL|HOLD)$")
    confidence: float
    sources: Dict[str, Union[float, str]] = {}   # ✅ supports float OR string
    current_price: float
    predicted_price: float
    past_prices: Optional[List[float]] = None

class RiskFilterResponse(BaseModel):
    decision: str
    action: str
    reasons: List[str]
    metrics: Dict[str, float]
    message: str
