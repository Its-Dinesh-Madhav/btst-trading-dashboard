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
import pandas_ta as ta

def process_stock_data(symbol, df_daily, strategy_type='all'):
    """
    Processes a single stock's dataframe for signals.
    df_daily: DataFrame with daily data (Open, High, Low, Close, Volume)
    """
    try:
        if df_daily.empty or len(df_daily) < 20:
            return None
            
        # Clean column names (ensure lowercase)
        df_daily.columns = [c.lower() for c in df_daily.columns]
        
        # 2. Apply Strategy
        from strategy import calculate_strategy_indicators
        df_daily = calculate_strategy_indicators(df_daily)
        
        # 3. Scan Last 10 Days for Signals
        last_signal = None  # 'BUY' or 'SELL'
        signal_details = {}
        golden_signal = None  # 'BUY' or 'SELL'
        
        days_to_scan = 10
        if len(df_daily) < days_to_scan + 2:
            days_to_scan = len(df_daily) - 2
        
        for i in range(len(df_daily) - days_to_scan, len(df_daily)):
            curr = df_daily.iloc[i]
            prev = df_daily.iloc[i - 1]
            
            # Sniper / Standard Strategy Checks (TSL)
            if strategy_type in ['all', 'standard', 'sniper']:
                # Buy Crossover
                if (prev['close'] < prev['tsl']) and (curr['close'] > curr['tsl']):
                    last_signal = 'BUY'
                    signal_details = {
                        'price': curr['close'],
                        'date': curr.name.strftime('%Y-%m-%d'),
                        'tsl': curr['tsl']
                    }
                # Sell Crossunder
                elif (prev['close'] > prev['tsl']) and (curr['close'] < curr['tsl']):
                    last_signal = 'SELL'
            
            # Golden Crossover detection
            if strategy_type in ['all', 'golden']:
                if check_golden_crossover_buy(df_daily):
                    golden_signal = 'BUY'
                elif check_golden_crossover_sell(df_daily):
                    golden_signal = 'SELL'
        
        # 4. Action based on Signals
        
        # --- Handle TSL / Sniper / Standard Signals ---
        if last_signal == 'SELL':
            remove_signal(symbol)
            
        elif last_signal == 'BUY':
            price = signal_details['price']
            date = signal_details['date']
            
            # Find Exact Trigger Time
            timestamp = f"{date} 15:30:00"

            # Calculate Trend Prediction
            tech_data = get_technical_analysis(symbol, df=df_daily)
            trend_pred = tech_data['prediction'] if tech_data else "Neutral"
            
            # DETERMINE SIGNAL STRENGTH
            strength = "Standard"
            try:
                ema_200 = ta.ema(df_daily['close'], length=200).iloc[-1]
                rsi = ta.rsi(df_daily['close'], length=14).iloc[-1]
                vol_avg = df_daily['volume'].rolling(window=20).mean().iloc[-1]
                vol_curr = df_daily['volume'].iloc[-1]
                
                if (price > ema_200) and (40 <= rsi <= 70) and (vol_curr > 1.5 * vol_avg):
                    strength = "Sniper"
            except Exception:
                pass
            
            # STRICT FILTERING FOR SNIPER STRATEGY
            if strategy_type == 'sniper' and strength != 'Sniper':
                return None
            
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
            price = df_daily['close'].iloc[-1]
            date = df_daily.index[-1].strftime('%Y-%m-%d')
            
            if last_signal != 'BUY': 
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
            
    except Exception as e:
        # print(f"Error processing {symbol}: {e}")
        return None
    return None

def chunk_list(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def scan_stocks(strategy_type='all'):
    print(f"--- Starting Algo Scanner ({strategy_type.upper()}) ---")
    
    # 1. Load Stock List
    symbols = load_stock_list()
    print(f"Loaded {len(symbols)} stocks to scan.")
    
    # 2. Batch Download and Process
    # Reduced chunk size to avoid Rate Limiting
    chunk_size = 20
    print(f"Scanning in batches of {chunk_size}...")
    
    total_processed = 0
    
    # Create a progress bar
    pbar = tqdm(total=len(symbols), unit="stock")
    
    for chunk in chunk_list(symbols, chunk_size):
        try:
            # Download batch
            # group_by='ticker' ensures we get a hierarchical index (Ticker -> OHLC)
            # threads=True uses yfinance's internal threading for download
            # auto_adjust=True to fix warning and ensure we get adjusted close
            data = yf.download(chunk, period="1y", interval="1d", group_by='ticker', threads=True, progress=False, auto_adjust=True)
            
            if data.empty:
                pbar.update(len(chunk))
                time.sleep(1) # Wait a bit even on failure
                continue
                
            # Process each symbol in the chunk
            for symbol in chunk:
                try:
                    df_sym = pd.DataFrame()
                    
                    if isinstance(data.columns, pd.MultiIndex):
                        # Extract data for this symbol
                        try:
                            df_sym = data.xs(symbol, level=0, axis=1)
                        except KeyError:
                            # Symbol might have failed to download
                            continue
                    else:
                        # If only one symbol was downloaded and it's not MultiIndex
                        if len(chunk) == 1 and chunk[0] == symbol:
                            df_sym = data
                        else:
                            continue
                    
                    # Drop rows with all NaNs
                    df_sym = df_sym.dropna(how='all')
                    
                    if not df_sym.empty:
                        process_stock_data(symbol, df_sym, strategy_type)
                        
                except Exception as e:
                    pass
                
                total_processed += 1
                pbar.update(1)
            
            # Sleep to avoid Rate Limiting
            time.sleep(2)
                
        except Exception as e:
            print(f"Batch download error: {e}")
            pbar.update(len(chunk))
            time.sleep(5) # Longer wait on error
            
    pbar.close()

    print("\n--- Scan Summary ---")
    print(f"Stocks Processed: {total_processed}")
    print(f"Stocks w/o Data:  {len(symbols) - total_processed}") # This is an approximation, better to track explicitly
    print(f"Signals Found:    N/A (needs explicit tracking in process_stock_data)") # This needs to be tracked
    print("--------------------")
    print("Check the Dashboard for results.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Algo Scanner')
    parser.add_argument('--strategy', type=str, default='all', 
                        choices=['all', 'standard', 'sniper', 'golden'],
                        help='Strategy to scan for: all, standard, sniper, or golden')
    
    args = parser.parse_args()
    scan_stocks(strategy_type=args.strategy)
