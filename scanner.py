import yfinance as yf
import pandas_ta as ta
import pandas as pd
from stock_list import load_stock_list
from strategy import check_buy_signal, check_sell_signal, check_golden_crossover_buy, check_golden_crossover_sell
from database import add_signal, remove_signal
from analysis import get_technical_analysis
import time
from datetime import datetime
import argparse
import argparse
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import requests
import time

# Create a session with headers to mimic a browser
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
})

def process_stock(symbol, strategy_type='all'):
    """
    Fetches data and checks for signal for a single stock.
    Returns result dict if signal found, else None.
    strategy_type: 'all', 'sniper', 'golden'
    """
    try:
        # 1. Fetch Daily Data with Retries
        df_daily = pd.DataFrame()
        for attempt in range(3):
            try:
                ticker = yf.Ticker(symbol, session=session)
                df_daily = ticker.history(period="6mo", interval="1d")
                if not df_daily.empty:
                    break
                time.sleep(1) # Wait a bit before retry
            except Exception:
                time.sleep(1)
        
        if df_daily.empty:
            return {'Symbol': symbol, 'Status': 'No Data', 'HasData': False}
            
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
            
            # Sniper Strategy Checks
            if strategy_type in ['all', 'sniper']:
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
            if strategy_type in ['all', 'golden']:
                if check_golden_crossover_buy(df_daily):
                    golden_signal = 'BUY'
                elif check_golden_crossover_sell(df_daily):
                    golden_signal = 'SELL'
        
        # 4. Action based on Signals
        
        # --- Handle TSL / Sniper Signals ---
        if last_signal == 'SELL':
            remove_signal(symbol)
            # We don't return here because we might still have a Golden Crossover BUY
            
        elif last_signal == 'BUY':
            # We have a valid active buy signal
            price = signal_details['price']
            date = signal_details['date']
            daily_tsl = signal_details['tsl']
            
            # Find Exact Trigger Time
            timestamp = f"{date} 09:15:00"
            try:
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
            
            # DETERMINE SIGNAL STRENGTH (Standard vs Sniper)
            # Sniper Criteria: Price > 200 EMA, RSI 40-70, Vol > 1.5x Avg
            strength = "Standard"
            try:
                # EMA 200
                ema_200 = ta.ema(df_daily['close'], length=200).iloc[-1]
                # RSI
                rsi = ta.rsi(df_daily['close'], length=14).iloc[-1]
                # Volume
                vol_avg = df_daily['volume'].rolling(window=20).mean().iloc[-1]
                vol_curr = df_daily['volume'].iloc[-1]
                
                if (price > ema_200) and (40 <= rsi <= 70) and (vol_curr > 1.5 * vol_avg):
                    strength = "Sniper"
            except Exception:
                pass
            # Save to DB (add_signal handles duplicates, so safe to call again)
            add_signal(symbol, price, date, trend_pred, timestamp=timestamp, signal_strength=strength)
            print(f"✅ FOUND SIGNAL: {symbol} ({strength}) at {price}")
            
            return {
                'Symbol': symbol,
                'Price': price,
                'Date': date,
                'Trend': trend_pred,
                'Timestamp': timestamp,
                'Strength': strength
            }

        # --- Handle Golden Crossover Signals ---
        if golden_signal == 'BUY':
            # For GC, we just use the latest date/price
            price = df_daily['close'].iloc[-1]
            date = df_daily.index[-1].strftime('%Y-%m-%d')
            
            # Check if we already have a Standard/Sniper signal for this date to avoid clutter?
            # Or just add it as a separate entry. The DB allows multiple signals if details differ?
            # add_signal checks (symbol, date). If we want to store BOTH, we might need to differentiate.
            # But usually, if it's a GC, it's a strong signal on its own.
            # Let's save it with strength='Golden Crossover'
            
            # We need to be careful not to overwrite a Sniper signal if it happened same day.
            # But add_signal prevents duplicates based on (symbol, date).
            # If we want to support multiple signal types per day, we'd need to change DB schema or logic.
            # For now, let's assume if it's Sniper/Standard, that takes precedence for "Signal Date".
            # BUT Golden Crossover is a long term signal.
            
            # Let's try to add it. If it fails (duplicate), so be it.
            # Actually, we should probably check if we just added a signal above.
            
            if last_signal != 'BUY': # Only add GC if we didn't just add a TSL buy
                 tech_data = get_technical_analysis(symbol, df=df_daily)
                 trend_pred = tech_data['prediction'] if tech_data else "Neutral"
                 add_signal(symbol, price, date, trend_pred, signal_strength="Golden Crossover")
                 print(f"🏅 FOUND GOLDEN CROSSOVER: {symbol} at {price}")
                 
                 return {
                    'Symbol': symbol,
                    'Price': price,
                    'Date': date,
                    'Trend': trend_pred,
                    'Strength': "Golden Crossover"
                 }

            
    except Exception:
        return {'Symbol': symbol, 'Status': 'Error', 'HasData': False}
    return {'Symbol': symbol, 'Status': 'No Signal', 'HasData': True}

def scan_stocks(strategy_type='all'):
    print(f"--- Starting Algo Scanner ({strategy_type.upper()}) ---")
    
    # 1. Load Stock List
    symbols = load_stock_list()
    print(f"Loaded {len(symbols)} stocks to scan.")
    
    # 2. Iterate and Scan with Multithreading
    # Max workers = 10 to avoid hitting rate limits too hard but still be fast
    print("Scanning... (This may take a while for large lists)")
    
    
    data_fetched_count = 0
    no_data_count = 0
    signals_found_count = 0

    # Reduce workers to avoid rate limiting
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all tasks
        future_to_symbol = {executor.submit(process_stock, sym, strategy_type): sym for sym in symbols}
        
        # Process results as they complete with a progress bar
        for future in tqdm(as_completed(future_to_symbol), total=len(symbols), unit="stock"):
            try:
                result = future.result()
                if result:
                    if result.get('HasData', False):
                        data_fetched_count += 1
                    else:
                        no_data_count += 1
                        
                    if 'Price' in result: # Signal found
                        signals_found_count += 1
            except Exception as e:
                print(f"Task failed: {e}")

    print("\n--- Scan Summary ---")
    print(f"Stocks with Data: {data_fetched_count}")
    print(f"Stocks w/o Data:  {no_data_count}")
    print(f"Signals Found:    {signals_found_count}")
    print("--------------------")
    print("Check the Dashboard for results.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Algo Scanner')
    parser.add_argument('--strategy', type=str, default='all', 
                        choices=['all', 'sniper', 'golden'],
                        help='Strategy to scan for: all, sniper, or golden')
    
    args = parser.parse_args()
    scan_stocks(strategy_type=args.strategy)
