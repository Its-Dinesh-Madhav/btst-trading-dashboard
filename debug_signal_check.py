import yfinance as yf
import pandas as pd
from strategy import calculate_strategy_indicators
import argparse

def debug_stock(symbol):
    print(f"--- Debugging {symbol} ---")
    
    # Fetch data
    print("Fetching data...")
    df = yf.Ticker(symbol).history(period="1y", interval="1d", auto_adjust=True)
    
    if df.empty:
        print("Error: No data found.")
        return

    # Clean columns
    df.columns = [c.lower() for c in df.columns]
    
    # Calculate Indicators
    print("Calculating indicators...")
    df = calculate_strategy_indicators(df)
    
    # Show last 10 days
    print("\nLast 10 Days Data:")
    cols = ['close', 'high', 'low', 'res', 'sup', 'avn', 'tsl']
    print(df[cols].tail(10))
    
    # Check for Crossover
    print("\nChecking for Buy Signal (Close > TSL and Prev Close < Prev TSL)...")
    
    for i in range(len(df)-5, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        date = curr.name.strftime('%Y-%m-%d')
        close = curr['close']
        tsl = curr['tsl']
        prev_close = prev['close']
        prev_tsl = prev['tsl']
        
        is_buy = (prev_close < prev_tsl) and (close > tsl)
        is_sell = (prev_close > prev_tsl) and (close < tsl)
        
        status = "NONE"
        if is_buy: status = "BUY SIGNAL"
        if is_sell: status = "SELL SIGNAL"
        
        print(f"Date: {date} | Close: {close:.2f} | TSL: {tsl:.2f} | PrevClose: {prev_close:.2f} | PrevTSL: {prev_tsl:.2f} | {status}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol", help="Stock symbol (e.g., RELIANCE.NS)")
    args = parser.parse_args()
    debug_stock(args.symbol)
