import time
import schedule
from scanner import scan_stocks as scan_market
from paper_trader import PaperTrader
from database import get_recent_signals, get_todays_trade_count
import sys
import logging
from datetime import datetime

# Setup Logging
logging.basicConfig(filename='auto_trader.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

trader = PaperTrader()

# Global Buffer
signal_buffer = []

def job():
    """Main Trading Loop"""
    global signal_buffer
    
    now = datetime.now()
    # Market Hours Check (9:15 to 3:30)
    if not (now.hour >= 9 and now.hour < 16):
        logging.info("Market Closed. Sleeping...")
        print(f"[{now}] Market Closed.")
        time.sleep(60)
        return
        
    logging.info("Starting Scan Cycle...")
    print(f"[{now}] Scanning markets... (Buffer: {len(signal_buffer)})")
    
    try:
        # 1. Manage Exits first
        trader.manage_active_trades()
        
        # 2. Check Daily Limit
        if get_todays_trade_count() >= trader.MAX_TRADES_PER_DAY:
            print("Daily limit reached. Monitoring exits only.")
            return

        # 3. Scan for New Signals (Trigger DB Update)
        # scan_stocks saves to DB automatically
        scan_market(strategy_type="standard")
        
        # 4. Fetch Fresh Signals (Last 5 mins)
        # 4. Fetch Fresh Signals (Last 5 mins)
        recent_signals = get_recent_signals(limit=20)
        
        # Collect signals that are RECENT (e.g., within last 2 minutes)
        # to avoid processing old signals repeatedly.
        # But for buffer logic, we might want to just process what's "new" since last check.
        # Ideally, we should track processed IDs. 
        # For simplicity, we pass recent 20 to 'process_buy_signals' which checks selection criteria.
        
        # Get Candidates (Don't execute yet)
        candidates = trader.process_buy_signals(recent_signals, execute=False)
        
        if candidates:
            print(f"Found {len(candidates)} candidates.")
            for cand in candidates:
                # Add to buffer if not already present
                if not any(b['symbol'] == cand['symbol'] for b in signal_buffer):
                    cand['added_at'] = datetime.now()
                    signal_buffer.append(cand)
                    print(f"Added {cand['symbol']} to buffer (at {cand['added_at'].strftime('%H:%M')}). Score: {cand['score']:.2f}")
        
        # 5. Buffer Logic
        # Condition A: Buffer satisfied (>= 2 signals)
        if len(signal_buffer) >= 2:
            print(f"Buffer satisfied ({len(signal_buffer)} >= 2). Selecting best...")
            trader.execute_best_candidate(signal_buffer)
            signal_buffer = []

        # Condition B: Timeout Logic (Force execute if waiting > 15 mins)
        elif len(signal_buffer) == 1:
            elapsed_min = (datetime.now() - signal_buffer[0]['added_at']).total_seconds() / 60
            if elapsed_min > 15:
                print(f"⏰ Timeout reached ({elapsed_min:.1f}m > 15m). Force executing single candidate.")
                trader.execute_best_candidate(signal_buffer)
                signal_buffer = []
            else:
                print(f"Waiting for more signals... ({len(signal_buffer)}/2) - Waiting for {elapsed_min:.1f}m")
        
        else:
             print("Waiting for signals...")

        logging.info("Cycle Completed.")
        
    except Exception as e:
        logging.error(f"Error in cycle: {e}")
        print(f"Error: {e}")

def start_auto_trader():
    print("🚀 Auto Trader Started! Running fully autonomous.")
    logging.info("Auto Trader Started.")
    
    # Run immediately once
    job()
    
    # Schedule every 1 minute
    schedule.every(1).minutes.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    start_auto_trader()
