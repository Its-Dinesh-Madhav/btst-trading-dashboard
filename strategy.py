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

def check_sell_signal(df):
    """
    Analyzes the DataFrame and returns True if a Sell signal is detected.
    """
    if df is None or df.empty or len(df) < 20:
        return False

    # Calculate indicators (if not already done, but usually passed df has them or we recalc)
    # To be safe, recalc if columns missing, but usually we pass fresh df
    if 'tsl' not in df.columns:
        df = calculate_strategy_indicators(df)
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Condition: Crossunder (Close crosses below TSL)
    crossunder = (prev['close'] > prev['tsl']) and (latest['close'] < latest['tsl'])
    
    if crossunder:
        return True

    return False


def calculate_golden_crossover(df, short_period=9, long_period=21):
    """
    Calculate short and long EMA and generate a 'gc_signal' column:
    - 'Buy' when short EMA crosses above long EMA
    - 'Sell' when short EMA crosses below long EMA
    - 'None' otherwise
    """
    if df is None or df.empty or len(df) < long_period:
        return df
    # Calculate EMAs using pandas_ta
    df['ema_short'] = ta.ema(df['close'], length=short_period)
    df['ema_long'] = ta.ema(df['close'], length=long_period)
    df['gc_signal'] = 'None'
    for i in range(1, len(df)):
        prev_short = df.at[i-1, 'ema_short']
        prev_long = df.at[i-1, 'ema_long']
        cur_short = df.at[i, 'ema_short']
        cur_long = df.at[i, 'ema_long']
        if pd.isna(prev_short) or pd.isna(prev_long) or pd.isna(cur_short) or pd.isna(cur_long):
            continue
        if prev_short <= prev_long and cur_short > cur_long:
            df.at[i, 'gc_signal'] = 'Buy'
        elif prev_short >= prev_long and cur_short < cur_long:
            df.at[i, 'gc_signal'] = 'Sell'
    return df


def check_golden_crossover_buy(df):
    """Return True if the latest row has a Golden Crossover Buy signal."""
    if df is None or df.empty:
        return False
    df = calculate_golden_crossover(df)
    latest = df.iloc[-1]
    return latest.get('gc_signal') == 'Buy'


def check_golden_crossover_sell(df):
    """Return True if the latest row has a Golden Crossover Sell signal."""
    if df is None or df.empty:
        return False
    df = calculate_golden_crossover(df)
    latest = df.iloc[-1]
    return latest.get('gc_signal') == 'Sell'
