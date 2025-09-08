from fastapi import APIRouter, HTTPException, status
from agents.signalAgent import SignalAgent
from agents.CapitalAllocator import CapitalAllocator
from fastapi.encoders import jsonable_encoder
import json
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session
from database.postgresConn import get_db
from fastapi import Depends

from agents.riskFilterAgent import RiskFilterInput, run_risk_filter
from schemas.risk_schema import RiskFilterRequest, RiskFilterResponse
from router.newsRoutes import get_news_sentiment

from Pred_models.trend_prediction import TrendPredict

from database.redisClient import redis_client

path = os.path.join("prediction.json")

router = APIRouter()

# def findPred(path, symbol) -> tuple[str, float, float, float]:
#     try:
#         with open(path, "r") as f:
#             data = json.load(f)
        
#         for item in data:
#             if item["stock"] == symbol:
#                 print("Found prediction for", symbol)
#                 print(item["trend_prediction"].get("trend"))
#                 return item["trend_prediction"].get("trend") , item["trend_prediction"].get("confidence") , item["trend_prediction"].get("predicted_price") , item["trend_prediction"].get("current_price")

#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Prediction for symbol '{symbol}' not found"
#             )
    
#     except Exception as e :
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                              detail=str(e))

def getCachedNews(symbol):
    redis_key = f"NewsSentiment:{symbol}"
    cached_news = redis_client.get(redis_key)
    tried = 0 
    newsdata = [] 
    if cached_news:
        try:
            newsdata = json.loads(cached_news)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to parse cached news data")
    else:
        #call news agent to fetch news
        try:
            newsdata = get_news_sentiment(symbol=symbol)
            print("No latest news was found so fetching new data")
            redis_client.set(redis_key, json.dumps(newsdata), ex=3600)  # Cache for 1 hour
            tried = tried +1
            if tried <=2 :
                getCachedNews(symbol)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to fetch news data")
    return newsdata 

def getCachedTrend(symbol: str) -> dict:
    redis_key = f"predictions:{symbol}"
    cached_trend = redis_client.hgetall(redis_key)

    if not cached_trend:
        raise HTTPException(status_code=404, detail=f"No trend data found in cache for {symbol}")

    try:
        # Decode bytes to str only if necessary
        decoded = {
            k.decode() if isinstance(k, bytes) else k:
            v.decode() if isinstance(v, bytes) else v
            for k, v in cached_trend.items()
        }

        # Get the latest timestamp
        latest_timestamp = max(decoded.keys())
        trenddata = json.loads(decoded[latest_timestamp])

        return trenddata

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse cached trend data: {str(e)}")
 


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


executor = ThreadPoolExecutor(max_workers=2)
tp = TrendPredict()
@router.get("/trend")
async def trend_prediction(symbol: str = "TATAMOTORS"):
    try:
        # Run simulation in background (non-blocking)
        loop = asyncio.get_event_loop()
        loop.run_in_executor(executor, tp.run_simulation)

        # Get latest cached trend (already decodes and parses JSON)
        latest_prediction = getCachedTrend(symbol)

        return latest_prediction

    except HTTPException:  # propagate known exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


signalAgent = SignalAgent()
@router.get("/signal")
async def signal(symbol:str):
    # trend , conf, pred_price, curr_price= findPred(path=path,symbol=symbol)
    # print(trend,conf)
        # Call /trend to trigger background simulation
    trend_data = await trend_prediction(symbol)

    pred_trend = trend_data.get("predicted_trend", 0)
    pred_price = trend_data.get("predicted_price", 0)
    curr_price = trend_data.get("current_price", 0)
    pred_time = trend_data.get("timestamp", "")

    trend_score_map = {"UP": 1.0, "FLAT": 0.0, "DOWN": -1.0}
    trend_str = pred_trend.strip().upper() 
    trend_score = trend_score_map.get(pred_trend, 0.0)


    newsdata = getCachedNews(symbol=symbol)
    print("News Data:", newsdata)

    news_score = aggregate_scores(newsdata)

    
    response =  signalAgent.generate_signal(ticker=symbol,
                                            trend_score=trend_score,
                                       news_score=news_score,
                                        current_price=curr_price,
                                        predicted_price=pred_price,
                                        movement=pred_trend,
                                        pred_time=pred_time)
    
    data = {"response": response}
    data = jsonable_encoder(data)
    redis_client.set(f"Signal_Response:{symbol}", json.dumps(data))

    return response

capitalAllocator = CapitalAllocator(mode="auto")

@router.get("/allocate")
def allocate(symbol: str, current_price: float, available_capital: float):
    try:
        signal_key = f"Signal_Response:{symbol}"
        cached_signal = redis_client.get(signal_key)
        if not cached_signal:
            raise HTTPException(status_code=404, detail="Signal data not found in cache")

        signal_data = json.loads(cached_signal)
        signal = signal_data.get("response", {})
        signal["ticker"] = symbol
        signal["current_price"] = current_price

        portfolio = {
            "total_equity": available_capital,
            "cash_available": available_capital,
            "open_positions": [],
            "risk_limits": {"max_allocation_pct": 0.15, "max_risk_per_trade_pct": 0.02, "max_exposure_per_ticker_pct": 0.20},
            "realized_drawdown_30d_pct": 0.05,
            "portfolio_volatility_30d_pct": 0.18,
        }

        allocation = capitalAllocator.allocate(signal, portfolio).dict()

        redis_client.set(f"Capital_Allocation:{symbol}", json.dumps(allocation))
        return {"symbol": symbol, "allocation": allocation}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ---------- NEW risk filter endpoint ----------
@router.get("/risk-filter", response_model=RiskFilterResponse)
def risk_filter(symbol: str):
    # 1. Call SignalAgent to generate signal
    signal_output = signal(symbol=symbol)

    # 2. Use its output to feed RiskFilter
    rf_input = RiskFilterInput(
        ticker=signal_output["ticker"],
        signal=signal_output["signal"],
        confidence=signal_output["confidence"],
        sources=signal_output.get("sources", {}),
        current_price=signal_output["current_price"],
        predicted_price=signal_output["predicted_price"],
        past_prices=signal_output.get("past_prices", []),
    )

    decision = run_risk_filter(rf_input)

    return RiskFilterResponse(
        decision=decision.decision, 
        action=decision.action,
        reasons=decision.reasons,
        metrics=decision.metrics,
        message=decision.message
    )

