from database import init_db, add_signal, get_recent_signals, clear_db

print("Testing DB Migration and Trend Saving...")

# 1. Init DB (should trigger migration)
init_db()

# 2. Add signal with trend
add_signal("FILTER_TEST.NS", 500.0, "2025-11-26", "Strong Uptrend Expected")

# 3. Fetch and check
signals = get_recent_signals(limit=5)
found = False
for s in signals:
    if s['symbol'] == "FILTER_TEST.NS":
        print(f"Signal Found: {s['symbol']} | Trend: {s['trend_prediction']}")
        if s['trend_prediction'] == "Strong Uptrend Expected":
            print("SUCCESS: Trend saved correctly.")
            found = True
        else:
            print("FAILURE: Trend mismatch.")
        break

if not found:
    print("FAILURE: Signal not found.")
