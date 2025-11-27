from database import add_signal, get_recent_signals, clear_db

print("Testing Database...")
clear_db()

# Add dummy signal
add_signal("TEST.NS", 100.50, "2025-11-26")

# Fetch
signals = get_recent_signals()
if len(signals) == 1 and signals[0]['symbol'] == "TEST.NS":
    print("SUCCESS: Signal added and fetched.")
else:
    print("FAILURE: Database operation failed.")
    print(signals)
