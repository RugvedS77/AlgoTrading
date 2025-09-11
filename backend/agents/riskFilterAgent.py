# # backend/agents/riskFilterAgent.py
# from __future__ import annotations
# from dataclasses import dataclass
# from typing import List, Dict, Optional
# import math

# # ---- config thresholds ----
# CONFIDENCE_MIN = 0.60
# VOLATILITY_MAX = 0.05        # 5% daily std dev
# STOP_LOSS_PCT  = 0.03        # 3% per trade
# RR_MIN         = 1.5
# NEWS_NEG_CUTOFF = -0.50
# ALLOW_BUY_ON_NEG_NEWS = False


# @dataclass
# class RiskFilterInput:
#     ticker: str
#     signal: str               # BUY | SELL | HOLD
#     confidence: float
#     sources: Dict[str, float]
#     current_price: float
#     predicted_price: float
#     past_prices: Optional[List[float]] = None


# @dataclass
# class RiskFilterDecision:
#     accept: bool
#     action: str
#     reasons: List[str]
#     metrics: Dict[str, float]


# def _calc_volatility(past_prices: List[float]) -> Optional[float]:
#     if not past_prices or len(past_prices) < 2:
#         return None
#     returns = []
#     for i in range(1, len(past_prices)):
#         if past_prices[i-1] == 0:
#             continue
#         returns.append((past_prices[i] - past_prices[i-1]) / past_prices[i-1])
#     if not returns:
#         return None
#     mean = sum(returns) / len(returns)
#     var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1) if len(returns) > 1 else 0.0
#     return math.sqrt(var)


# def _reward_risk(curr: float, pred: float) -> Dict[str, float]:
#     risk = abs(curr * STOP_LOSS_PCT)
#     reward = abs(pred - curr)
#     rr = (reward / risk) if risk > 0 else 0.0
#     return {"risk": risk, "reward": reward, "rr": rr}


# def run_risk_filter(payload: RiskFilterInput) -> RiskFilterDecision:
#     reasons, metrics = [], {}
#     action = payload.signal
#     accept = True

#     # 1) confidence
#     metrics["confidence"] = payload.confidence
#     if payload.confidence < CONFIDENCE_MIN:
#         reasons.append(f"confidence {payload.confidence:.2f} < {CONFIDENCE_MIN}")
#         accept, action = False, "HOLD"

#     # 2) news impact
#     news_score = float(payload.sources.get("news_score", 0.0))
#     metrics["news_score"] = news_score
#     if news_score <= NEWS_NEG_CUTOFF and payload.signal == "BUY":
#         if not ALLOW_BUY_ON_NEG_NEWS:
#             reasons.append(f"negative news_score {news_score:.2f} ≤ {NEWS_NEG_CUTOFF}")
#             accept, action = False, "HOLD"

#     # 3) volatility
#     vol = _calc_volatility(payload.past_prices) if payload.past_prices else None
#     if vol is not None:
#         metrics["volatility"] = vol
#         if vol > VOLATILITY_MAX:
#             reasons.append(f"volatility {vol:.3f} > {VOLATILITY_MAX:.3f}")
#             accept, action = False, "HOLD"

#     # 4) reward:risk
#     rr_metrics = _reward_risk(payload.current_price, payload.predicted_price)
#     metrics.update(rr_metrics)
#     if rr_metrics["rr"] < RR_MIN:
#         reasons.append(f"R/R {rr_metrics['rr']:.2f} < {RR_MIN}")
#         accept, action = False, "HOLD"

#     # final decision
#     if not reasons:
#         reasons.append("all checks passed")

#     return RiskFilterDecision(accept, action, reasons, metrics)


# backend/agents/riskFilterAgent.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional
import math

# ---- config thresholds ----
CONFIDENCE_MIN = 0.60
VOLATILITY_MAX = 0.05        # 5% daily std dev
STOP_LOSS_PCT  = 0.03        # 3% per trade
RR_MIN         = 1.5
NEWS_NEG_CUTOFF = -0.50
ALLOW_BUY_ON_NEG_NEWS = False


@dataclass
class RiskFilterInput:
    ticker: str
    signal: str               # BUY | SELL | HOLD
    confidence: float
    sources: Dict[str, float]
    current_price: float
    predicted_price: float
    # past_prices: Optional[List[float]] = None


@dataclass
class RiskFilterDecision:
    decision: str             # APPROVED | REJECTED | UNDER REVIEW
    action: str
    reasons: List[str]
    metrics: Dict[str, float]
    message: str


def _calc_volatility(past_prices: List[float]) -> Optional[float]:
    if not past_prices or len(past_prices) < 2:
        return None
    returns = []
    for i in range(1, len(past_prices)):
        if past_prices[i-1] == 0:
            continue
        returns.append((past_prices[i] - past_prices[i-1]) / past_prices[i-1])
    if not returns:
        return None
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1) if len(returns) > 1 else 0.0
    return math.sqrt(var)


def _reward_risk(curr: float, pred: float) -> Dict[str, float]:
    risk = abs(curr * STOP_LOSS_PCT)
    reward = abs(pred - curr)
    rr = (reward / risk) if risk > 0 else 0.0
    return {"risk": risk, "reward": reward, "rr": rr}


def run_risk_filter(payload: RiskFilterInput) -> RiskFilterDecision:
    reasons, metrics = [], {}
    action = payload.signal
    decision = "APPROVED"   # default

    # 1) confidence
    metrics["confidence"] = payload.confidence
    if payload.confidence < CONFIDENCE_MIN:
        reasons.append(f"confidence {payload.confidence:.2f} < {CONFIDENCE_MIN}")
        decision, action = "REJECTED", "HOLD"
        if payload.confidence >= CONFIDENCE_MIN - 0.05:  # borderline case
            decision = "UNDER REVIEW"

    # 2) news impact
    news_score = float(payload.sources.get("news_score", 0.0))
    metrics["news_score"] = news_score
    if news_score <= NEWS_NEG_CUTOFF and payload.signal == "BUY":
        if not ALLOW_BUY_ON_NEG_NEWS:
            reasons.append(f"negative news_score {news_score:.2f} ≤ {NEWS_NEG_CUTOFF}")
            decision, action = "REJECTED", "HOLD"

    # 3) volatility
    vol = _calc_volatility(payload.past_prices) if payload.past_prices else None
    if vol is not None:
        metrics["volatility"] = vol
        if vol > VOLATILITY_MAX:
            reasons.append(f"volatility {vol:.3f} > {VOLATILITY_MAX:.3f}")
            decision, action = "REJECTED", "HOLD"

    # 4) reward:risk
    rr_metrics = _reward_risk(payload.current_price, payload.predicted_price)
    metrics.update(rr_metrics)
    if rr_metrics["rr"] < RR_MIN:
        reasons.append(f"R/R {rr_metrics['rr']:.2f} < {RR_MIN}")
        decision, action = "REJECTED", "HOLD"

    # final reasons
    if not reasons:
        reasons.append("all checks passed")

    # --- human explanation ---
    if decision == "APPROVED":
        message = "✅ This trade looks good. The prediction is strong, news sentiment is supportive, and the risk/reward ratio is favorable."
    elif decision == "UNDER REVIEW":
        message = "⚠️ This trade is borderline. Some signals are weak, proceed with caution."
    else:
        parts = []
        if payload.confidence < CONFIDENCE_MIN:
            parts.append("the prediction is weak")
        if news_score <= NEWS_NEG_CUTOFF:
            parts.append("news is negative")
        if vol is not None and vol > VOLATILITY_MAX:
            parts.append("volatility is too high")
        if rr_metrics["rr"] < RR_MIN:
            parts.append("the potential loss is bigger than the potential gain")

        message = "❌ Don’t take this trade right now. " + ", ".join(parts) + "."

    return RiskFilterDecision(decision, action, reasons, metrics, message)
