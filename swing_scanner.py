import yfinance as yf
import pandas as pd
from stock_list import load_stock_list
from swing_strategy import check_breakout_swing, check_pullback_trend, check_volume_pocket
from database import add_swing_signal
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def process_swing_stock(symbol, strategy_type='all'):
    """
    Fetches data and checks for swing signals.
    """
    try:
        # 1. Fetch Daily Data (Need at least 200 days for EMA 200)
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y", interval="1d")
        
        if df.empty or len(df) < 50:
            return None
            
        # Clean column names
        df.columns = [c.lower() for c in df.columns]
        
        latest_price = df['close'].iloc[-1]
        signal_date = df.index[-1].strftime('%Y-%m-%d')
        
        # 2. Check Strategies
        
        # Strategy 1: Breakout
        if strategy_type in ['all', 'breakout']:
            is_breakout, reason = check_breakout_swing(df)
            if is_breakout:
                add_swing_signal(symbol, latest_price, signal_date, 'Breakout', reason)
                return {'Symbol': symbol, 'Strategy': 'Breakout', 'Reason': reason}

        # Strategy 2: Pullback
        if strategy_type in ['all', 'pullback']:
            is_pullback, reason = check_pullback_trend(df)
            if is_pullback:
                add_swing_signal(symbol, latest_price, signal_date, 'Pullback', reason)
                return {'Symbol': symbol, 'Strategy': 'Pullback', 'Reason': reason}

        # Strategy 3: Volume Pocket
        if strategy_type in ['all', 'volume_pocket']:
            is_pocket, reason = check_volume_pocket(df)
            if is_pocket:
                add_swing_signal(symbol, latest_price, signal_date, 'VolumePocket', reason)
                return {'Symbol': symbol, 'Strategy': 'VolumePocket', 'Reason': reason}

    except Exception as e:
        # print(f"Error processing {symbol}: {e}")
        return None
    return None

def scan_swing_stocks(strategy_type='all'):
    print(f"--- Starting Swing Scanner ({strategy_type.upper()}) ---")
    
    symbols = load_stock_list()
    print(f"Loaded {len(symbols)} stocks to scan.")
    print("Scanning... (This may take a while)")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_symbol = {executor.submit(process_swing_stock, sym, strategy_type): sym for sym in symbols}
        
        for future in tqdm(as_completed(future_to_symbol), total=len(symbols), unit="stock"):
            pass

    print("\n--- Swing Scan Complete ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Swing Trading Scanner')
    parser.add_argument('--strategy', type=str, default='all', 
                        choices=['all', 'breakout', 'pullback', 'volume_pocket'],
                        help='Strategy to scan for')
    
    args = parser.parse_args()
    scan_swing_stocks(strategy_type=args.strategy)
