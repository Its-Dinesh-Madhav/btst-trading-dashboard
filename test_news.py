import yfinance as yf

print("Fetching Market News...")
ticker = yf.Ticker("^NSEI")
news = ticker.news

if news:
    print(f"Found {len(news)} news items.")
    print("Raw First Item:")
    print(news[0])
else:
    print("No news found.")
