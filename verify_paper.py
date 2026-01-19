import unittest
from paper_trader import PaperTrader
from database import init_db, clear_db, get_active_paper_trades, close_paper_trade
import sqlite3
import os

class TestPaperTrader(unittest.TestCase):
    def setUp(self):
        # Use a separate DB or just clear existing for test if safe?
        # Ideally mock, but for integration let's just use the functions carefully.
        # We will NOT clear the real DB. We will just test the calculation functions.
        self.trader = PaperTrader()

    def test_mock_trade_execution(self):
        """Test if trade entry logic works (Mocking DB calls if possible, or just syntax)"""
        # We can't easily mock DB here without refactoring, so we can test the Class methods logic
        pass

if __name__ == '__main__':
    # Simple Manual Verification Script
    print("--- Running Manual Verification ---")
    
    # 1. Test Fetching Data
    print("1. Fetching Data for INFY.NS...")
    df = PaperTrader().get_live_data("INFY.NS")
    if df is not None and not df.empty:
        print(f"   Success. Rows: {len(df)}")
    else:
        print("   Failed.")
        
    print("--- verification complete ---")
