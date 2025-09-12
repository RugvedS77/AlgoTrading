# from datetime import datetime, timezone

# class SignalAgent:
#     def __init__(self, trend_weight=0.5, news_weight=0.1, price_weight=0.3, movement_weight=0.1,
#                  buy_threshold=0.5, sell_threshold=-0.5):
#         self.trend_weight = trend_weight
#         self.news_weight = news_weight
#         self.price_weight = price_weight
#         self.movement_weight = movement_weight
#         self.buy_threshold = buy_threshold
#         self.sell_threshold = sell_threshold

#     def generate_signal(self, ticker, trend_score, news_score, current_price, predicted_price, movement, pred_time):
#         """
#         trend_score: float (-1 to 1)
#         news_score: float (-1 to 1)
#         current_price: float
#         predicted_price: float
#         movement: str ("UP", "FLAT", "DOWN")
#         """

#         # Price factor
#         price_diff = (predicted_price - current_price) / current_price

#         # Trend movement factor
#         movement_map = {"UP": 1, "FLAT": 0, "DOWN": -1}
#         movement_score = movement_map.get(movement.upper(), 0)

#         # Combined weighted score
#         combined_score = (
#             (self.trend_weight * trend_score) +
#             (self.news_weight * news_score) +
#             (self.price_weight * price_diff) +
#             (self.movement_weight * movement_score)
#         )

#         # Decide action
#         if combined_score >= self.buy_threshold:
#             signal = "BUY"
#         elif combined_score <= self.sell_threshold:
#             signal = "SELL"
#         else:
#             signal = "HOLD"

#         # Confidence = mix of score & price gap
#         confidence = round(min(1.0, abs(combined_score) + abs(price_diff)), 3)

#         return {
#             "ticker": ticker,
#             "signal": signal,
#             "confidence": confidence,
#             "sources": {
#                 "trend_score": trend_score,
#                 "news_score": news_score,
#                 "price_diff": round(price_diff, 3),
#                 "movement": movement
#             },
#             "current_price": current_price,
#             "predicted_price": predicted_price,
#             "prediction_for": pred_time,
#             "timestamp": datetime.now(timezone.utc).isoformat()
#         }


from datetime import datetime, timezone
import numpy as np

class SignalAgent:
    def __init__(self, trend_weight=0.5, news_weight=0.1, price_weight=0.3, movement_weight=0.1,
                 buy_threshold=0.6, sell_threshold=-0.3):
        self.trend_weight = trend_weight
        self.news_weight = news_weight
        self.price_weight = price_weight
        self.movement_weight = movement_weight
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def generate_signal(self, ticker, trend_prob, news_score, current_price, predicted_price, movement, pred_time, sim_date, volatility=0.0):
        # Convert trend_prob (0-1) → trend_score (-1 to 1)
        trend_score = (trend_prob * 2) - 1  

        # Price factor
        price_diff = (predicted_price - current_price) / current_price

        # Trend movement factor
        movement_map = {"UP": 1, "FLAT": 0, "DOWN": -1}
        movement_score = movement_map.get(movement.upper(), 0)

        # Weighted sum
        combined_score = (
            (self.trend_weight * trend_score) +
            (self.news_weight * news_score) +
            (self.price_weight * price_diff) +
            (self.movement_weight * movement_score)
        )

        # Volatility penalty (lower score in choppy markets)
        risk_factor = 1 / (1 + volatility)
        combined_score *= risk_factor

        # Decide action
        if combined_score >= self.buy_threshold:
            signal = "BUY"
        elif combined_score <= self.sell_threshold:
            signal = "SELL"
        else:
            signal = "HOLD"

        # Confidence: nonlinear + agreement boost
        agreement = np.sign(trend_score) == np.sign(price_diff)
        confidence = float(np.tanh(abs(combined_score) * (1.2 if agreement else 0.8)))

        return {
            "ticker": ticker,
            "signal": signal,
            "confidence": round(confidence, 3),
            "combined_score": round(combined_score, 3),
            "sources": {
                "trend_prob": round(trend_prob, 3),
                "trend_score": round(trend_score, 3),
                "news_score": news_score,
                "price_diff": round(price_diff, 3),
                "movement": movement,
                "volatility": round(volatility, 3)
            },
            "current_price": current_price,
            "predicted_price": predicted_price,
            "prediction_for": pred_time,
            "simulation_date": sim_date,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
