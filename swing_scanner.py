import yfinance as yf
import pandas as pd
from stock_list import load_stock_list
from swing_strategy import check_breakout_swing, check_pullback_trend, check_volume_pocket
from database import add_swing_signal
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def process_swing_stock_data(symbol, df, strategy_type='all'):
    """
    Checks for swing signals on a pre-fetched DataFrame.
    """
    try:
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

def chunk_list(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def scan_swing_stocks(strategy_type='all'):
    print(f"--- Starting Swing Scanner ({strategy_type.upper()}) ---")
    
    symbols = load_stock_list()
    print(f"Loaded {len(symbols)} stocks to scan.")
    
    # Batch Download
    chunk_size = 20
    print(f"Scanning in batches of {chunk_size}...")
    
    pbar = tqdm(total=len(symbols), unit="stock")
    
    import time
    
    for chunk in chunk_list(symbols, chunk_size):
        try:
            # Download batch (Need 1y for EMA 200)
            data = yf.download(chunk, period="1y", interval="1d", group_by='ticker', threads=True, progress=False, auto_adjust=True)
            
            if data.empty:
                pbar.update(len(chunk))
                time.sleep(1)
                continue
                
            for symbol in chunk:
                try:
                    df_sym = pd.DataFrame()
                    
                    if isinstance(data.columns, pd.MultiIndex):
                        try:
                            df_sym = data.xs(symbol, level=0, axis=1)
                        except KeyError:
                            continue
                    else:
                        if len(chunk) == 1 and chunk[0] == symbol:
                            df_sym = data
                        else:
                            continue
                    
                    df_sym = df_sym.dropna(how='all')
                    
                    if not df_sym.empty:
                        process_swing_stock_data(symbol, df_sym, strategy_type)
                        
                except Exception:
                    pass
                
                pbar.update(1)
            
            time.sleep(2)
                
        except Exception as e:
            print(f"Batch error: {e}")
            pbar.update(len(chunk))
            time.sleep(5)

    pbar.close()
    print("\n--- Swing Scan Complete ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Swing Trading Scanner')
    parser.add_argument('--strategy', type=str, default='all', 
                        choices=['all', 'breakout', 'pullback', 'volume_pocket'],
                        help='Strategy to scan for')
    
    args = parser.parse_args()
    scan_swing_stocks(strategy_type=args.strategy)
