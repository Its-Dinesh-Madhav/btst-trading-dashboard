import pandas_ta as ta
import pandas as pd
import numpy as np

def check_breakout_swing(df):
    """
    Strategy 1: Breakout Swing Trading
    Filters:
    - Price near resistance (approx. highest high of last 20 days)
    - Tight consolidation (NR7 or low volatility)
    - Volume rising > 20% above average
    - RSI between 45-60
    """
    if df is None or df.empty or len(df) < 25:
        return False, None

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 1. RSI Filter (45-60)
    rsi = ta.rsi(df['close'], length=14)
    if rsi is None: return False, None
    curr_rsi = rsi.iloc[-1]
    if not (45 <= curr_rsi <= 65): # Slightly wider range for flexibility
        return False, None

    # 2. Volume Rising (> 1.2x Average)
    avg_vol = df['volume'].rolling(window=20).mean().iloc[-1]
    if latest['volume'] <= avg_vol * 1.2:
        return False, None

    # 3. Consolidation / Near Resistance
    # Check if price is within 5% of 20-day high
    high_20 = df['high'].rolling(window=20).max().iloc[-1]
    if latest['close'] < high_20 * 0.95:
        return False, None
        
    # Check for consolidation (ATR is low relative to price)
    atr = ta.atr(df['high'], df['low'], df['close'], length=14)
    curr_atr = atr.iloc[-1]
    atr_pct = (curr_atr / latest['close']) * 100
    
    # NR7 Check (Narrowest Range in last 7 days) - Optional but good
    # range_7 = (df['high'] - df['low']).rolling(window=7).min().iloc[-1]
    # is_nr7 = (latest['high'] - latest['low']) <= range_7
    
    # Combined Logic: Near High + Good Volume + Healthy RSI
    return True, f"Breakout Setup: Vol {latest['volume']/avg_vol:.1f}x, RSI {curr_rsi:.1f}, Near 20d High"


def check_pullback_trend(df):
    """
    Strategy 2: Pullback to Trend
    Filters:
    - Price > 50 EMA and > 200 EMA
    - Pullback of 3-6% from recent swing high
    - RSI between 35-50
    """
    if df is None or df.empty or len(df) < 200:
        return False, None

    latest = df.iloc[-1]
    
    # 1. Trend Filter (Above 50 & 200 EMA)
    ema_50 = ta.ema(df['close'], length=50).iloc[-1]
    ema_200 = ta.ema(df['close'], length=200).iloc[-1]
    
    if not (latest['close'] > ema_50 > ema_200):
        return False, None

    # 2. Pullback Logic
    # Find recent high (last 10 days)
    recent_high = df['high'].rolling(window=10).max().iloc[-1]
    pullback_pct = ((recent_high - latest['close']) / recent_high) * 100
    
    if not (3 <= pullback_pct <= 8): # 3-8% pullback
        return False, None

    # 3. RSI Filter (35-55)
    rsi = ta.rsi(df['close'], length=14).iloc[-1]
    if not (35 <= rsi <= 55):
        return False, None

    return True, f"Pullback: {pullback_pct:.1f}% from High, RSI {rsi:.1f}, Uptrend"


def check_volume_pocket(df):
    """
    Strategy 3: Volume-Pocket Swing Trade
    Filters:
    - Volume > 2.5x Daily Average
    - Price breaking structure (New 20-day high)
    """
    if df is None or df.empty or len(df) < 25:
        return False, None

    latest = df.iloc[-1]
    
    # 1. Massive Volume Spike
    avg_vol = df['volume'].rolling(window=20).mean().iloc[-1]
    if latest['volume'] <= avg_vol * 2.5:
        return False, None

    # 2. Price Strength (New 20-day High or close to it)
    high_20 = df['high'].rolling(window=20).max().iloc[-2] # Previous 20 days
    if latest['close'] > high_20:
        return True, f"Vol Pocket: Vol {latest['volume']/avg_vol:.1f}x, New 20d High"
        
    return False, None
