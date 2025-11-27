from forecasting import get_ai_price_prediction

symbol = "RELIANCE.NS"
print(f"🔮 Running AI Prediction for {symbol}...")

pred = get_ai_price_prediction(symbol)

if pred:
    print("--- AI Forecast ---")
    print(f"Current Price: {pred['current_price']:.2f}")
    print(f"Predicted (5d avg): {pred['predicted_price']:.2f}")
    print(f"Change: {pred['change_pct']:.2f}%")
    print(f"Direction: {pred['direction']}")
    print(f"Confidence: {pred['confidence']:.1f}%")
else:
    print("AI Prediction failed.")
