# import pandas as pd
# import numpy as np
# import os
# import tensorflow as tf
# import pickle
# import time
# from tensorflow.keras.models import load_model
# import warnings

# from models.trend_predict_model import TrendPredict 
# import json
# from database.redisClient import redis_client
# from datetime import datetime

# warnings.filterwarnings("ignore")

# DATA_FILE = 'Pred_models/TATAMOTORS_minute.csv'

# class TrendPredict:
#     def __init__(self):
#         self.PRICE_LSTM_MODEL_PATH = 'Pred_models/lstm_feature_extractor_5min.h5'# --- Models for Price Prediction ---
#         self.PRICE_SCALER_PATH = 'Pred_models/scaler_5min.pkl'

#         self.TREND_MODEL_PATH = 'Pred_models/directional_model.h5'# --- Models for Trend Prediction ---
#         self.TREND_SCALER_PATH = 'Pred_models/scalers.pkl'

#         self.TARGET_DAY = '2025-07-21' # The day you want to simulate
#         self.TIME_STEPS = 60 # Sequence length for models
#         self.SCALE_FACTOR = 1000 # Must match the factor used during price model training
#         self.PRICE_FEATURES = ["open", "high", "low", "close", "volume", "EMA_10", "EMA_30",
#                   "Boll_Upper", "Boll_Lower", "RSI", "ATR", "ADX"]
        
#     def save_prediction(self, ticker: str, result: dict):
#         redis_key = f"predictions:{ticker}"

#         # Use simulation_date + prediction_for as unique field
#         field_key = f"{result['simulation_date']} {result['prediction_for']}"  

#         print(f"DEBUG: Saving {field_key} -> {result}")  
#         # Save to hash (all historical predictions)
#         redis_client.hset(redis_key, field_key, json.dumps(result))

#         # Save to "latest" key (always overwrite with most recent simulation timestamp)
#         latest_key = f"{redis_key}:latest"
#         redis_client.set(latest_key, json.dumps(result))

#         print(f"✅ Saved prediction for {field_key} -> {ticker}")

#     # ------------------- Feature Engineering Function (Advanced Version) -------------------
#     # This combined function includes all indicators needed for both models.
#     def add_features(self, df):
#         """Adds technical indicators and time features to the dataframe."""
#         df_feat = df.copy()
#         # Indicators from original script
#         df_feat["EMA_10"] = df_feat["close"].ewm(span=10, adjust=False).mean()
#         df_feat["EMA_30"] = df_feat["close"].ewm(span=30, adjust=False).mean()
#         rolling_mean = df_feat["close"].rolling(window=20).mean()
#         rolling_std = df_feat["close"].rolling(window=20).std()
#         df_feat["Boll_Upper"] = rolling_mean + (rolling_std * 2)
#         df_feat["Boll_Lower"] = rolling_mean - (rolling_std * 2)
#         delta = df_feat["close"].diff()
#         gain = delta.where(delta > 0, 0)
#         loss = -delta.where(delta < 0, 0)
#         # Using rolling mean for RSI as in the trend script
#         rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
#         df_feat["RSI"] = 100 - (100 / (1 + rs))
#         high_low = df_feat["high"] - df_feat["low"]
#         high_close = (df_feat["high"] - df_feat["close"].shift(1)).abs()
#         low_close = (df_feat["low"] - df_feat["close"].shift(1)).abs()
#         tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
#         df_feat["ATR"] = tr.rolling(14).mean()
#         plus_dm = df_feat["high"].diff(); plus_dm[plus_dm < 0] = 0
#         minus_dm = -df_feat["low"].diff(); minus_dm[minus_dm < 0] = 0
#         tr14 = tr.rolling(14).sum()
#         plus_di = 100 * (plus_dm.ewm(alpha=1/14).mean() / (tr14 + 1e-9))
#         minus_di = 100 * (minus_dm.ewm(alpha=1/14).mean() / (tr14 + 1e-9))
#         dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
#         df_feat["ADX"] = dx.ewm(alpha=1/14).mean()
        
#         # Additional indicators from trend script
#         ema_12 = df_feat['close'].ewm(span=12, adjust=False).mean()
#         ema_26 = df_feat['close'].ewm(span=26, adjust=False).mean()
#         df_feat['MACD'] = ema_12 - ema_26
#         df_feat['MACD_Signal'] = df_feat['MACD'].ewm(span=9, adjust=False).mean()
#         df_feat['volatility'] = df_feat['close'].pct_change().rolling(window=20).std()
#         df_feat['RSI_change'] = df_feat['RSI'].diff(5)
#         df_feat['hour_of_day'] = df_feat.index.hour
#         df_feat['day_of_week'] = df_feat.index.dayofweek
#         return df_feat.dropna()


#     # ------------------- Combined Prediction Pipeline -------------------
#     def get_combined_prediction(self, window_df, models, scalers, trend_features):
#         """
#         Generates predictions from both the price model and the trend model.
#         """
#         PRICE_FEATURES = self.PRICE_FEATURES
#         TIME_STEPS = self.TIME_STEPS
#         SCALE_FACTOR = self.SCALE_FACTOR

#         # --- Price Prediction ---
#         price_lstm_model = models['price_lstm']
#         price_scaler = scalers['price']

#         # 1. Prepare data for Price LSTM
#         price_features_unscaled = window_df[PRICE_FEATURES]
#         price_features_scaled = price_scaler.transform(price_features_unscaled)
#         X_pred_lstm = np.reshape(price_features_scaled, (1, TIME_STEPS, len(PRICE_FEATURES)))
        
#         # 2. Get LSTM's scaled prediction
#         scaled_price_pred = price_lstm_model.predict(X_pred_lstm, verbose=0)[0][0]
        
#         # 3. De-scale to get predicted price
#         predicted_return = scaled_price_pred / SCALE_FACTOR
#         last_close_price = price_features_unscaled['close'].iloc[-1]
#         predicted_price = last_close_price * (1 + predicted_return)
        
#         # --- Trend Model Prediction ---
#         trend_model = models['trend']
#         trend_scaler = scalers['trend']

#         # 1. Prepare data for Trend Model
#         trend_features_unscaled = window_df[trend_features]
#         trend_features_scaled = trend_scaler.transform(trend_features_unscaled)
#         X_pred_trend = np.expand_dims(trend_features_scaled, axis=0)
        
#         # 2. Get Trend prediction
#         trend_prob = trend_model.predict(X_pred_trend, verbose=0)[0][0]
#         trend_direction = "UP" if trend_prob > 0.5 else "DOWN"

#         return predicted_price, trend_direction, trend_prob

#     # ------------------- Live Simulation -------------------
#     def run_simulation(self):
#         print("--- Starting Combined 5-Minute Live Prediction Simulation ---")
#         PRICE_LSTM_MODEL_PATH = self.PRICE_LSTM_MODEL_PATH
#         PRICE_SCALER_PATH = self.PRICE_SCALER_PATH
#         TREND_MODEL_PATH = self.TREND_MODEL_PATH
#         TREND_SCALER_PATH = self.TREND_SCALER_PATH
#         TARGET_DAY = self.TARGET_DAY
#         TIME_STEPS = self.TIME_STEPS
#         # 1. Load All Models and Scalers
#         try:
#             print("Loading all models and scalers...")
#             models = {
#                 'price_lstm': load_model(PRICE_LSTM_MODEL_PATH, compile=False),
#                 'trend': load_model(TREND_MODEL_PATH)
#             }

#             with open(PRICE_SCALER_PATH, 'rb') as f:
#                 price_scaler = pickle.load(f)
                
#             with open(TREND_SCALER_PATH, 'rb') as f:
#                 trend_data = pickle.load(f)
#                 trend_scaler = trend_data['scaler_X']
#                 trend_features = trend_data['features']

#             scalers = {'price': price_scaler, 'trend': trend_scaler}
#             print("All assets loaded successfully.")
#         except Exception as e:
#             print(f"Error loading assets: {e}")
#             return

#         # 2. Load and Prepare Full Dataset (Efficient Method)
#         try:
#             print(f"Loading and preparing all historical data from {DATA_FILE}...")
#             full_df_1min = pd.read_csv(DATA_FILE, parse_dates=["date"], index_col="date")
            
#             # Resample to 5 minutes
#             full_df_5min = full_df_1min.resample('5T').agg({
#                 'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
#             }).dropna()

#             # Calculate features on the entire dataset ONCE
#             df_featured_full = self.add_features(full_df_5min)
#             print("Feature calculation complete.")

#         except FileNotFoundError:
#             print(f"Error: Data file '{DATA_FILE}' not found.")
#             return

#         # 3. Filter for the simulation day
#         simulation_day = df_featured_full[df_featured_full.index.date == pd.to_datetime(TARGET_DAY).date()]
#         if simulation_day.empty:
#             print(f"Error: No data available for {TARGET_DAY} after feature calculation.")
#             return
            
#         print(f"\n--- Simulating trading day for {TARGET_DAY} ---")
        
#         # 4. Iterate through the day's candles
#         for current_timestamp in simulation_day.index:
#             # Find the index location of the current candle in the full dataframe
#             end_idx_loc = df_featured_full.index.get_loc(current_timestamp)
#             start_idx_loc = end_idx_loc - TIME_STEPS + 1
            
#             if start_idx_loc < 0:
#                 print(f"[{current_timestamp.time()}] Collecting more historical data...")
#                 continue
            
#             # Slice the pre-calculated historical window
#             historical_window = df_featured_full.iloc[start_idx_loc : end_idx_loc + 1]
            
#             if len(historical_window) < TIME_STEPS:
#                 continue

#             if start_idx_loc < 0 or len(historical_window) < TIME_STEPS:
#                 result = {
#                     "ticker": "TATAMOTORS",
#                     "current_price": float(full_df_5min.loc[current_timestamp]["close"]),
#                     "predicted_price": None,
#                     "trend": "N/A",
#                     "confidence": 0.0,
#                     "prediction_for": str(current_timestamp.time()),
#                     "timestamp": datetime.utcnow().isoformat(),
#                     "simulation_date": str(current_timestamp.date())
#                 }
#                 self.save_prediction("TATAMOTORS", result)
#                 continue

#             # --- Make a combined prediction for the *next* 5-minute candle ---
#             price, trend_dir, trend_conf = self.get_combined_prediction(
#                 historical_window, models, scalers, trend_features
#             )

#             current_price = historical_window.iloc[-1]['close']
#             next_interval_start = current_timestamp + pd.Timedelta(minutes=5)
            
#             print(f"\n--- Candle Closed at {current_timestamp.time()} (Price: {current_price:.2f}) ---")
#             print(f"PREDICTION FOR NEXT 5-MIN CANDLE ({next_interval_start.time()}):")
#             print(f"  -> Price Model (LSTM): Predicted Close Price: {price:.2f}")
#             print(f"  -> Trend Model (LSTM): Predicted Direction: {trend_dir} (Confidence: {trend_conf:.2f})")
#                         # --- NEW: Save prediction to Redis ---
#             result = {
#                 "ticker": "TATAMOTORS",
#                 "current_price": float(current_price),
#                 "predicted_price": price,
#                 "trend": trend_dir,
#                 "confidence": float(trend_conf),

#                 # this is the candle you are predicting (from dataset)
#                 "prediction_for": str(next_interval_start.time()),  

#                 # this is when your backend actually ran the prediction
#                 "timestamp": datetime.utcnow().isoformat(),          

#                 # extra field: which day in dataset the simulation belongs to
#                 "simulation_date": str(current_timestamp.date())     
#             }


#             # redis_key = f"predictions:TATAMOTORS"
#             # redis_client.hset(redis_key, str(next_interval_start.time()), json.dumps(result))
#             # redis_client.set(f"{redis_key}:latest", json.dumps(result))
#             # print("new prediction saved to Redis.")

#             self.save_prediction("TATAMOTORS", result)

#             time.sleep(300)

#         print("\n--- Simulation Complete ---")

# # if __name__ == "__main__":
# #     run_simulation()


import pandas as pd
import numpy as np
import os
import tensorflow as tf
import pickle
import time
from tensorflow.keras.models import load_model
import warnings

import json
from database.redisClient import redis_client
from datetime import datetime

warnings.filterwarnings("ignore")

DATA_FILE = 'Pred_models/TATAMOTORS_minute.csv'


class TrendPredict:
    def __init__(self):
        self.PRICE_LSTM_MODEL_PATH = 'Pred_models/lstm_feature_extractor_5min.h5'
        self.PRICE_SCALER_PATH = 'Pred_models/scaler_5min.pkl'
        self.TREND_MODEL_PATH = 'Pred_models/directional_model.h5'
        self.TREND_SCALER_PATH = 'Pred_models/scalers.pkl'

        self.TARGET_DAY = '2025-07-21'
        self.TIME_STEPS = 60
        self.SCALE_FACTOR = 1000
        self.PRICE_FEATURES = ["open", "high", "low", "close", "volume",
                               "EMA_10", "EMA_30", "Boll_Upper", "Boll_Lower",
                               "RSI", "ATR", "ADX"]

    def save_prediction(self, ticker: str, result: dict):
        redis_key = f"predictions:{ticker}"
        # unique field: simulation_date + prediction_for
        field_key = f"{result['simulation_date']} {result['prediction_for']}"

        # write to hash
        redis_client.hset(redis_key, field_key, json.dumps(result))

        # update :latest only if this simulated datetime is newer than stored one
        latest_key = f"{redis_key}:latest"
        try:
            existing = redis_client.get(latest_key)
            if existing:
                existing_obj = json.loads(existing)
                # combine simulation_date + prediction_for to form comparable datetime
                existing_dt = datetime.strptime(
                    f"{existing_obj['simulation_date']} {existing_obj['prediction_for']}",
                    "%Y-%m-%d %H:%M:%S"
                )
            else:
                existing_dt = None

            new_dt = datetime.strptime(f"{result['simulation_date']} {result['prediction_for']}", "%Y-%m-%d %H:%M:%S")

            if existing_dt is None or new_dt >= existing_dt:
                redis_client.set(latest_key, json.dumps(result))

        except Exception as e:
            # fallback: set latest (safe option) and log the error
            print(f"[save_prediction] Error checking latest key: {e}. Overwriting latest.")
            redis_client.set(latest_key, json.dumps(result))

        print(f"✅ Saved prediction for {field_key} -> {ticker}")

    def add_features(self, df):
        df_feat = df.copy()
        df_feat["EMA_10"] = df_feat["close"].ewm(span=10, adjust=False).mean()
        df_feat["EMA_30"] = df_feat["close"].ewm(span=30, adjust=False).mean()
        rolling_mean = df_feat["close"].rolling(window=20).mean()
        rolling_std = df_feat["close"].rolling(window=20).std()
        df_feat["Boll_Upper"] = rolling_mean + (rolling_std * 2)
        df_feat["Boll_Lower"] = rolling_mean - (rolling_std * 2)
        delta = df_feat["close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
        df_feat["RSI"] = 100 - (100 / (1 + rs))
        high_low = df_feat["high"] - df_feat["low"]
        high_close = (df_feat["high"] - df_feat["close"].shift(1)).abs()
        low_close = (df_feat["low"] - df_feat["close"].shift(1)).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df_feat["ATR"] = tr.rolling(14).mean()
        plus_dm = df_feat["high"].diff(); plus_dm[plus_dm < 0] = 0
        minus_dm = -df_feat["low"].diff(); minus_dm[minus_dm < 0] = 0
        tr14 = tr.rolling(14).sum()
        plus_di = 100 * (plus_dm.ewm(alpha=1/14).mean() / (tr14 + 1e-9))
        minus_di = 100 * (minus_dm.ewm(alpha=1/14).mean() / (tr14 + 1e-9))
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
        df_feat["ADX"] = dx.ewm(alpha=1/14).mean()

        ema_12 = df_feat['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df_feat['close'].ewm(span=26, adjust=False).mean()
        df_feat['MACD'] = ema_12 - ema_26
        df_feat['MACD_Signal'] = df_feat['MACD'].ewm(span=9, adjust=False).mean()
        df_feat['volatility'] = df_feat['close'].pct_change().rolling(window=20).std()
        df_feat['RSI_change'] = df_feat['RSI'].diff(5)
        df_feat['hour_of_day'] = df_feat.index.hour
        df_feat['day_of_week'] = df_feat.index.dayofweek
                # MODIFICATION: Add short and long-term Simple Moving Averages
        df_feat["MA_short"] = df_feat["close"].rolling(window=10).mean()
        df_feat["MA_long"] = df_feat["close"].rolling(window=50).mean()
        return df_feat.dropna()

    def get_combined_prediction(self, window_df, models, scalers, trend_features):
        PRICE_FEATURES = self.PRICE_FEATURES
        TIME_STEPS = self.TIME_STEPS
        SCALE_FACTOR = self.SCALE_FACTOR

        price_lstm_model = models['price_lstm']
        price_scaler = scalers['price']

        price_features_unscaled = window_df[PRICE_FEATURES]
        price_features_scaled = price_scaler.transform(price_features_unscaled)
        X_pred_lstm = np.reshape(price_features_scaled, (1, TIME_STEPS, len(PRICE_FEATURES)))

        scaled_price_pred = price_lstm_model.predict(X_pred_lstm, verbose=0)[0][0]

        predicted_return = scaled_price_pred / SCALE_FACTOR
        last_close_price = price_features_unscaled['close'].iloc[-1]
        predicted_price = last_close_price * (1 + predicted_return)

        trend_model = models['trend']
        trend_scaler = scalers['trend']
        trend_features_unscaled = window_df[trend_features]
        trend_features_scaled = trend_scaler.transform(trend_features_unscaled)
        X_pred_trend = np.expand_dims(trend_features_scaled, axis=0)

        trend_prob = float(trend_model.predict(X_pred_trend, verbose=0)[0][0])
        trend_direction = "UP" if trend_prob > 0.5 else "DOWN"

        return float(predicted_price), trend_direction, trend_prob

        # MODIFICATION: New method to be called by the standalone service
    def run_continuously(self, sleep_seconds: int = 300):
        """
        Runs the prediction loop continuously, simulating a live trading day.
        This is meant to be run as a standalone background service.
        """
        print("--- Initializing Continuous Mode ---")

        # --- This block is identical to the setup in run_simulation ---
        try:
            models = {
                'price_lstm': load_model(self.PRICE_LSTM_MODEL_PATH, compile=False),
                'trend': load_model(self.TREND_MODEL_PATH)
            }
            with open(self.PRICE_SCALER_PATH, 'rb') as f:
                price_scaler = pickle.load(f)
            with open(self.TREND_SCALER_PATH, 'rb') as f:
                trend_data = pickle.load(f)
                trend_scaler = trend_data['scaler_X']
                trend_features = trend_data['features']
            scalers = {'price': price_scaler, 'trend': trend_scaler}
        except Exception as e:
            print(f"[Initialization Error] Could not load models/scalers: {e}")
            return

        try:
            full_df_1min = pd.read_csv(DATA_FILE, parse_dates=["date"], index_col="date")
            full_df_5min = full_df_1min.resample('5T').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
            }).dropna()
            df_featured_full = self.add_features(full_df_5min)
        except Exception as e:
            print(f"[Data Prep Error] Could not prepare data: {e}")
            return

        simulation_day = df_featured_full[df_featured_full.index.date == pd.to_datetime(self.TARGET_DAY).date()]
        if simulation_day.empty:
            print(f"[Data Error] No data available for {self.TARGET_DAY}")
            return
        # --- End of setup block ---

        print(f"\n--- ✅ Service is LIVE. Simulating trading day for {self.TARGET_DAY} ---")
        
        # This is the main service loop
        for current_timestamp in simulation_day.index:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Processing timestamp: {current_timestamp.time()}")
            
            end_idx_loc = df_featured_full.index.get_loc(current_timestamp)
            start_idx_loc = end_idx_loc - self.TIME_STEPS + 1
            
            # Skip if there's not enough historical data
            if start_idx_loc < 0:
                print(f"[{current_timestamp.time()}] Not enough history yet; skipping.")
                time.sleep(sleep_seconds)
                continue

            historical_window = df_featured_full.iloc[start_idx_loc: end_idx_loc + 1]
            if len(historical_window) < self.TIME_STEPS:
                print(f"[{current_timestamp.time()}] Historical window too short; skipping.")
                time.sleep(sleep_seconds)
                continue

            # Make and save the prediction
            try:
                price, trend_dir, trend_conf = self.get_combined_prediction(
                    historical_window, models, scalers, trend_features
                )
                # Get the most recent row of data to extract features from
                latest_data = historical_window.iloc[-1]
                
                current_price = historical_window.iloc[-1]['close']
                next_interval_start = current_timestamp + pd.Timedelta(minutes=5)

                result = {
                    "ticker": "TATAMOTORS",
                    "current_price": float(current_price),
                    "predicted_price": float(price),
                    "trend": trend_dir,
                    "confidence": float(trend_conf),
                    # --- Add the new data points required by the SignalAgent ---
                    "atr": float(latest_data["ATR"]),
                    "ma_short": float(latest_data["MA_short"]),
                    "ma_long": float(latest_data["MA_long"]),

                    "prediction_for": str(next_interval_start.time()),
                    "timestamp": datetime.utcnow().isoformat(),
                    "simulation_date": str(current_timestamp.date())

                }
                self.save_prediction("TATAMOTORS", result)
                
            except Exception as e:
                print(f"[{current_timestamp.time()}] Prediction error: {e}")

            # Wait for the next interval
            print(f"🎉🎉--- Prediction saved. Waiting for {sleep_seconds} seconds... ---")
            time.sleep(sleep_seconds)
            
        print("\n--- Simulation for the day complete. Service finished. ---")



    def run_simulation(self, sleep_seconds: int = 300, save_placeholders: bool = True):
        """
        Run simulation loop.
        - sleep_seconds: how long to wait between iterations (set 0 for fast backtest)
        - save_placeholders: save entries with predicted_price=None when not enough history
        """
        print("--- Starting Combined 5-Minute Live Prediction Simulation ---")

        # load models & scalers
        try:
            models = {
                'price_lstm': load_model(self.PRICE_LSTM_MODEL_PATH, compile=False),
                'trend': load_model(self.TREND_MODEL_PATH)
            }
            with open(self.PRICE_SCALER_PATH, 'rb') as f:
                price_scaler = pickle.load(f)
            with open(self.TREND_SCALER_PATH, 'rb') as f:
                trend_data = pickle.load(f)
                trend_scaler = trend_data['scaler_X']
                trend_features = trend_data['features']
            scalers = {'price': price_scaler, 'trend': trend_scaler}
        except Exception as e:
            print(f"[run_simulation] Error loading models/scalers: {e}")
            return

        # prepare data
        try:
            full_df_1min = pd.read_csv(DATA_FILE, parse_dates=["date"], index_col="date")
            full_df_5min = full_df_1min.resample('5T').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
            }).dropna()
            df_featured_full = self.add_features(full_df_5min)
        except Exception as e:
            print(f"[run_simulation] Error preparing data: {e}")
            return

        # filter day
        simulation_day = df_featured_full[df_featured_full.index.date == pd.to_datetime(self.TARGET_DAY).date()]
        if simulation_day.empty:
            print(f"[run_simulation] Error: No data available for {self.TARGET_DAY}")
            return

        print(f"\n--- Simulating trading day for {self.TARGET_DAY} ---")

        for current_timestamp in simulation_day.index:
            end_idx_loc = df_featured_full.index.get_loc(current_timestamp)
            start_idx_loc = end_idx_loc - self.TIME_STEPS + 1

            # slice bounds check
            if start_idx_loc < 0:
                if save_placeholders:
                    # save placeholder for this time (no prediction yet)
                    placeholder = {
                        "ticker": "TATAMOTORS",
                        "current_price": float(full_df_5min.loc[current_timestamp]["close"]),
                        "predicted_price": None,
                        "trend": "N/A",
                        "confidence": 0.0,
                        "prediction_for": str(current_timestamp.time()),
                        "timestamp": datetime.utcnow().isoformat(),
                        "simulation_date": str(current_timestamp.date())
                    }
                    self.save_prediction("TATAMOTORS", placeholder)
                else:
                    print(f"[{current_timestamp.time()}] Not enough history yet; skipping.")
                if sleep_seconds:
                    time.sleep(sleep_seconds)
                continue

            historical_window = df_featured_full.iloc[start_idx_loc: end_idx_loc + 1]
            if len(historical_window) < self.TIME_STEPS:
                if save_placeholders:
                    placeholder = {
                        "ticker": "TATAMOTORS",
                        "current_price": float(full_df_5min.loc[current_timestamp]["close"]),
                        "predicted_price": None,
                        "trend": "N/A",
                        "confidence": 0.0,
                        "prediction_for": str(current_timestamp.time()),
                        "timestamp": datetime.utcnow().isoformat(),
                        "simulation_date": str(current_timestamp.date())
                    }
                    self.save_prediction("TATAMOTORS", placeholder)
                else:
                    print(f"[{current_timestamp.time()}] Historical window too short; skipping.")
                if sleep_seconds:
                    time.sleep(sleep_seconds)
                continue

            # make predictions
            try:
                price, trend_dir, trend_conf = self.get_combined_prediction(
                    historical_window, models, scalers, trend_features
                )
            except Exception as e:
                print(f"[{current_timestamp.time()}] Prediction error: {e}")
                # save placeholder to keep timeline continuity
                placeholder = {
                    "ticker": "TATAMOTORS",
                    "current_price": float(historical_window.iloc[-1]['close']),
                    "predicted_price": None,
                    "trend": "N/A",
                    "confidence": 0.0,
                    "prediction_for": str((current_timestamp + pd.Timedelta(minutes=5)).time()),
                    "timestamp": datetime.utcnow().isoformat(),
                    "simulation_date": str(current_timestamp.date())
                }
                self.save_prediction("TATAMOTORS", placeholder)
                if sleep_seconds:
                    time.sleep(sleep_seconds)
                continue

            current_price = historical_window.iloc[-1]['close']
            next_interval_start = current_timestamp + pd.Timedelta(minutes=5)

            result = {
                "ticker": "TATAMOTORS",
                "current_price": float(current_price),
                "predicted_price": float(price),
                "trend": trend_dir,
                "confidence": float(trend_conf),
                "prediction_for": str(next_interval_start.time()),
                "timestamp": datetime.utcnow().isoformat(),
                "simulation_date": str(current_timestamp.date())
            }

            self.save_prediction("TATAMOTORS", result)

            if sleep_seconds:
                time.sleep(sleep_seconds)

        print("\n--- Simulation Complete ---")
