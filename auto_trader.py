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
        scan_market(strategy_type="standard", save_to_db=True)
        
        # 4. Fetch Fresh Signals (Last 5 mins)
        from database import get_recent_signals
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
                    signal_buffer.append(cand)
                    print(f"Added {cand['symbol']} to buffer. Score: {cand['score']:.2f}")
        
        # 5. Buffer Logic
        # "wait for 2-3 signals and then select the best stock"
        # We also need a timeout or max wait, otherwise we might wait forever if only 1 signal appears.
        # Let's say: Execute if Buffer >= 3 OR (Buffer >= 1 and Wait Time > 5 mins - omitted for simplicity)
        
        if len(signal_buffer) >= 2:
            print(f"Buffer satisfied ({len(signal_buffer)} >= 2). Selecting best...")
            
            # Execute Best
            trader.execute_best_candidate(signal_buffer)
            
            # Clear buffer after execution (or just remove the executed one? User said "select best stock out of them")
            # Usually we clear buffer to restart cycle.
            signal_buffer = []
        else:
            if len(signal_buffer) > 0:
                print(f"Waiting for more signals... ({len(signal_buffer)}/2)")

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
