from analysis import get_technical_analysis, get_stock_news_sentiment, _sector_lookup
import pandas as pd

symbol = "RELIANCE.NS"
print(f"--- Debugging {symbol} ---")

# 1. Test Sector Lookup
print(f"Sector Lookup: {_sector_lookup(symbol)}")

# 2. Test News
print("Fetching News...")
score, news = get_stock_news_sentiment(symbol)
print(f"Sentiment Score: {score}")
print(f"News Items: {len(news)}")
if news:
    print(f"First News: {news[0]}")
else:
    print("No news found.")

# 3. Test Technicals
print("Fetching Technicals...")
tech = get_technical_analysis(symbol)
if tech:
    print("Technical Data Retrieved:")
    for k, v in tech.items():
        print(f"{k}: {v}")
else:
    print("Technical Analysis returned None.")

# 4. Check if sector mapping file exists and is readable
import os
print(f"Sector Mapping File Exists: {os.path.exists('sector_mapping.csv')}")
if os.path.exists('sector_mapping.csv'):
    df = pd.read_csv('sector_mapping.csv')
    print(f"Mapping Head:\n{df.head()}")
