import yfinance as yf
import pandas as pd
import pandas_ta as ta
from stock_list import load_stock_list
import time
from tqdm import tqdm

def get_breakout_candidates(limit=50):
    """
    Implements the "3-Step Methodology for Identifying Breakout Candidates".
    
    Step 1: Fundamental Strength (Assumed pre-filtered or Nifty 500)
    Step 2: The Setup (Healthy Pullback in Uptrend)
       - Trend: Price > 50 SMA & 200 SMA
       - Pullback: Price near Support (20 SMA or 50 SMA)
       - Volume: Lower volume during pullback (checked via recent avg)
    Step 3: The Trigger (Pre-Breakout Signal)
       - Patterns: Hammer, Dragonfly Doji, Bullish Engulfing, Morning Star
       - Volume Confirmation: Vol > Avg Vol
    """
    print("--- Starting 3-Step Breakout Scan ---")
    symbols = load_stock_list()
    candidates = []
    
    # Batch processing
    chunk_size = 20
    
    def chunk_list(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    for chunk in chunk_list(symbols, chunk_size):
        try:
            # Download data (need enough for 200 SMA)
            data = yf.download(chunk, period="1y", interval="1d", group_by='ticker', threads=True, progress=False, auto_adjust=True)
            
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
                    
                    if len(df) < 200:
                        continue
                        
                    # --- INDICATORS ---
                    df.columns = [c.lower() for c in df.columns]
                    
                    # Moving Averages
                    df['sma_20'] = ta.sma(df['close'], length=20)
                    df['sma_50'] = ta.sma(df['close'], length=50)
                    df['sma_200'] = ta.sma(df['close'], length=200)
                    
                    # Volume Avg
                    df['vol_avg'] = df['volume'].rolling(window=20).mean()
                    
                    curr = df.iloc[-1]
                    prev = df.iloc[-2]
                    prev2 = df.iloc[-3]
                    
                    # --- STEP 2: THE SETUP (Uptrend + Pullback) ---
                    
                    # 1. Long-Term Uptrend
                    is_uptrend = (curr['close'] > curr['sma_50']) and (curr['close'] > curr['sma_200'])
                    
                    if not is_uptrend:
                        continue
                        
                    # 2. Pullback to Support (Near 20 SMA or 50 SMA)
                    # "Near" defined as within 3% range
                    dist_20 = abs(curr['close'] - curr['sma_20']) / curr['sma_20']
                    dist_50 = abs(curr['close'] - curr['sma_50']) / curr['sma_50']
                    
                    at_support = (dist_20 < 0.03) or (dist_50 < 0.03)
                    
                    # 3. Short-term dip (Last 3-5 days generally down or consolidation)
                    # Simple check: Price lower than 5 days ago
                    recent_dip = curr['close'] < df['close'].iloc[-5]
                    
                    if not (at_support or recent_dip):
                        continue

                    # --- STEP 3: THE TRIGGER (Patterns + Volume) ---
                    
                    patterns = []
                    
                    # A. Hammer / Dragonfly Doji
                    # Lower wick >= 2x body, Upper wick small
                    body = abs(curr['close'] - curr['open'])
                    lower_wick = min(curr['close'], curr['open']) - curr['low']
                    upper_wick = curr['high'] - max(curr['close'], curr['open'])
                    
                    is_hammer = (lower_wick >= 2 * body) and (upper_wick <= body)
                    if is_hammer:
                        patterns.append("Hammer/Dragonfly")
                        
                    # B. Bullish Engulfing
                    # Prev candle Red, Curr candle Green, Curr wraps Prev
                    is_engulfing = (prev['close'] < prev['open']) and \
                                   (curr['close'] > curr['open']) and \
                                   (curr['close'] > prev['open']) and \
                                   (curr['open'] < prev['close'])
                    if is_engulfing:
                        patterns.append("Bullish Engulfing")
                        
                    # C. Morning Star (Approximate)
                    # Red -> Doji/Small -> Green
                    is_morning_star = (prev2['close'] < prev2['open']) and \
                                      (abs(prev['close'] - prev['open']) < (prev2['open'] - prev2['close']) * 0.5) and \
                                      (curr['close'] > curr['open']) and \
                                      (curr['close'] > (prev2['close'] + prev2['open'])/2)
                    if is_morning_star:
                        patterns.append("Morning Star")
                        
                    if not patterns:
                        continue
                        
                    # D. Volume Confirmation
                    vol_confirm = curr['volume'] > curr['vol_avg']
                    
                    if vol_confirm:
                        patterns.append("High Volume")
                        
                    # Final Selection
                    candidates.append({
                        'Symbol': symbol,
                        'Price': round(curr['close'], 2),
                        'Support': "20 SMA" if dist_20 < dist_50 else "50 SMA",
                        'Patterns': ", ".join(patterns),
                        'Volume': f"{curr['volume']/100000:.1f}L",
                        'Score': len(patterns) + (1 if vol_confirm else 0)
                    })
                        
                except Exception:
                    continue
            
            time.sleep(1)
            
        except Exception:
            time.sleep(1)
            
    # Sort by Score
    df_results = pd.DataFrame(candidates)
    if not df_results.empty:
        df_results = df_results.sort_values(by='Score', ascending=False).head(limit)
        
    return df_results

if __name__ == "__main__":
    df = get_breakout_candidates()
    print(df)
