from analysis import get_stock_news_sentiment, get_technical_analysis

symbol = "RELIANCE.NS"
print(f"Testing Analysis for {symbol}...")

# Test Sentiment
print("\n--- Sentiment ---")
score, news = get_stock_news_sentiment(symbol)
print(f"Score: {score}")
print(f"News Count: {len(news)}")
if news:
    print(f"Sample: {news[0]['title']}")

# Test Technicals
print("\n--- Technicals ---")
tech = get_technical_analysis(symbol)
if tech:
    print(f"ADX: {tech['adx']}")
    print(f"RSI: {tech['rsi']}")
    print(f"RVOL: {tech['rvol']}")
    print(f"Prediction: {tech['prediction']}")
else:
    print("Failed to get technicals.")
