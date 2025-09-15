# allocators/llm_allocator.py
from pydantic import BaseModel, Field, conlist, validator
from typing import List, Optional, Literal, Dict, Any

# This represents a single stock holding in the portfolio
class Position(BaseModel):
    ticker: str
    quantity: float = Field(..., description="Number of shares held.")
    average_buy_price: float = Field(..., description="The average cost per share.")
    market_value: float = Field(..., description="The current market value of the position (quantity * current_price).")

# This is the simplified snapshot for the agents
class PortfolioState(BaseModel):
    total_equity: float = Field(..., description="The total value of the account (cash + market value of all positions).")
    cash_available: float = Field(..., description="The amount of free cash for trading.")
    open_positions: List[Position] = Field(default=[], description="A list of all currently held stock positions.")
    
    # Risk limits are essential for decision-making
    risk_limits: Dict[str, Any] = Field(..., description="Portfolio-level risk parameters.")
    
    # Optional performance metrics can provide further context
    portfolio_volatility_30d_pct: Optional[float] = None
    realized_drawdown_30d_pct: Optional[float] = None

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