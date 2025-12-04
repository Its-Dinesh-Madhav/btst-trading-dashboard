import yfinance as yf
import pandas as pd
import pandas_ta as ta
from strategy import calculate_strategy_indicators
from stock_list import load_stock_list
import datetime
from tqdm import tqdm

def scan_until_signal():
    symbols = load_stock_list()
    print(f"Loaded {len(symbols)} symbols.")
    
    count = 0
    for symbol in tqdm(symbols):
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1mo", interval="1d")
            
            if df.empty or len(df) < 20:
                continue

            df.columns = [c.lower() for c in df.columns]
            df = calculate_strategy_indicators(df)
            
            # Check last 5 days
            for i in range(len(df) - 5, len(df)):
                curr = df.iloc[i]
                prev = df.iloc[i-1]
                
                # Buy Signal
                if (prev['close'] < prev['tsl']) and (curr['close'] > curr['tsl']):
                    print(f"\n🚀 FOUND SIGNAL: {symbol} on {curr.name.strftime('%Y-%m-%d')}")
                    print(f"Prev Close: {prev['close']}, Prev TSL: {prev['tsl']}")
                    print(f"Curr Close: {curr['close']}, Curr TSL: {curr['tsl']}")
                    return # Stop after finding one
                    
        except Exception:
            pass
            
        count += 1
        if count > 500:
            print("Scanned 500 stocks, no signals found.")
            break

if __name__ == "__main__":
    scan_until_signal()
