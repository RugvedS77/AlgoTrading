# In agents/signal_agent.py

from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Literal
import numpy as np

class SignalAgent:
    """
    A sophisticated, regime-aware signal agent that adjusts its strategy
    based on market volatility and trend conditions.
    """
    def __init__(self):
        self.regime_configs = {
            "VOLATILE_TRENDING": {"weights": {"trend": 0.6, "news": 0.1, "price": 0.3}, "thresholds": {"buy": 0.7, "sell": -0.7}},
            "QUIET_TRENDING": {"weights": {"trend": 0.5, "news": 0.15, "price": 0.35}, "thresholds": {"buy": 0.5, "sell": -0.5}},
            "VOLATILE_RANGING": {"weights": {"trend": 0.2, "news": 0.2, "price": 0.6}, "thresholds": {"buy": 0.8, "sell": -0.8}},
            "QUIET_RANGING": {"weights": {"trend": 0.3, "news": 0.2, "price": 0.5}, "thresholds": {"buy": 0.6, "sell": -0.6}}
        }

    def _get_market_regime(self, atr: float, price: float, ma_short: float, ma_long: float) -> Tuple[str, str]:
        volatility_threshold = price * 0.01
        volatility = "VOLATILE" if atr > volatility_threshold else "QUIET"
        trend = "TRENDING" if (price > ma_short > ma_long) or (price < ma_short < ma_long) else "RANGING"
        return volatility, trend

    def generate_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a trading signal based on a dynamic, regime-aware analysis."""
        
        # --- 1. Determine Market Regime ---
        volatility_state, trend_state = self._get_market_regime(
            atr=signal_data["atr"],
            price=signal_data["current_price"],
            ma_short=signal_data["ma_short"],
            ma_long=signal_data["ma_long"],
        )
        regime = f"{volatility_state}_{trend_state}"
        config = self.regime_configs.get(regime, self.regime_configs["QUIET_RANGING"])

        # --- 2. Calculate Component Scores ---
        trend_score = (signal_data["trend_prob"] * 2) - 1
        price_diff = (signal_data["predicted_price"] - signal_data["current_price"]) / signal_data["current_price"] if signal_data["current_price"] != 0 else 0
        
        # --- 3. Calculate Weighted Combined Score ---
        weights = config["weights"]
        combined_score = (
            (weights["trend"] * trend_score) +
            (weights["news"] * signal_data["news_score"]) +
            (weights["price"] * price_diff)
        )

        # --- 4. Determine Signal based on Dynamic Thresholds ---
        thresholds = config["thresholds"]
        signal = "HOLD"
        if combined_score >= thresholds["buy"]:
            signal = "BUY"
        elif combined_score <= thresholds["sell"]:
            signal = "SELL"

        # --- 5. Calculate Confidence ---
        is_aligned = (signal == "BUY" and trend_state == "TRENDING" and trend_score > 0) or \
                     (signal == "SELL" and trend_state == "TRENDING" and trend_score < 0)
        confidence_multiplier = 1.2 if is_aligned else 0.8
        confidence = float(np.tanh(abs(combined_score) * confidence_multiplier))
        
        # Final output dictionary, including ATR for the Capital Allocator
        return {
            "ticker": signal_data["ticker"],
            "signal": signal,
            "confidence": round(confidence, 4),
            "combined_score": round(combined_score, 4),
            "sources": {
                "trend_prob": round(signal_data["trend_prob"], 4),
                "news_score": round(signal_data["news_score"], 4),
                "price_diff": round(price_diff, 4),
                "movement": signal_data["movement"],
                "market_regime": regime,
                "ATR": round(signal_data["atr"], 4)
            },
            "current_price": signal_data["current_price"],
            "predicted_price": signal_data["predicted_price"],
            "pred_for": signal_data["pred_for"],
            "simulation_date": signal_data["sim_date"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# from datetime import datetime, timezone
# import numpy as np

# class SignalAgent:
#     def __init__(self, trend_weight=0.5, news_weight=0.1, price_weight=0.3, movement_weight=0.1,
#                  buy_threshold=0.6, sell_threshold=-0.3):
#         self.trend_weight = trend_weight
#         self.news_weight = news_weight
#         self.price_weight = price_weight
#         self.movement_weight = movement_weight
#         self.buy_threshold = buy_threshold
#         self.sell_threshold = sell_threshold

#     def generate_signal(self, ticker, trend_prob, news_score, current_price, predicted_price, movement, pred_time, sim_date, volatility=0.0):
#         # Convert trend_prob (0-1) → trend_score (-1 to 1)
#         trend_score = (trend_prob * 2) - 1  

#         # Price factor
#         price_diff = (predicted_price - current_price) / current_price

#         # Trend movement factor
#         movement_map = {"UP": 1, "FLAT": 0, "DOWN": -1}
#         movement_score = movement_map.get(movement.upper(), 0)

#         # Weighted sum
#         combined_score = (
#             (self.trend_weight * trend_score) +
#             (self.news_weight * news_score) +
#             (self.price_weight * price_diff) +
#             (self.movement_weight * movement_score)
#         )

#         # Volatility penalty (lower score in choppy markets)
#         risk_factor = 1 / (1 + volatility)
#         combined_score *= risk_factor

#         # Decide action
#         if combined_score >= self.buy_threshold:
#             signal = "BUY"
#         elif combined_score <= self.sell_threshold:
#             signal = "SELL"
#         else:
#             signal = "HOLD"

#         # Confidence: nonlinear + agreement boost
#         agreement = np.sign(trend_score) == np.sign(price_diff)
#         confidence = float(np.tanh(abs(combined_score) * (1.2 if agreement else 0.8)))

#         return {
#             "ticker": ticker,
#             "signal": signal,
#             "confidence": round(confidence, 3),
#             "combined_score": round(combined_score, 3),
#             "sources": {
#                 "trend_prob": round(trend_prob, 3),
#                 "trend_score": round(trend_score, 3),
#                 "news_score": news_score,
#                 "price_diff": round(price_diff, 3),
#                 "movement": movement,
#                 "volatility": round(volatility, 3)
#             },
#             "current_price": current_price,
#             "predicted_price": predicted_price,
#             "prediction_for": pred_time,
#             "simulation_date": sim_date,
#             "timestamp": datetime.now(timezone.utc).isoformat()
#         }
