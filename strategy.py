import pandas_ta as ta
import pandas as pd
import numpy as np

def calculate_strategy_indicators(df):
    """
    Calculates the strategy indicators (res, sup, avn, tsl) for the entire DataFrame.
    Returns the DataFrame with these new columns.
    """
    if df is None or df.empty or len(df) < 20:
        return df

    # --- STRATEGY PARAMETERS ---
    no = 3  # Swing period

    # --- CALCULATION ---
    # 1. Calculate Highest High and Lowest Low over 'no' periods
    df['res'] = df['high'].rolling(window=no).max()
    df['sup'] = df['low'].rolling(window=no).min()

    # 2. Calculate Trend State (avd, avn) and TSL
    df['avn'] = 0
    df['tsl'] = 0.0
    
    close = df['close'].values
    res = df['res'].values
    sup = df['sup'].values
    avn = np.zeros(len(df), dtype=int)
    tsl = np.zeros(len(df))
    
    curr_avn = 0
    
    for i in range(no, len(df)):
        prev_res = res[i-1]
        prev_sup = sup[i-1]
        curr_close = close[i]
        
        avd = 0
        if curr_close > prev_res:
            avd = 1
        elif curr_close < prev_sup:
            avd = -1
            
        if avd != 0:
            curr_avn = avd
        
        avn[i] = curr_avn
        
        if curr_avn == 1:
            tsl[i] = sup[i]
        else:
            tsl[i] = res[i]

    df['tsl'] = tsl
    df['avn'] = avn
    return df

def check_buy_signal(df):
    """
    Analyzes the DataFrame and returns True if a Buy signal is detected.
    """
    if df is None or df.empty or len(df) < 20:
        return False

    # Calculate indicators
    df = calculate_strategy_indicators(df)
    
    # 3. Check for Buy Signal (Crossover)
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Condition 1: Crossover (Close crosses above TSL)
    # And ensure we are in an Uptrend (avn == 1)
    crossover = (prev['close'] < prev['tsl']) and (latest['close'] > latest['tsl'])
    
    if crossover:
        return True

    return False

def find_intraday_signal(df):
    """
    Scans the DataFrame (intraday) to find if a buy signal occurred recently (e.g., today).
    Returns a dict with signal details if found, else None.
    """
    if df is None or df.empty or len(df) < 20:
        return None

    # Calculate indicators
    df = calculate_strategy_indicators(df)
    
    # Check specifically for signals in the last 'N' candles (e.g., last 1 day ~ 25 candles for 15m)
    # We iterate backwards to find the *latest* signal, or forwards for *first*?
    # User wants "time when signal triggered". If triggered at 10am and still valid, show 10am.
    
    # Get today's date from the last candle
    last_date = df.index[-1].date()
    
    # Filter for today's candles
    today_df = df[df.index.date == last_date]
    
    if today_df.empty:
        return None
        
    # We need to look at the transition from the candle *before* the current one
    # So we iterate through today's indices
    
    for i in range(len(df) - len(today_df), len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        # Condition: Crossover (Close crosses above TSL)
        crossover = (prev['close'] < prev['tsl']) and (curr['close'] > curr['tsl'])
        
        if crossover:
            return {
                'price': curr['close'],
                'date': curr.name.strftime('%Y-%m-%d'),
                'timestamp': curr.name.strftime('%Y-%m-%d %H:%M:%S')
            }
            
    return None
