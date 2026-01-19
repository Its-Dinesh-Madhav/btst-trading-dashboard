import pandas as pd
import requests
import io

def get_nifty50_symbols():
    """Returns Nifty 50 symbols."""
    symbols = [
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", 
        "KOTAKBANK", "LICI", "HINDUNILVR", "LT", "BAJFINANCE", "MARUTI", "AXISBANK",
        "ASIANPAINT", "TITAN", "SUNPHARMA", "ULTRACEMCO", "NTPC", "TATAMOTORS", "M&M",
        "ONGC", "ADANIENT", "ADANIPORTS", "POWERGRID", "TATASTEEL", "JSWSTEEL", "HCLTECH",
        "COALINDIA", "WIPRO", "SBILIFE", "DRREDDY", "BAJAJFINSV", "HDFCLIFE", "GRASIM",
        "TECHM", "BRITANNIA", "INDUSINDBK", "CIPLA", "EICHERMOT", "NESTLEIND", "TATACONSUM",
        "DIVISLAB", "HEROMOTOCO", "APOLLOHOSP", "LTIM", "BPCL", "UPL"
    ]
    return [f"{sym}.NS" for sym in symbols]

def get_nifty_next50_symbols():
    """Returns Nifty Next 50 symbols."""
    symbols = [
        "ABB", "ADANIENSOL", "ADANIGREEN", "ADANIPOWER", "ATGL", "AMBUJACEM", "BAJAJHLDNG",
        "BANKBARODA", "BEL", "BERGEPAINT", "BOSCHLTD", "CANBK", "CHOLAFIN", "COLPAL", "DLF",
        "DMART", "GAIL", "GODREJCP", "HAL", "HAVELLS", "HDFCAMC", "HINDPETRO", "ICICIGI",
        "ICICIPRULI", "INDIGO", "IOC", "IRCTC", "JINDALSTEL", "JSWENERGY", "LODHA", "MARICO",
        "MOTHERSON", "NAUKRI", "PIDILITIND", "PIIND", "PNB", "RECLTD", "SBICARD", "SHREECEM",
        "SIEMENS", "SRF", "TORNTPHARM", "TRENT", "TVSMOTOR", "VEDL", "ZOMATO", "ZYDUSLIFE",
        "VARUNBEV", "JIOFIN", "BHEL" 
    ]
    return [f"{sym}.NS" for sym in symbols]

def get_nifty100_symbols():
    """Returns Nifty 100 (Nifty 50 + Nifty Next 50) symbols."""
    return get_nifty50_symbols() + get_nifty_next50_symbols()

def get_all_nse_symbols():
    """
    Attempts to download the full list of active NSE equities.
    Falls back to Nifty 50 if download fails.
    """
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    try:
        # NSE blocks automated requests often, so we need headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            # Column is usually 'SYMBOL'
            symbols = df['SYMBOL'].tolist()
            print(f"Successfully fetched {len(symbols)} symbols from NSE.")
            return [f"{sym}.NS" for sym in symbols]
        else:
            print(f"Failed to fetch full list (Status: {response.status_code}). Using Nifty 50 fallback.")
            return get_nifty50_symbols()
    except Exception as e:
        print(f"Error fetching full list: {e}. Using Nifty 50 fallback.")
        return get_nifty50_symbols()

def load_stock_list(csv_path=None):
    """
    Loads stock list.
    """
    if csv_path:
        try:
            df = pd.read_csv(csv_path)
            symbols = df['Symbol'].tolist()
            return [s if s.endswith('.NS') or s.endswith('.BO') else f"{s}.NS" for s in symbols]
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return []
    else:
        # Default to all NSE symbols
        return get_all_nse_symbols()
