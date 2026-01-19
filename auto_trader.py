import time
import schedule
from scanner import scan_market
from paper_trader import PaperTrader
import sys
import logging
from datetime import datetime

# Setup Logging
logging.basicConfig(filename='auto_trader.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

trader = PaperTrader()

def job():
    """Main Trading Loop"""
    now = datetime.now()
    # Market Hours Check (9:15 to 3:30)
    if not (now.hour >= 9 and now.hour < 16):
        logging.info("Market Closed. Sleeping...")
        return
        
    logging.info("Starting Scan Cycle...")
    print(f"[{now}] Scanning markets...")
    
    try:
        # 1. Manage Exits first
        trader.manage_active_trades()
        
        # 2. Scan for New Signals
        # We reuse the scan logic but need it to return a list, not just print/save to DB
        # scan_market in scanner.py mainly updates DB. 
        # We can read from DB directly to get latest signals added in last few minutes.
        
        # Trigger a scan (updates DB)
        scan_market(strategy_type="standard", save_to_db=True)
        
        # Fetch fresh signals from DB (last 5 mins)
        from database import get_recent_signals
        recent_signals = get_recent_signals(limit=20)
        
        # Filter for freshly generated (e.g., last 5 mins)
        fresh_signals = []
        for sig in recent_signals:
            # Assuming 'timestamp' or 'signal_date' helps. 
            # In live scanner, we might want to pass the list memory-wise, 
            # but DB is safer for decoupling.
            fresh_signals.append(sig) 
            
        # Process Entry
        trader.process_buy_signals(fresh_signals)
        
        logging.info("Cycle Completed.")
        
    except Exception as e:
        logging.error(f"Error in cycle: {e}")
        print(f"Error: {e}")

def start_auto_trader():
    print("🚀 Auto Trader Started! Press Ctrl+C to stop.")
    logging.info("Auto Trader Started.")
    
    # Run immediately once
    job()
    
    # Schedule every 2 minutes
    schedule.every(2).minutes.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    start_auto_trader()
