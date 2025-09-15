from pydantic import BaseModel
from typing import Optional

class SignalResponse(BaseModel):
    ticker: str
    signal: str
    reason: Optional[str] = None
    current_price: float
    predicted_price: float
    movement: str
    pred_time: str
    confidence: Optional[float] = None
    news_score: Optional[float] = None
    atr: Optional[float] = None
    ma_short: Optional[float] = None
    ma_long: Optional[float] = None
    prediction_for: Optional[str] = None
    simulation_date: Optional[str] = None