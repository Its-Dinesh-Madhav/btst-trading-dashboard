import time
import sys
import os
import yfinance as yf

# Add current directory to path
sys.path.append(os.getcwd())

import swing_scanner

def test_swing_batch_speed():
    print("\nTesting Swing Scanner Batch Speed (Small Subset)...")
    
    # Mock load_stock_list
    original_loader = swing_scanner.load_stock_list
    
    swing_scanner.load_stock_list = lambda: [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", 
        "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "LICI.NS",
        "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS", "MARUTI.NS", "AXISBANK.NS",
        "ASIANPAINT.NS", "TITAN.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS", "NTPC.NS"
    ]
    
    start_time = time.time()
    swing_scanner.scan_swing_stocks(strategy_type='all')
    end_time = time.time()
    
    print(f"Swing Batch Scan Time (20 stocks): {end_time - start_time:.4f} seconds")
    
    # Restore
    swing_scanner.load_stock_list = original_loader

if __name__ == "__main__":
    test_swing_batch_speed()
