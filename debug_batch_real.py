import yfinance as yf
import pandas as pd
from scanner import process_stock_data
from strategy import calculate_strategy_indicators

def debug_batch_download():
    print("--- Debugging Batch Download ---")
    symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
    
    print(f"Downloading {symbols}...")
    data = yf.download(symbols, period="1y", interval="1d", group_by='ticker', threads=True, progress=False)
    
    print("\nData Shape:", data.shape)
    print("Data Columns:", data.columns)
    
    if data.empty:
        print("ERROR: Downloaded data is empty!")
        return

    # Check RELIANCE.NS
    symbol = "RELIANCE.NS"
    try:
        df_sym = data.xs(symbol, level=0, axis=1)
        print(f"\nExtracted {symbol} Data:")
        print(df_sym.tail())
        
        # Check for NaNs
        if df_sym.isnull().all().all():
             print("ERROR: All data is NaN!")
        
        # Run Strategy
        print(f"\nRunning Strategy on {symbol}...")
        df_sym.columns = [c.lower() for c in df_sym.columns] # Fix: Lowercase columns
        df_strat = calculate_strategy_indicators(df_sym.copy())
        print("Strategy Columns:", df_strat.columns)
        print("Last 5 TSL:", df_strat['tsl'].tail().values)
        print("Last 5 AVN:", df_strat['avn'].tail().values)
        
        # Run Process Logic
        print(f"\nRunning process_stock_data on {symbol}...")
        result = process_stock_data(symbol, df_sym, strategy_type='all')
        print("Result:", result)
        
    except Exception as e:
        print(f"ERROR extracting/processing {symbol}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_batch_download()
