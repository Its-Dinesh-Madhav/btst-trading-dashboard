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
        # 1. Fetch Daily Data (The "Pine Script" Logic)
        ticker = yf.Ticker(symbol)
        df_daily = ticker.history(period="6mo", interval="1d")
        
        if df_daily.empty:
            return None
            
        # Clean column names
        df_daily.columns = [c.lower() for c in df_daily.columns]
        
        # 2. Apply Strategy on Daily Frame
        from strategy import calculate_strategy_indicators
        df_daily = calculate_strategy_indicators(df_daily)
        
        # Check Buy Condition manually to get the TSL level
        latest = df_daily.iloc[-1]
        prev = df_daily.iloc[-2]
        
        # Condition: Crossover (Close crosses above TSL)
        crossover = (prev['close'] < prev['tsl']) and (latest['close'] > latest['tsl'])
        
        if crossover:
            price = latest['close']
            date = latest.name.strftime('%Y-%m-%d')
            daily_tsl = latest['tsl']
            
            # 3. Find Exact Trigger Time using Intraday Data
            # We want the time when Price > Daily TSL first happened today
            timestamp = f"{date} 09:15:00" # Default to market open if not found
            
            try:
                # Fetch today's 15m data
                df_intra = ticker.history(period="5d", interval="15m")
                if not df_intra.empty:
                    # Filter for today
                    df_intra.columns = [c.lower() for c in df_intra.columns]
                    today_str = latest.name.strftime('%Y-%m-%d')
                    df_today = df_intra[df_intra.index.strftime('%Y-%m-%d') == today_str]
                    
                    # Find first candle > Daily TSL
                    for idx, row in df_today.iterrows():
                        if row['close'] > daily_tsl:
                            timestamp = idx.strftime('%Y-%m-%d %H:%M:%S')
                            break
            except Exception:
                pass # Fallback to default timestamp
            
            # Calculate Trend Prediction
            tech_data = get_technical_analysis(symbol, df=df_daily)
            trend_pred = tech_data['prediction'] if tech_data else "Neutral"
            
            # Save to DB
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
