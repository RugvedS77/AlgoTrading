from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RiskLimits(BaseModel):
    max_allocation_pct: float = 0.15
    max_risk_per_trade_pct: float = 0.02
    max_exposure_per_ticker_pct: float = 0.20

class AccountSchema(BaseModel):
    id: int
    user_name: str
    total_equity: float
    cash_available: float
    risk_limits: RiskLimits
    realized_drawdown_30d_pct: Optional[float] = 0.05
    portfolio_volatility_30d_pct: Optional[float] = 0.18
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class AccountCreate(BaseModel):
    user_name: str
    total_equity: float
    cash_available: float
    risk_limits: Optional[RiskLimits] = RiskLimits()