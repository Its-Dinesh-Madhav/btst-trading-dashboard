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
    # Vectorized approach
    
    # Shift to get previous values (avoid lookahead)
    df['prev_res'] = df['res'].shift(1)
    df['prev_sup'] = df['sup'].shift(1)
    
    # Calculate avd (1 if close > prev_res, -1 if close < prev_sup, else 0)
    # We use 0 as default, then forward fill
    
    conditions = [
        (df['close'] > df['prev_res']),
        (df['close'] < df['prev_sup'])
    ]
    choices = [1, -1]
    
    # Create a series for avd with NaNs where condition is not met
    # This allows us to ffill() to simulate "valuewhen"
    df['avd_raw'] = np.select(conditions, choices, default=np.nan)
    
    # Forward fill to get avn (last non-zero avd)
    df['avn'] = df['avd_raw'].ffill().fillna(0).astype(int)
    
    # Calculate TSL based on avn
    # If avn == 1 (Uptrend), TSL = prev_sup
    # If avn == -1 (Downtrend), TSL = prev_res
    df['tsl'] = np.where(df['avn'] == 1, df['prev_sup'], df['prev_res'])
    
    # Clean up temporary columns
    df.drop(columns=['prev_res', 'prev_sup', 'avd_raw'], inplace=True)

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
