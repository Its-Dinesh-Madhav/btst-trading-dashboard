from database import init_portfolio_db, add_to_portfolio, get_portfolio, remove_from_portfolio

print("Testing Portfolio Functions...")

# 1. Init (ensure table exists)
init_portfolio_db()

# 2. Add Item
symbol = "TEST_PORTFOLIO.NS"
print(f"Adding {symbol}...")
added = add_to_portfolio(symbol, 100.0, 'WATCHLIST', 'Test Note')
if added:
    print("Success: Added to DB.")
else:
    print("Info: Already exists.")

# 3. Fetch
items = get_portfolio()
found = False
for item in items:
    if item['symbol'] == symbol:
        print(f"Found Item: {item['symbol']} | Status: {item['status']} | Price: {item['entry_price']}")
        found = True
        break

if found:
    print("SUCCESS: Portfolio fetch working.")
else:
    print("FAILURE: Item not found.")

# 4. Cleanup
remove_from_portfolio(symbol)
print("Cleanup: Removed test item.")
