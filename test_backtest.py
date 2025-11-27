from backtester import run_backtest

symbol = "RELIANCE.NS"
print(f"Running Backtest for {symbol}...")

results = run_backtest(symbol)

if results:
    print("--- Backtest Results ---")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']:.2f}%")
    print(f"Total Return: {results['total_return']:.2f}%")
    print(f"Profit Factor: {results['profit_factor']:.2f}")
    print("\nTrades Head:")
    if results['trades']:
        import pandas as pd
        print(pd.DataFrame(results['trades']).head())
else:
    print("Backtest failed or returned None.")
