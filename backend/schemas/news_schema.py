from pydantic import BaseModel
from typing import List, Optional

class NewsItem(BaseModel):
    title: str
    summary: str
    link: str
    sentiment: Optional[str] = None  
    source: str

class NewsItemWithSentiment(BaseModel):
    title: str
    summary: str
    link: str
    sentiment: str

class AgentResponse(BaseModel):
    symbol: str
    news_items: List[NewsItemWithSentiment]