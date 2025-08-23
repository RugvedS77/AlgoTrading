
# from datetime import datetime, timezone

# class SignalAgent:
#     def __init__(self, trend_weight=0.6, news_weight=0.4, buy_threshold=0.5, sell_threshold=-0.5):
#         self.trend_weight = trend_weight
#         self.news_weight = news_weight
#         self.buy_threshold = buy_threshold
#         self.sell_threshold = sell_threshold

#     def generate_signal(self, ticker, trend_score, news_score):
#         """
#         trend_score: float (-1 to 1) where -1 is bearish, +1 is bullish
#         news_score: float (-1 to 1) where -1 is negative, +1 is positive
#         """
#         # Weighted average
#         combined_score = (self.trend_weight * trend_score) + (self.news_weight * news_score)

#         # Determine action
#         if combined_score >= self.buy_threshold:
#             signal = "BUY"
#         elif combined_score <= self.sell_threshold:
#             signal = "SELL"
#         else:
#             signal = "HOLD"

#         # Confidence = absolute strength of combined signal
#         confidence = round(abs(combined_score), 3)

#         # Build JSON-like output
#         result = {
#             "ticker": ticker,
#             "signal": signal,
#             "confidence": confidence,
#             "sources": {
#                 "trend": trend_score,
#                 "news": news_score
#             },
#             "timestamp": datetime.now(timezone.utc).isoformat()
#         }
#         return result


from datetime import datetime, timezone

class SignalAgent:
    def __init__(self, trend_weight=0.4, news_weight=0.3, price_weight=0.2, movement_weight=0.1,
                 buy_threshold=0.5, sell_threshold=-0.5):
        self.trend_weight = trend_weight
        self.news_weight = news_weight
        self.price_weight = price_weight
        self.movement_weight = movement_weight
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def generate_signal(self, ticker, trend_score, news_score, current_price, predicted_price, movement):
        """
        trend_score: float (-1 to 1)
        news_score: float (-1 to 1)
        current_price: float
        predicted_price: float
        movement: str ("UP", "FLAT", "DOWN")
        """

        # Price factor
        price_diff = (predicted_price - current_price) / current_price

        # Trend movement factor
        movement_map = {"UP": 1, "FLAT": 0, "DOWN": -1}
        movement_score = movement_map.get(movement.upper(), 0)

        # Combined weighted score
        combined_score = (
            (self.trend_weight * trend_score) +
            (self.news_weight * news_score) +
            (self.price_weight * price_diff) +
            (self.movement_weight * movement_score)
        )

        # Decide action
        if combined_score >= self.buy_threshold:
            signal = "BUY"
        elif combined_score <= self.sell_threshold:
            signal = "SELL"
        else:
            signal = "HOLD"

        # Confidence = mix of score & price gap
        confidence = round(min(1.0, abs(combined_score) + abs(price_diff)), 3)

        return {
            "ticker": ticker,
            "signal": signal,
            "confidence": confidence,
            "sources": {
                "trend_score": trend_score,
                "news_score": news_score,
                "price_diff": round(price_diff, 3),
                "movement": movement
            },
            "current_price": current_price,
            "predicted_price": predicted_price,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
