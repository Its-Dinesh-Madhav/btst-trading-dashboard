import pandas as pd
from database import get_recent_signals
import datetime

def debug_dashboard():
    print("--- Debugging Dashboard Data ---")
    
    # 1. Fetch Data
    signals = get_recent_signals(limit=500)
    print(f"Fetched {len(signals)} signals from DB.")
    
    if not signals:
        print("❌ No signals returned from DB.")
        return

    df = pd.DataFrame(signals)
    print(f"DataFrame Shape: {df.shape}")
    print("Columns:", df.columns.tolist())
    
    # 2. Process Columns (mimic dashboard.py)
    if 'signal_strength' not in df.columns:
        df['signal_strength'] = 'Standard'
        
    df = df[['symbol', 'price', 'signal_date', 'trend_prediction', 'timestamp', 'signal_strength']]
    df.columns = ['Symbol', 'Price (INR)', 'Signal Date', 'Trend', 'Scanned At', 'Strength']
    
    print("\nFirst 5 rows:")
    print(df.head())
    
    # 3. Apply Filters (mimic "All" selection)
    trend_filter = "All"
    if trend_filter != "All":
        df = df[df['Trend'].str.contains(trend_filter, na=False)]
        
    print(f"\nAfter Trend Filter ('All'): {len(df)} rows")
    
    time_filter = "All"
    if time_filter != "All":
        # ... date logic ...
        pass
        
    print(f"After Time Filter ('All'): {len(df)} rows")
    
    # Check for 20MICRONS.NS
    row = df[df['Symbol'] == '20MICRONS.NS']
    if not row.empty:
        print("\n✅ Found 20MICRONS.NS:")
        print(row)
    else:
        print("\n❌ 20MICRONS.NS NOT found in DataFrame.")

if __name__ == "__main__":
    debug_dashboard()
