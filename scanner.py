import yfinance as yf
import pandas as pd
from stock_list import load_stock_list
from strategy import check_buy_signal, check_sell_signal, check_golden_crossover_buy, check_golden_crossover_sell
from database import add_signal, remove_signal
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
        # 1. Fetch Daily Data
        ticker = yf.Ticker(symbol)
        df_daily = ticker.history(period="6mo", interval="1d")
        
        if df_daily.empty:
            return None
            
        # Clean column names
        df_daily.columns = [c.lower() for c in df_daily.columns]
        
        # 2. Apply Strategy
        from strategy import calculate_strategy_indicators
        df_daily = calculate_strategy_indicators(df_daily)
        
        # 3. Scan Last 10 Days for Signals
        # Detect standard Sniper signals and Golden Crossover signals.
        
        last_signal = None  # 'BUY' or 'SELL'
        signal_details = {}
        golden_signal = None  # 'BUY' or 'SELL'
        
        days_to_scan = 10
        if len(df_daily) < days_to_scan + 2:
            days_to_scan = len(df_daily) - 2
        
        for i in range(len(df_daily) - days_to_scan, len(df_daily)):
            curr = df_daily.iloc[i]
            prev = df_daily.iloc[i - 1]
            
            # Sniper Buy Crossover
            if (prev['close'] < prev['tsl']) and (curr['close'] > curr['tsl']):
                last_signal = 'BUY'
                signal_details = {
                    'price': curr['close'],
                    'date': curr.name.strftime('%Y-%m-%d'),
                    'tsl': curr['tsl']
                }
            # Sniper Sell Crossunder
            elif (prev['close'] > prev['tsl']) and (curr['close'] < curr['tsl']):
                last_signal = 'SELL'
            
            # Golden Crossover detection using new functions
            if check_golden_crossover_buy(df_daily):
                golden_signal = 'BUY'
            elif check_golden_crossover_sell(df_daily):
                golden_signal = 'SELL'
        
        # 4. Action based on Signals
        if last_signal == 'SELL':
            remove_signal(symbol)
            return {'Symbol': symbol, 'Status': 'Removed (Sell Signal)'}
            
        elif last_signal == 'BUY':
            # We have a valid active buy signal (from today or recent past)
            price = signal_details['price']
            date = signal_details['date']
            daily_tsl = signal_details['tsl']
            
            # Find Exact Trigger Time (Intraday) for that specific date
            timestamp = f"{date} 09:15:00"
            
            try:
                # Fetch intraday data covering the signal date
                # 5d might not be enough if signal was 7 days ago, but max is 60d for 15m
                df_intra = ticker.history(period="1mo", interval="15m") 
                if not df_intra.empty:
                    df_intra.columns = [c.lower() for c in df_intra.columns]
                    df_today = df_intra[df_intra.index.strftime('%Y-%m-%d') == date]
                    
                    for idx, row in df_today.iterrows():
                        if row['close'] > daily_tsl:
                            timestamp = idx.strftime('%Y-%m-%d %H:%M:%S')
                            break
            except Exception:
                pass

            # Calculate Trend Prediction
            tech_data = get_technical_analysis(symbol, df=df_daily)
            trend_pred = tech_data['prediction'] if tech_data else "Neutral"
            
            # Save to DB (add_signal handles duplicates, so safe to call again)
            add_signal(symbol, price, date, trend_pred, timestamp=timestamp)
            
            return {
                'Symbol': symbol,
                'Price': price,
                'Date': date,
                'Trend': trend_pred,
                'Timestamp': timestamp
            }
            
    except Exception:
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
