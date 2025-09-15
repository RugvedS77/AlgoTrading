# models/trade_model.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func, Enum
from sqlalchemy.orm import relationship
from database.postgresConn import Base
import enum

class TradeSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class Trade(Base):
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    side = Column(Enum(TradeSide), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    
    # Foreign Key to link to the Account
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    
    owner = relationship("Account", back_populates="trades")