import time
import sys
import os
import pandas as pd
import yfinance as yf

# Add current directory to path
sys.path.append(os.getcwd())

from scanner import process_stock_data, scan_stocks
from strategy import calculate_strategy_indicators

def test_single_stock_logic():
    symbol = "RELIANCE.NS"
    print(f"Testing logic for {symbol}...")
    
    # Manually fetch data to pass to function
    df = yf.Ticker(symbol).history(period="1y")
    
    start_time = time.time()
    result = process_stock_data(symbol, df, strategy_type='all')
    end_time = time.time()
    
    print(f"Logic Time taken: {end_time - start_time:.4f} seconds")
    print("Result:", result)

def test_batch_scan_speed():
    print("\nTesting Batch Scan Speed (Small Subset)...")
    # We will mock load_stock_list to return just 20 stocks for a quick test
    import scanner
    original_loader = scanner.load_stock_list
    
    scanner.load_stock_list = lambda: [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", 
        "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "LICI.NS",
        "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS", "MARUTI.NS", "AXISBANK.NS",
        "ASIANPAINT.NS", "TITAN.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS", "NTPC.NS"
    ]
    
    start_time = time.time()
    scanner.scan_stocks(strategy_type='all')
    end_time = time.time()
    
    print(f"Batch Scan Time (20 stocks): {end_time - start_time:.4f} seconds")
    
    # Restore
    scanner.load_stock_list = original_loader

if __name__ == "__main__":
    test_single_stock_logic()
    test_batch_scan_speed()
