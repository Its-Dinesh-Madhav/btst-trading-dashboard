from btst_strategy import get_btst_candidates

print("Running BTST Scan...")
df = get_btst_candidates(limit=10)

if not df.empty:
    print(f"Found {len(df)} candidates.")
    print(df.head())
else:
    print("No candidates found (or error occurred).")
