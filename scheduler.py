import schedule
import time
import subprocess
import sys
from datetime import datetime

def run_scanner():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⏰ Starting Scheduled Scan...")
    try:
        # Run the scanner script
        subprocess.run([sys.executable, "scanner.py"], check=True)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Scan Complete.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running scanner: {e}")

def start_scheduler():
    print("--- 🗓️ Algo Scanner Auto-Scheduler Started ---")
    print("Scheduled times: 09:15, 12:00, 15:15")
    
    # Schedule tasks
    schedule.every().day.at("09:15").do(run_scanner)
    schedule.every().day.at("12:00").do(run_scanner)
    schedule.every().day.at("15:15").do(run_scanner)
    
    # Also run once immediately on start (optional, good for testing)
    # run_scanner() 
    
    while True:
        schedule.run_pending()
        time.sleep(60) # Check every minute

if __name__ == "__main__":
    start_scheduler()
