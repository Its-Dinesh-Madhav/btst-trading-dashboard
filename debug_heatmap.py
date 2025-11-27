from analysis import get_sector_performance
import pandas as pd

print("Testing get_sector_performance...")
try:
    df = get_sector_performance(limit=5) # Try small batch first
    print(f"Result DataFrame Shape: {df.shape}")
    if not df.empty:
        print(df.head())
    else:
        print("DataFrame is empty.")
except Exception as e:
    print(f"Function failed with error: {e}")
