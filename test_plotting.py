from plotting import plot_stock_chart

symbol = "RELIANCE.NS"
print(f"Generating Chart for {symbol}...")

fig = plot_stock_chart(symbol)

if fig:
    print("SUCCESS: Chart generated.")
    # In a real environment we could fig.show(), but here we just check object creation
    print(f"Figure Type: {type(fig)}")
    print(f"Data Traces: {len(fig.data)}")
else:
    print("FAILURE: Chart generation failed.")
