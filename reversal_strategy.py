import yfinance as yf
import pandas as pd
import pandas_ta as ta
from stock_list import load_stock_list
import time
from tqdm import tqdm

def get_reversal_candidates(limit=50):
    """
    Scans for stocks that are in a downtrend but showing signs of reversal.
    Criteria:
    1. Downtrend: Price < 50 EMA OR RSI < 40 (recently)
    2. Reversal: 
       - Volume Spike (> 1.5x Avg)
       - RSI Rising
       - Green Candle (Close > Open)
    """
    print("--- Starting Reversal Strategy Scan ---")
    symbols = load_stock_list()
    candidates = []
    
    # Batch processing
    chunk_size = 20
    
    def chunk_list(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    for chunk in chunk_list(symbols, chunk_size):
        try:
            # Download data
            data = yf.download(chunk, period="6mo", interval="1d", group_by='ticker', threads=True, progress=False, auto_adjust=True)
            
            if data.empty:
                continue
                
            for symbol in chunk:
                try:
                    df = pd.DataFrame()
                    if isinstance(data.columns, pd.MultiIndex):
                        try:
                            df = data.xs(symbol, level=0, axis=1)
                        except KeyError:
                            continue
                    else:
                        if len(chunk) == 1 and chunk[0] == symbol:
                            df = data
                        else:
                            continue
                            
                    # Drop NaNs
                    df = df.dropna(how='all')
                    
                    if len(df) < 50:
                        continue
                        
                    # --- INDICATORS ---
                    # Ensure lowercase columns
                    df.columns = [c.lower() for c in df.columns]
                    
                    # EMA 50 (Trend)
                    df['ema_50'] = ta.ema(df['close'], length=50)
                    
                    # RSI 14 (Momentum)
                    df['rsi'] = ta.rsi(df['close'], length=14)
                    
                    # Volume SMA 20
                    df['vol_avg'] = df['volume'].rolling(window=20).mean()
                    
                    # Current Candle
                    curr = df.iloc[-1]
                    prev = df.iloc[-2]
                    
                    # --- LOGIC ---
                    
                    # 1. Downtrend Context
                    # Price below 50 EMA OR RSI was oversold recently
                    is_downtrend = (curr['close'] < curr['ema_50']) or (df['rsi'].iloc[-5:-1].min() < 40)
                    
                    if not is_downtrend:
                        continue
                        
                    # 2. Reversal Triggers
                    
                    # A. Volume Spike
                    vol_spike = curr['volume'] > 1.5 * curr['vol_avg']
                    
                    # B. RSI Recovery (Rising and crossed above 30 or 40)
                    rsi_rising = curr['rsi'] > prev['rsi']
                    rsi_recovery = (prev['rsi'] < 40) and (curr['rsi'] > 40)
                    
                    # C. Price Action (Green Candle + Engulfing-ish)
                    green_candle = curr['close'] > curr['open']
                    strong_move = curr['close'] > prev['high']
                    
                    reason = []
                    score = 0
                    
                    if vol_spike:
                        reason.append("Volume Spike")
                        score += 1
                        
                    if rsi_recovery:
                        reason.append("RSI Recovery")
                        score += 2
                    elif rsi_rising and curr['rsi'] < 60:
                        reason.append("RSI Rising")
                        score += 1
                        
                    if strong_move:
                        reason.append("Strong Price Action")
                        score += 2
                    elif green_candle:
                        score += 1
                        
                    # Filter: Must have at least Volume Spike OR Strong Move, AND be Green
                    if green_candle and (vol_spike or strong_move or rsi_recovery):
                        candidates.append({
                            'Symbol': symbol,
                            'Price': round(curr['close'], 2),
                            'Change %': round(((curr['close'] - prev['close']) / prev['close']) * 100, 2),
                            'RSI': round(curr['rsi'], 1),
                            'Volume': f"{curr['volume']/100000:.1f}L", # Lakhs
                            'Reason': ", ".join(reason),
                            'Score': score
                        })
                        
                except Exception:
                    continue
            
            # Rate limit
            time.sleep(1)
            
        except Exception:
            time.sleep(1)
            
    # Sort by Score (High to Low)
    df_results = pd.DataFrame(candidates)
    if not df_results.empty:
        df_results = df_results.sort_values(by='Score', ascending=False).head(limit)
        
    return df_results

if __name__ == "__main__":
    df = get_reversal_candidates()
    print(df)
