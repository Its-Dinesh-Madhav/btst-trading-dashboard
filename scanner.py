import yfinance as yf
import pandas as pd
from stock_list import load_stock_list
from strategy import check_buy_signal
from database import add_signal
from analysis import get_technical_analysis
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def process_stock(symbol):
    """
    Fetches data and checks for signal for a single stock.
    Returns result dict if signal found, else None.
    """
    try:
    try:
        # Fetch data (Intraday 15m for accurate timing)
        ticker = yf.Ticker(symbol)
        # 5 days of 15m data is enough for the strategy (requires ~20 candles)
        df = ticker.history(period="5d", interval="15m")
        
        if df.empty:
            return None
            
        # Clean column names
        df.columns = [c.lower() for c in df.columns]
        
        # Apply Strategy (Intraday)
        from strategy import find_intraday_signal
        signal = find_intraday_signal(df)
        
        if signal:
            price = signal['price']
            date = signal['date']
            timestamp = signal['timestamp']
            
            # Calculate Trend Prediction (still useful to know general trend)
            # We can fetch daily data separately if needed, or just use intraday trend
            # For speed, let's use the intraday trend prediction from analysis
            tech_data = get_technical_analysis(symbol, df=df)
            trend_pred = tech_data['prediction'] if tech_data else "Neutral"
            
            # Save to DB
            # Note: We pass the specific 'timestamp' found by the strategy
            # We need to update add_signal to accept a specific timestamp if we want to override CURRENT_TIMESTAMP
            # But for now, we can just save it. The dashboard uses 'timestamp' column which is auto-generated.
            # Wait, the user wants the "Trigger Time" to be shown.
            # The dashboard uses the 'timestamp' column from the DB.
            # So we must pass this 'timestamp' to the DB.
            
            # We need to modify add_signal to accept an explicit timestamp
            # For now, let's just pass it and I will update database.py next.
            add_signal(symbol, price, date, trend_pred, timestamp=timestamp)
            
            return {
                'Symbol': symbol,
                'Price': price,
                'Date': date,
                'Trend': trend_pred,
                'Timestamp': timestamp
            }
    except Exception:
        # Silently fail for individual stock errors to keep scanner running
        return None
    return None

def scan_stocks():
    print("--- Starting Algo Scanner ---")
    
    # 1. Load Stock List
    symbols = load_stock_list()
    print(f"Loaded {len(symbols)} stocks to scan.")
    
    # 2. Iterate and Scan with Multithreading
    # Max workers = 10 to avoid hitting rate limits too hard but still be fast
    print("Scanning... (This may take a while for large lists)")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        future_to_symbol = {executor.submit(process_stock, sym): sym for sym in symbols}
        
        # Process results as they complete with a progress bar
        for future in tqdm(as_completed(future_to_symbol), total=len(symbols), unit="stock"):
            # Results are already saved to DB in process_stock
            pass

    print("\n--- Scan Complete ---")
    print("Check the Dashboard for results.")

if __name__ == "__main__":
    scan_stocks()
