import pandas as pd
import numpy as np
import os
import tensorflow as tf
import xgboost as xgb
import pickle
import time
from tensorflow.keras.models import load_model
import warnings

from models.trend_predict_model import TrendPredict 
import json
from database.redisClient import redis_client

warnings.filterwarnings("ignore")
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

DATA_FILE = 'Pred_models/TATAMOTORS_minute.csv'

class TrendPredict:
    def __init__(self):
        self.LSTM_MODEL_PATH = 'Pred_models/lstm_feature_extractor_tata_motors.h5'
        self.XGB_MODEL_PATH = 'Pred_models/xgb_classifier_tata_motors.json'
        self.SCALER_PATH = 'Pred_models/scaler_tata_motors.pkl'
        # Features used for training (must be consistent)
        self.FEATURES = ["open", "high", "low", "close", "volume", "EMA_10", "EMA_30",
                         "Boll_Upper", "Boll_Lower", "RSI", "ATR", "ADX"]
        self.TIME_STEPS = 60

    def save_to_redis(self, symbol, timestamp, prediction):
        key = f"predictions:{symbol}"
        # Ensure timestamp is string
        prediction["timestamp"] = timestamp.isoformat()
        redis_client.hset(key, timestamp.isoformat(), json.dumps(prediction))

    # ------------------- Feature Engineering Function -------------------
    # This function must be identical to the one used for training
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
        avg_gain = pd.Series(gain, index=df_feat.index).rolling(14).mean()
        avg_loss = pd.Series(loss, index=df_feat.index).rolling(14).mean()
        rs = avg_gain / (avg_loss + 1e-9)
        df_feat["RSI"] = 100 - (100 / (1 + rs))
        high_low = df_feat["high"] - df_feat["low"]
        high_close = np.abs(df_feat["high"] - df_feat["close"].shift(1))
        low_close = np.abs(df_feat["low"] - df_feat["close"].shift(1))
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df_feat["ATR"] = tr.rolling(14).mean()
        plus_dm = df_feat["high"].diff()
        minus_dm = df_feat["low"].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        tr14 = tr.rolling(14).sum()
        plus_di = 100 * (plus_dm.ewm(alpha=1/14).mean() / tr14)
        minus_di = 100 * (abs(minus_dm.ewm(alpha=1/14).mean()) / tr14)
        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
        df_feat["ADX"] = dx.ewm(alpha=1/14).mean()
        return df_feat

    # ------------------- Prediction Pipeline -------------------
    def predict_next_candle(self, latest_data_df, lstm_model, xgb_model, scaler):
        """
        Predicts the next candle's price and trend using the loaded models.
        """
        # Calculate indicators on the new data
        data_with_features = self.add_features(latest_data_df)
        
        # Get the last 60-minute sequence for prediction
        last_sequence_unscaled = data_with_features[self.FEATURES].iloc[-self.TIME_STEPS:]
        
        if len(last_sequence_unscaled) < self.TIME_STEPS or last_sequence_unscaled.isnull().values.any():
            # Not enough data or indicators are still NaN
            return None, None

        # Scaling
        last_sequence_scaled = scaler.transform(last_sequence_unscaled)
        X_pred = np.reshape(last_sequence_scaled, (1, self.TIME_STEPS, len(self.FEATURES)))

        # LSTM Prediction
        predicted_return = lstm_model.predict(X_pred, verbose=0)[0][0]
        
        # Prepare Data for XGBoost
        xgb_input = np.append(last_sequence_unscaled.iloc[-1].values, predicted_return)
        xgb_input = np.reshape(xgb_input, (1, -1))

        # XGBoost Prediction
        trend_prediction_code = xgb_model.predict(xgb_input)[0]
        predicted_trend = "Up" if trend_prediction_code == 1 else "Down"

        # Calculate Predicted Price
        last_close_price = last_sequence_unscaled['close'].iloc[-1]
        predicted_price = last_close_price * (1 + predicted_return)

        return predicted_trend, predicted_price

    # ------------------- Live Simulation -------------------
    def run_simulation(self):
        print("--- Starting Live Prediction Simulation ---")
        print(os.getcwd())
        print(os.listdir('.'))
        # 1. Load Models and Scaler
        try:
            print("Loading models and scaler...")
            lstm_model = load_model(self.LSTM_MODEL_PATH, compile=False)
            xgb_model = xgb.XGBClassifier()
            xgb_model.load_model(self.XGB_MODEL_PATH)
            with open(self.SCALER_PATH, 'rb') as f:
                scaler = pickle.load(f)
            print("Models and scaler loaded successfully.")
        except Exception as e:
            print(f"Error loading assets: {e}")
            return

        # 2. Load and prepare simulation data
        try:
            print(f"Loading simulation data from {DATA_FILE}...")
            full_df = pd.read_csv(DATA_FILE, parse_dates=["date"])
            full_df.set_index('date', inplace=True)
        except FileNotFoundError:
            print(f"Error: Data file '{DATA_FILE}' not found.")
            return

        # Filter for the specific day to simulate
        simulation_day = full_df[full_df.index.date == pd.to_datetime("2025-07-21").date()]
        if simulation_day.empty:
            print("Error: No data available for 2025-07-21 in the dataset.")
            return
            
        print(f"Simulating trading day for 2025-07-21, with {len(simulation_day)} minutes of data.")
        
        # We need at least 40 rows of prior data to calculate indicators for the first minute of the day
        history_needed = 100 
        day_start_index = full_df.index.get_loc(simulation_day.index[0])
        historical_data = full_df.iloc[day_start_index - history_needed : day_start_index]
        
        live_data_buffer = historical_data.copy()
        all_predictions = []

        # 3. Iterate through the day, minute by minute
        for current_timestamp, new_candle in simulation_day.iterrows():
            # Add the new candle to our buffer
            live_data_buffer = pd.concat([live_data_buffer, new_candle.to_frame().T])
            
            # Keep the buffer from growing indefinitely
            if len(live_data_buffer) > history_needed + 5: # Keep some extra history
                live_data_buffer = live_data_buffer.iloc[-history_needed:]

            print(f"\n--- {current_timestamp} ---")
            print(f"New Candle Received: Open={new_candle['open']:.2f}, Close={new_candle['close']:.2f}")

            # Make a prediction for the *next* candle
            trend, price = self.predict_next_candle(live_data_buffer.copy(), lstm_model, xgb_model, scaler)

            if trend and price:
                next_minute = current_timestamp + pd.Timedelta(minutes=1)
                print(f"PREDICTION FOR {next_minute.time()}:")
                print(f"  -> Predicted Trend: {trend}")
                print(f"  -> Predicted Price: {price:.2f}")

                response ={
                    "symbol": "TATAMOTORS",
                    "timestamp": next_minute.time(),
                    "predicted_trend": trend,
                    "predicted_price": round(price, 2),
                    "current_price": round(new_candle['close'], 2)
                }
                
                self.save_to_redis("TATAMOTORS", next_minute, response)
                all_predictions.append((next_minute, response))
                
            else:
                print("Collecting more data before making predictions...")


            SIMULATION_SPEED = 12   # 1 real second = 12 market seconds → ~5s per market minute
            time.sleep(60 / SIMULATION_SPEED)
            # time.sleep(1)

        print("\n--- Simulation Complete ---")

if __name__ == "__main__":
    tp = TrendPredict()
    tp.run_simulation()
