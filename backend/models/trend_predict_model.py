from sqlalchemy.orm import relationship
from database.postgresConn import Base
from sqlalchemy import Column, Integer, String, Float, DateTime, func

class TrendPredict(Base):
    __tablename__ = 'trend_predictions'

    id = Column(Integer, primary_key=True, index=True)
    stock_symbol = Column(String, unique=True, index=True)
    trend = Column(String)
    predicted_price = Column(Float)
    current_price = Column(Float)
    created_at = Column(DateTime, default=func.now())