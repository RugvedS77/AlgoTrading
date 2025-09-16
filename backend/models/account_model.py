from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, func
from database.postgresConn import Base
from sqlalchemy.orm import relationship

class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, index=True)
    #ticker_name = Column(String, index=True, nullable=True)
    total_equity = Column(Float, default=0.0)
    cash_available = Column(Float, default=0.0)
    risk_limits = Column(JSON)
    realized_drawdown_30d_pct = Column(Float, default=0.0)
    portfolio_volatility_30d_pct = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())  # Automatically set the current timestamp
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # Update timestamp on modification

    trades = relationship("Trade", back_populates="owner", cascade="all, delete-orphan")