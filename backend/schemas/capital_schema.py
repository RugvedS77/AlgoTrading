# allocators/llm_allocator.py
from pydantic import BaseModel, Field, conlist, validator
from typing import List, Optional, Literal, Dict

class Position(BaseModel):
    ticker: str
    side: Literal["LONG", "SHORT"]
    qty: float
    avg_price: float
    market_value: float

class PortfolioState(BaseModel):
    total_equity: float                   # total account value
    cash_available: float
    open_positions: List[Position] = []
    risk_limits: dict
    realized_drawdown_30d_pct: float = 0.0
    portfolio_volatility_30d_pct: float = 0.0

# class AllocationDecision(BaseModel):
#     ticker: str
#     intent: Literal["ENTER", "INCREASE", "DECREASE", "EXIT", "SKIP"]
#     side: Literal["LONG", "SHORT", "NA"]
#     allocation_cash: float                # absolute cash allocation (₹/$)
#     allocation_pct_of_equity: float       # 0..1
#     position_size_qty: float              # computed using current_price
#     suggested_stop_loss: Optional[float]  # price level
#     suggested_take_profit: Optional[float]
#     rationale: str

#     @validator("allocation_cash", "position_size_qty", "allocation_pct_of_equity")
#     def non_negative(cls, v):
#         if v is None: return v
#         if v < 0: raise ValueError("negative values not allowed")
#         return v

# class CapitalAllocatorRequest(BaseModel):
#     ticker: str
#     signal: str
#     confidence: float
#     current_price: float
#     predicted_price: float
#     sources: Optional[Dict[str, float]] = {}
#     portfolio: dict  # Portfolio data (e.g., total_equity, cash_available, etc.)

class CapitalAllocatorResponse(BaseModel):
    ticker: str
    intent: Literal["ENTER", "INCREASE", "DECREASE", "EXIT", "SKIP"]
    side: Literal["LONG", "SHORT", "NA"]
    allocation_cash: float
    allocation_pct_of_equity: float
    position_size_qty: float
    suggested_stop_loss: Optional[float]
    suggested_take_profit: Optional[float]
    rationale: str
    prediction_for_time: Optional[str]