from fastapi import APIRouter, HTTPException, status
from agents.signalAgent import SignalAgent
import json
import os

from database.redisClient import redis_client

path = os.path.join("prediction.json")

router = APIRouter()

def findPred(path, symbol) -> tuple[str, float, float, float]:
    try:
        with open(path, "r") as f:
            data = json.load(f)
        
        for item in data:
            if item["stock"] == symbol:
                print("Found prediction for", symbol)
                print(item["trend_prediction"].get("trend"))
                return item["trend_prediction"].get("trend") , item["trend_prediction"].get("confidence") , item["trend_prediction"].get("predicted_price") , item["trend_prediction"].get("current_price")

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction for symbol '{symbol}' not found"
            )
    
    except Exception as e :
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                             detail=str(e))

def getCachedNews(symbol):
    redis_key = f"NewsSentiment:{symbol}"
    cached_news = redis_client.get(redis_key)
    
    newsdata = [] 
    if cached_news:
        try:
            newsdata = json.loads(cached_news)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to parse cached news data")
        
    return newsdata  


def aggregate_scores(newsdata):
    sentiment_map = {"positive": 1, "neutral": 0, "negative": -1}

    articles = newsdata.get("news_items", []) if isinstance(newsdata, dict) else newsdata

    news_sentiments = [item['sentiment'].lower() for item in articles if 'sentiment' in item]
    print("News Sentiments:", news_sentiments)

    scores = [sentiment_map[s] for s in news_sentiments]
    if not scores:
        return 0
    avg_score = sum(scores) / len(scores)

    if avg_score > 0.2:
        aggregated = "positive"
    elif avg_score < -0.2:
        aggregated = "negative"
    else:
        aggregated = "neutral"

    print("Avg Score:", avg_score)
    print("Aggregated Sentiment:", aggregated)

    return avg_score


signalAgent = SignalAgent()
@router.get("/signal")
def signal(symbol:str):
    trend , conf, pred_price, curr_price= findPred(path=path,symbol=symbol)
    print(trend,conf)

    newsdata = getCachedNews(symbol=symbol)
    print("News Data:", newsdata)

    news_score = aggregate_scores(newsdata)
    return signalAgent.generate_signal(ticker=symbol,
                                       news_score=news_score,
                                        current_price=curr_price,
                                        predicted_price=pred_price,
                                        movement=trend,
                                       trend_score=conf)