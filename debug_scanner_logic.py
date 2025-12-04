import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from strategy import calculate_strategy_indicators

def debug_stock(symbol):
    print(f"Debugging {symbol}...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="6mo", interval="1d")
    
    if df.empty:
        print("No data found.")
        return

    df.columns = [c.lower() for c in df.columns]
    print(f"Data fetched: {len(df)} rows. Last date: {df.index[-1]}")
    
    # Calculate Indicators
    df = calculate_strategy_indicators(df)
    
    # Print last 10 rows of relevant columns
    print("\nLast 10 rows (Date, Close, TSL, AVN):")
    print(df[['close', 'tsl', 'avn']].tail(10))
    
    # Check for signals in last 10 days
    print("\nChecking for signals...")
    days_to_scan = 10
    for i in range(len(df) - days_to_scan, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        date = curr.name.strftime('%Y-%m-%d')
        close = curr['close']
        tsl = curr['tsl']
        prev_close = prev['close']
        prev_tsl = prev['tsl']
        
        print(f"Date: {date} | Close: {close:.2f} | TSL: {tsl:.2f} | Prev Close: {prev_close:.2f} | Prev TSL: {prev_tsl:.2f}")
        
        if (prev_close < prev_tsl) and (close > tsl):
            print(f"  >>> BUY SIGNAL DETECTED on {date} <<<")
        elif (prev_close > prev_tsl) and (close < tsl):
            print(f"  >>> SELL SIGNAL DETECTED on {date} <<<")

if __name__ == "__main__":
    debug_stock("RELIANCE.NS")
