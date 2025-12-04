import yfinance as yf
import time
from concurrent.futures import ThreadPoolExecutor

symbols = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", 
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "LICI.NS",
    "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS", "MARUTI.NS", "AXISBANK.NS",
    "ASIANPAINT.NS", "TITAN.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS", "NTPC.NS",
    "TATAMOTORS.NS", "M&M.NS", "ONGC.NS", "ADANIENT.NS", "ADANIPORTS.NS",
    "POWERGRID.NS", "TATASTEEL.NS", "JSWSTEEL.NS", "HCLTECH.NS", "COALINDIA.NS",
    "WIPRO.NS", "SBILIFE.NS", "DRREDDY.NS", "BAJAJFINSV.NS", "HDFCLIFE.NS",
    "GRASIM.NS", "TECHM.NS", "BRITANNIA.NS", "INDUSINDBK.NS", "CIPLA.NS",
    "EICHERMOT.NS", "NESTLEIND.NS", "TATACONSUM.NS", "DIVISLAB.NS", "HEROMOTOCO.NS",
    "APOLLOHOSP.NS", "LTIM.NS", "BPCL.NS", "UPL.NS", "ADANIGREEN.NS"
]

def fetch_single(sym):
    try:
        dat = yf.Ticker(sym).history(period="1y")
        return len(dat)
    except:
        return 0

def test_sequential_threads():
    print(f"Testing Sequential/Threaded Fetch for {len(symbols)} stocks...")
    start = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        list(executor.map(fetch_single, symbols))
    end = time.time()
    print(f"Threaded Time: {end - start:.4f} seconds")

def test_batch_download():
    print(f"Testing Batch Download for {len(symbols)} stocks...")
    start = time.time()
    # threads=True is default, but explicit is good
    dat = yf.download(symbols, period="1y", group_by='ticker', threads=True, progress=False)
    end = time.time()
    print(f"Batch Time: {end - start:.4f} seconds")

if __name__ == "__main__":
    test_sequential_threads()
    test_batch_download()
