import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from sklearn.ensemble import RandomForestClassifier

def get_btst_candidates(limit=50):
    """
    Scans for stocks with high probability of a Gap Up or positive move tomorrow.
    Returns a DataFrame of top candidates.
    """
    try:
        # 1. Load Stock List (using sector mapping as a source for now)
        mapping_df = pd.read_csv("sector_mapping.csv")
        symbols = mapping_df['symbol'].tolist()[:limit]
        
        if not symbols:
            return pd.DataFrame()
            
        # 2. Batch Download Data (Need enough for indicators)
        data = yf.download(symbols, period="6mo", progress=False)
        
        candidates = []
        
        # Handle MultiIndex
        try:
            close_df = data['Close']
            open_df = data['Open']
            high_df = data['High']
            low_df = data['Low']
            vol_df = data['Volume']
        except KeyError:
             # Fallback for single level or lowercase
            close_df = data.get('Close', data.get('close'))
            open_df = data.get('Open', data.get('open'))
            high_df = data.get('High', data.get('high'))
            low_df = data.get('Low', data.get('low'))
            vol_df = data.get('Volume', data.get('volume'))

        if close_df is None:
            return pd.DataFrame()

        for sym in symbols:
            try:
                # Extract series
                if isinstance(close_df, pd.DataFrame):
                    if sym not in close_df.columns: continue
                    c = close_df[sym].dropna()
                    o = open_df[sym].dropna()
                    h = high_df[sym].dropna()
                    l = low_df[sym].dropna()
                    v = vol_df[sym].dropna()
                else:
                    c, o, h, l, v = close_df, open_df, high_df, low_df, vol_df
                
                if len(c) < 50: continue
                
                # --- Scoring System (Weighted) ---
                score = 0
                reasons = []
                
                # 1. Trend (EMA 20)
                ema_20 = ta.ema(c, length=20).iloc[-1]
                if c.iloc[-1] > ema_20:
                    score += 15
                    reasons.append("Uptrend")
                
                # 2. Momentum (RSI)
                rsi_val = ta.rsi(c, length=14).iloc[-1]
                if 50 < rsi_val < 80:
                    score += 20
                    if rsi_val > 60:
                        reasons.append("Strong Momentum")
                
                # 3. Volume
                avg_vol = v.rolling(window=10).mean().iloc[-1]
                vol_ratio = v.iloc[-1] / avg_vol if avg_vol > 0 else 0
                if vol_ratio > 1.0:
                    score += 20
                    if vol_ratio > 1.5:
                        reasons.append("Volume Spike")
                elif vol_ratio > 0.8:
                    score += 10 # Partial score for decent volume
                
                # 4. Candle Strength (Close Position)
                candle_range = h.iloc[-1] - l.iloc[-1]
                if candle_range > 0:
                    close_pos = (c.iloc[-1] - l.iloc[-1]) / candle_range
                    if close_pos > 0.7:
                        score += 20
                        reasons.append("Strong Close")
                    elif close_pos > 0.5:
                        score += 10
                
                # --- AI Probability ---
                # Train model
                df_ml = pd.DataFrame({
                    'rsi': ta.rsi(c, length=14),
                    'vol_ratio': v / v.rolling(window=10).mean(),
                    'close_pos': (c - l) / (h - l),
                    'target': (o.shift(-1) > c).astype(int)
                }).dropna()
                
                prob = 50 # Default neutral
                if len(df_ml) > 30:
                    X = df_ml[['rsi', 'vol_ratio', 'close_pos']].iloc[:-1]
                    y = df_ml['target'].iloc[:-1]
                    model = RandomForestClassifier(n_estimators=50, max_depth=3, random_state=42)
                    model.fit(X, y)
                    
                    curr_feat = [[rsi_val, vol_ratio, close_pos]]
                    prob = model.predict_proba(curr_feat)[0][1] * 100
                
                # Add AI contribution to score (Max 25 points)
                if prob > 60:
                    score += 25
                    reasons.append("AI Bullish")
                elif prob > 50:
                    score += 10
                
                # Final Selection
                if score >= 40: # Lenient threshold to ensure results
                    candidates.append({
                        'Symbol': sym,
                        'Price': c.iloc[-1],
                        'Change %': ((c.iloc[-1] - c.iloc[-2])/c.iloc[-2])*100,
                        'BTST Score': score,
                        'Gap Up Prob %': prob,
                        'Reason': ", ".join(reasons[:3]), # Top 3 reasons
                        'RSI': rsi_val,
                        'Volume Ratio': vol_ratio
                    })
                        
            except Exception:
                continue
                
        # Sort by Score
        df_res = pd.DataFrame(candidates)
        if not df_res.empty:
            df_res = df_res.sort_values(by='BTST Score', ascending=False)
            
        return df_res
        
    except Exception as e:
        print(f"BTST Error: {e}")
        return pd.DataFrame()
