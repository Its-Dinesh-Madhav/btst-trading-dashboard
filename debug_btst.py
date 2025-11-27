import yfinance as yf
import pandas as pd
import pandas_ta as ta

symbols = ["RELIANCE.NS", "TCS.NS"]
print(f"Debugging BTST for {symbols}...")

data = yf.download(symbols, period="6mo", progress=False)

close_df = data['Close']
vol_df = data['Volume']

for sym in symbols:
    print(f"\n--- {sym} ---")
    c = close_df[sym].dropna()
    v = vol_df[sym].dropna()
    
    if len(c) < 50:
        print("Not enough data")
        continue
        
    ema_20 = ta.ema(c, length=20).iloc[-1]
    rsi = ta.rsi(c, length=14).iloc[-1]
    avg_vol = v.rolling(window=10).mean().iloc[-1]
    vol_ratio = v.iloc[-1] / avg_vol
    
    print(f"Price: {c.iloc[-1]:.2f}")
    print(f"EMA 20: {ema_20:.2f} (Pass: {c.iloc[-1] > ema_20})")
    print(f"RSI: {rsi:.2f} (Pass: {55 < rsi < 80})")
    print(f"Vol Ratio: {vol_ratio:.2f} (Pass: {vol_ratio > 1.2})")
