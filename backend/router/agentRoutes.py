from fastapi import APIRouter, HTTPException, status
from agents.signalAgent import SignalAgent
from agents.CapitalAllocator import CapitalAllocator
from fastapi.encoders import jsonable_encoder
import json
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import uuid

from sqlalchemy.orm import Session
from database.postgresConn import get_db
from fastapi import Depends

from agents.riskSupervisorAgent import RiskSupervisorAgent
from schemas.risk_schema import RiskFilterResponse
from schemas.signal_schema import SignalResponse
from schemas.capital_schema import CapitalAllocatorResponse, PortfolioState
from models.account_model import Account
from models.agent_results_model import AgentResults
from router.newsRoutes import get_news_sentiment
from router.accountRoutes import get_account, get_all_accounts, create_account, update_account, fetch_account

from Pred_models.trend_pred_new import TrendPredict

from database.redisClient import redis_client

path = os.path.join("prediction.json")

router = APIRouter()

async def getCachedNews(ticker):
    redis_key = f"NewsSentiment:{ticker}"
    cached_news = redis_client.get(redis_key)
    #tried = 0 
    newsdata = [] 
    if cached_news:
        try:
            newsdata = json.loads(cached_news)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to parse cached news data")
    else:
        #call news agent to fetch news
        try:
            newsdata = await get_news_sentiment(symbol=ticker)
            print("No latest news was found so fetching new data")
            redis_client.set(redis_key, json.dumps(newsdata), ex=3600)  # Cache for 1 hour
            # tried = tried +1
            # if tried <=2 :
            #     getCachedNews(symbol)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to fetch news data")
    return newsdata 

def getCachedTrend(ticker: str) -> dict:
    redis_key = f"predictions:{ticker}:latest"
    cached_trend = redis_client.get(redis_key)

    if not cached_trend:
        raise HTTPException(status_code=404, detail=f"No trend data found in cache for {ticker}")

    try:
        # #Decode bytes to str only if necessary
        # decoded = {
        #     k.decode() if isinstance(k, bytes) else k:
        #     v.decode() if isinstance(v, bytes) else v
        #     for k, v in cached_trend.items()
        # }

        # # Get the latest timestamp
        # latest_timestamp = max(decoded.keys())
        # trenddata = json.loads(decoded[latest_timestamp])

        trenddata = json.loads(cached_trend.decode() if isinstance(cached_trend, bytes) else cached_trend)
        print("trendata what i got ",trenddata)
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



def save_agent_response(
    db: Session,
    user_name: str,
    ticker: str,
    signal_output: dict,
    risk_output: dict,
    allocator_output: dict
):
    trade_id = str(uuid.uuid4())  # unique id

    result = AgentResults(
        trade_id=trade_id,
        user_name=user_name,
        ticker=ticker,
        signal_output=signal_output,
        risk_output=risk_output,
        allocator_output=allocator_output
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result

#---------- TREND, SIGNAL, ALLOCATE endpoints ----------
executor = ThreadPoolExecutor(max_workers=2)
tp = TrendPredict()
@router.get("/trend")
async def trend_prediction(ticker: str = "TATAMOTORS"):
    try:
        # Try cache first
        latest_prediction = None
        try:
            latest_prediction = getCachedTrend(ticker)
        except HTTPException as e:
            if e.status_code != 404:  # only ignore "not found"
                raise

        if latest_prediction:
            return latest_prediction

        # If not cached → trigger simulation
        loop = asyncio.get_running_loop()
        loop.run_in_executor(executor, tp.run_simulation)
        print(f"⚡ Started simulation for {ticker} in background...")

        # Tell client prediction will come later
        return {
            "ticker": ticker,
            "status": "RUNNING",
            "message": "No cached prediction found. Simulation started...",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

signalAgent = SignalAgent()
@router.get("/signal", response_model=SignalResponse)
async def signal_endpoint(ticker: str = "TATAMOTORS"):
    try:
        trend_data = None
        
        # --- MODIFICATION: SMART POLLING IMPLEMENTATION ---

        # 1. First, try an instant fetch for maximum speed.
        print(f"Attempting instant fetch for {ticker}...")
        try:
            trend_data = getCachedTrend(ticker)
            print("✅ Data found instantly.")
        except HTTPException as e:
            # 2. If it's a 'Not Found' error, start polling.
            if e.status_code == 404:
                print(f"⚠️ No data found. Starting to poll for a short time...")
                max_wait_seconds = 20  # Max time to wait
                poll_interval = 2      # Check every 2 seconds
                waited = 0

                while trend_data is None and waited < max_wait_seconds:
                    await asyncio.sleep(poll_interval)
                    waited += poll_interval
                    print(f"   (polling... waited {waited}s)")
                    try:
                        # Try fetching again inside the loop
                        trend_data = getCachedTrend(ticker)
                    except HTTPException:
                        # Still not found, loop will continue
                        pass
            else:
                # Re-raise any other HTTP errors (like 500)
                raise e

        # 3. After polling, if data is still not found, return the WAIT message.
        if trend_data is None:
            print("❌ Polling timed out. No prediction available yet.")
            return {
                "ticker": ticker,
                "signal": "WAIT",
                "reason": f"Prediction data not available after waiting {max_wait_seconds}s.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # --- END OF MODIFICATION ---

        # --- Extract prediction info ---
        # pred_trend = trend_data.get("trend", "FLAT")
        # pred_price = trend_data.get("predicted_price", 0)
        # curr_price = trend_data.get("current_price", 0)
        # pred_time = trend_data.get("prediction_for", "")
        # conf = trend_data.get("confidence", 0.0)
        # sim_date = trend_data.get("simulation_date", "")

        # trend_score_map = {"UP": 1.0, "FLAT": 0.0, "DOWN": -1.0}
        # trend_score = trend_score_map.get(pred_trend.strip().upper(), 0.0)

        # --- News sentiment ---
        newsdata = await getCachedNews(ticker=ticker)
        if not newsdata:
            print("⚠️ No news data found, using default score=0")
        news_score = aggregate_scores(newsdata)

        # --- MODIFICATION: Assemble the complete data package ---
        signal_data_package = {
            "ticker": ticker,
            "trend_prob": trend_data.get("trend_prob", 0.5),
            "news_score": news_score,
            "current_price": trend_data.get("current_price", 0.0),
            "predicted_price": trend_data.get("predicted_price", 0.0),
            "movement": trend_data.get("movement", "FLAT"),
            "atr": trend_data.get("atr", 0.0),
            "ma_short": trend_data.get("ma_short", 0.0),
            "ma_long": trend_data.get("ma_long", 0.0),
            "pred_for": trend_data.get("prediction_for", ""),
            "sim_date": trend_data.get("simulation_date", "")
        }
        
        # --- Generate signal using the new agent ---
        signal_response = signalAgent.generate_signal(signal_data_package)

        redis_client.set(f"Signal_Response:{ticker}", json.dumps(signal_response))
        return signal_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signal generation failed: {e}")

capitalAllocator = CapitalAllocator(mode="auto")
@router.get("/allocate", response_model=CapitalAllocatorResponse)
async def cap_allocate(ticker: str, signal_output: dict, portfolio: dict):
    try:
        # signal_key = f"Signal_Response:{ticker}"
        # cached_signal = redis_client.get(signal_key)
        # if not cached_signal:
        #     await signal_endpoint(ticker=ticker)
        #     print("Signal data not found in cache")
        # else:
        #     print("Signal data found in cache")
        #     signal_data = json.loads(cached_signal)
        # signal = signal_data.get("response", {})
        # signal["ticker"] = ticker
        # current_price = signal["current_price"]

        allocation_response = capitalAllocator.allocate(signal_output, portfolio).dict()

        redis_client.set(f"Capital_Allocation:{ticker}", json.dumps(allocation_response))
        # return {"symbol": ticker, "allocation": allocation_response}
        return allocation_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


risk_supervisor = RiskSupervisorAgent(google_api_key=os.getenv("GOOGLE_API_KEY"))
# ---------- NEW risk filter endpoint ----------
# @router.get("/risk-filter", response_model=RiskFilterResponse)
# async def risk_filter(ticker: str, signal_output):
#     # 1. Call SignalAgent to generate signal
#     # signal_output = await signal_endpoint(ticker=ticker)

#     # 2. Use its output to feed RiskFilter
#     rf_input = RiskFilterRequest(
#         ticker=signal_output["ticker"],
#         signal=signal_output["signal"],
#         confidence=signal_output.get("confidence", 0.0),
#         sources=signal_output.get("sources", {}),
#         current_price=signal_output["current_price"],
#         predicted_price=signal_output["predicted_price"]
#     )

#     risk_decision = run_risk_filter(rf_input)

#     if risk_decision.action == "WAIT":
#         return RiskFilterResponse(
#             decision="SKIPPED",
#             action="WAIT",
#             reasons=["Risk filter blocked trade."],
#             metrics=risk_decision.metrics if hasattr(risk_decision, "metrics") else {},
#             message="Risk filter blocked trade."
#         )

#     return RiskFilterResponse(
#         decision=risk_decision.decision, 
#         action=risk_decision.action,
#         reasons=risk_decision.reasons,
#         metrics=risk_decision.metrics,
#         message=risk_decision.message
#     )


@router.post("/run-pipeline")
async def run_agentic_pipeline(ticker: str, username: str, db: Session = Depends(get_db)):
    # 1. Get portfolio from the database
    portfolio = fetch_account(username=username, db=db)
    print("Portfolio:", portfolio)
    portfolio_state = PortfolioState(**portfolio)

    # 2. Fetch or generate signal
    print(f"Executing pipeline: Always fetching the latest signal for {ticker}...")
    signal_output = await signal_endpoint(ticker=ticker)
    
    print("Fresh Signal Data:", signal_output)
    
    # 3. Run Capital Allocator
    alloc_decision = await cap_allocate(ticker, signal_output, portfolio)
    print("Allocation Decision:", alloc_decision)


    # 4. Get the final supervisory review from the Risk Supervisor
    final_decision = risk_supervisor.review_trade_setup(
        signal_output=signal_output,
        allocation_output=alloc_decision, # Pass the Pydantic model directly
        portfolio_state=portfolio_state
    )
    print("Risk Supervisor Output Received.")

    # 5. Save the outputs of all three agents to the database
    result = save_agent_response(
        db=db,
        user_name=username,
        ticker=signal_output["ticker"],
        signal_output=signal_output,
        # MODIFICATION: Save the entire supervisor output as a dictionary
        risk_output=final_decision.dict(),
        # MODIFICATION: Save the allocator output as a dictionary
        allocator_output=alloc_decision
    )

    # 6. Return the final, structured response to the frontend
    return {
        "status": "SAVED",
        "trade_id": result.trade_id,
        # MODIFICATION: Return allocator output as a dictionary
        "allocation": alloc_decision,
        # MODIFICATION: Use the correct variable 'final_decision'
        "risk_decision": final_decision.dict()
    }