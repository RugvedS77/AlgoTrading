from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from typing import List
import json

from database.redisClient import redis_client
from schemas.news_schema import NewsItem,  AgentResponse
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
                response = AgentResponse(symbol=symbol, news_items=news_item)

                data = {"news_items": response.news_items}
                data = jsonable_encoder(data)
                redis_client.set(f"NewsSentiment:{symbol}", json.dumps(data))
                return response
        except Exception as e:
                print(f"Error in sentiment fetch: {e}")
                raise HTTPException(status_code=500, detail="Sentiment analysis failed")