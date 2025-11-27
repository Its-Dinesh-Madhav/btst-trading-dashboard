from plotting import plot_stock_chart

symbol = "RELIANCE.NS"
print(f"Generating TV Chart for {symbol}...")

chart_data = plot_stock_chart(symbol)

if chart_data:
    print("SUCCESS: Chart data generated.")
    print(f"Keys: {chart_data.keys()}")
    print(f"Series Count: {len(chart_data['series'])}")
    print(f"First Series Type: {chart_data['series'][0]['type']}")
else:
    print("FAILURE: Chart generation failed.")
