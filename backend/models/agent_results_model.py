from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from database.postgresConn import Base

class AgentResults(Base):
    __tablename__ = "agent_results"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, index=True)
    trade_id = Column(String, unique=True, index=True)   # unique identifier for each run
    ticker = Column(String, index=True)

    signal_output = Column(JSON)       # Signal Agent JSON
    risk_output = Column(JSON)         # Risk Filter Agent JSON
    allocator_output = Column(JSON)    # Capital Allocator JSON

    created_at = Column(DateTime, default=datetime.utcnow)
