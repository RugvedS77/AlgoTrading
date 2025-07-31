from fastapi import APIRouter, HTTPException
from schemas.news_schema import NewsItem,  AgentResponse
from typing import List
from agents import newsAnalysisAgent

router = APIRouter(tags=["News"])

agent = newsAnalysisAgent.NewsAgent()


@router.get("/news/{symbol}", response_model=List[NewsItem])
async def get_combined_news(symbol: str):
        return await agent.get_combined_news(symbol)

@router.get("/news/sentiment/{symbol}", response_model=AgentResponse)
async def get_news_sentiment(symbol: str):
        """
        Get sentiment analysis for news articles related to a specific symbol.
        """
        try:
                news_item = await agent.get_news_with_sentiment(symbol)
                return AgentResponse(symbol=symbol, news_items=news_item)
        except Exception as e:
                print(f"Error in sentiment fetch: {e}")
                raise HTTPException(status_code=500, detail="Sentiment analysis failed")