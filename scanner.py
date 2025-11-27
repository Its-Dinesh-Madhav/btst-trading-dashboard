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
        # Fetch data (Daily timeframe)
        # Fetching 3 months to ensure enough data for rolling windows
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="6mo", interval="1d") # Increased to 6mo for ADX
        
        if df.empty:
            return None
            
        # Clean column names
        df.columns = [c.lower() for c in df.columns]
        
        # Apply Strategy
        if check_buy_signal(df):
            price = df.iloc[-1]['close']
            date = df.index[-1].strftime('%Y-%m-%d')
            
            # Calculate Trend Prediction immediately
            # We pass the existing DF to avoid re-fetching
            tech_data = get_technical_analysis(symbol, df=df)
            trend_pred = tech_data['prediction'] if tech_data else "Neutral"
            
            # Save to DB immediately
            add_signal(symbol, price, date, trend_pred)
            
            return {
                'Symbol': symbol,
                'Price': price,
                'Date': date,
                'Trend': trend_pred
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
