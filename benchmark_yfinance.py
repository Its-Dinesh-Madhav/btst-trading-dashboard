import yfinance as yf
import time

symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]

print(f"Fetching info for {len(symbols)} stocks...")
start_time = time.time()

for sym in symbols:
    try:
        ticker = yf.Ticker(sym)
        info = ticker.info
        # Access a few fields to ensure they are loaded
        mcap = info.get('marketCap')
        roe = info.get('returnOnEquity')
        print(f"{sym}: MCap={mcap}, ROE={roe}")
    except Exception as e:
        print(f"{sym}: Error {e}")

end_time = time.time()
duration = end_time - start_time
print(f"Total time: {duration:.2f} seconds")
print(f"Avg time per stock: {duration/len(symbols):.2f} seconds")
