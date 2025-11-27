import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

def get_ai_price_prediction(symbol):
    """
    Trains a quick Random Forest model on the stock's recent history 
    to predict the price trend for the next 5 days.
    Returns: Dictionary with 'predicted_price', 'direction', 'confidence'
    """
    try:
        # 1. Fetch Data (2 years for training)
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2y", interval="1d")
        
        if len(df) < 100:
            return None
            
        df.columns = [c.lower() for c in df.columns]
        
        # 2. Feature Engineering
        # We use technical indicators as features
        df['rsi'] = ta.rsi(df['close'], length=14)
        df['ema_20'] = ta.ema(df['close'], length=20)
        df['ema_50'] = ta.ema(df['close'], length=50)
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        
        # Lagged Returns (Momentum)
        df['return_1d'] = df['close'].pct_change(1)
        df['return_5d'] = df['close'].pct_change(5)
        
        # Target: Future Price (Average of next 5 days)
        df['target'] = df['close'].rolling(window=5).mean().shift(-5)
        
        # Drop NaNs
        df.dropna(inplace=True)
        
        if df.empty:
            return None
            
        # Select Features
        features = ['close', 'rsi', 'ema_20', 'ema_50', 'atr', 'return_1d', 'return_5d']
        X = df[features]
        y = df['target']
        
        # 3. Train Model (Random Forest)
        # We don't need a massive grid search, just a robust estimator
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X, y)
        
        # 4. Predict for "Tomorrow" (using the latest data point)
        # We need the *actual* latest data which might have been dropped due to shift(-5)
        # So we re-fetch or use the tail of the original df before dropna, 
        # but simpler is to just use the last row of X if it represents "today".
        # Actually, X's last row is 5 days ago because of shift(-5).
        # We need to construct the feature vector for the *current* active day.
        
        # Re-calculate features for the very last available candle
        last_row = ticker.history(period="3mo", interval="1d").tail(60) # Fetch enough for indicators
        last_row.columns = [c.lower() for c in last_row.columns]
        
        last_row['rsi'] = ta.rsi(last_row['close'], length=14)
        last_row['ema_20'] = ta.ema(last_row['close'], length=20)
        last_row['ema_50'] = ta.ema(last_row['close'], length=50)
        last_row['atr'] = ta.atr(last_row['high'], last_row['low'], last_row['close'], length=14)
        last_row['return_1d'] = last_row['close'].pct_change(1)
        last_row['return_5d'] = last_row['close'].pct_change(5)
        
        current_features = last_row.iloc[-1][features].values.reshape(1, -1)
        current_price = last_row.iloc[-1]['close']
        
        prediction = model.predict(current_features)[0]
        
        # 5. Interpret Result
        change_pct = ((prediction - current_price) / current_price) * 100
        
        direction = "Neutral"
        if change_pct > 1.5:
            direction = "Bullish"
        elif change_pct < -1.5:
            direction = "Bearish"
            
        # Confidence (heuristic based on tree variance or simple R^2 proxy)
        # For simplicity, we'll use the model's score on the training set as a proxy for "fit quality"
        confidence = model.score(X, y) * 100 # R-squared
        confidence = max(0, min(99, confidence)) # Clip 0-99
        
        return {
            'current_price': current_price,
            'predicted_price': prediction,
            'change_pct': change_pct,
            'direction': direction,
            'confidence': confidence
        }
        
    except Exception as e:
        print(f"AI Error: {e}")
        return None
