import sqlite3
from datetime import datetime
import os

DB_FILE = "signals.db"

def init_db():
    """Initializes the database and creates the table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            signal_date TEXT NOT NULL,
            trend_prediction TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            signal_strength TEXT DEFAULT 'Standard'
        )
    ''')
    conn.commit()
    conn.close()
    
    # Run migration to ensure column exists in old DBs
    migrate_db()
    init_portfolio_db()

def init_portfolio_db():
    """Creates the portfolio table."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            entry_price REAL,
            quantity INTEGER DEFAULT 1,
            status TEXT DEFAULT 'WATCHLIST', -- WATCHLIST, OPEN, CLOSED
            added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

def migrate_db():
    """Adds missing columns if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Add trend_prediction column
    try:
        c.execute("ALTER TABLE signals ADD COLUMN trend_prediction TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    # Add signal_strength column
    try:
        c.execute("ALTER TABLE signals ADD COLUMN signal_strength TEXT DEFAULT 'Standard'")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()

# --- Portfolio Functions ---

def add_to_portfolio(symbol, price, status='WATCHLIST', notes=''):
    """Adds a stock to the portfolio/watchlist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Check if already exists
    c.execute("SELECT id FROM portfolio WHERE symbol = ? AND status != 'CLOSED'", (symbol,))
    if c.fetchone():
        conn.close()
        return False # Already exists
        
    c.execute('''
        INSERT INTO portfolio (symbol, entry_price, status, notes)
        VALUES (?, ?, ?, ?)
    ''', (symbol, price, status, notes))
    conn.commit()
    conn.close()
    return True

def get_portfolio():
    """Fetches all active portfolio items."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM portfolio WHERE status != 'CLOSED' ORDER BY added_date DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def close_position(symbol):
    """Marks a position as CLOSED."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE portfolio SET status = 'CLOSED' WHERE symbol = ?", (symbol,))
    conn.commit()
    conn.close()

def remove_from_portfolio(symbol):
    """Permanently removes from portfolio."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM portfolio WHERE symbol = ?", (symbol,))
    conn.commit()
    conn.close()

# --- Signal Functions ---

def add_signal(symbol, price, signal_date, trend_prediction="Neutral", timestamp=None, signal_strength="Standard"):
    """Adds a new buy signal to the database, including signal strength."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Check if signal already exists for today to avoid duplicates
    c.execute('''
        SELECT id FROM signals 
        WHERE symbol = ? AND signal_date = ?
    ''', (symbol, signal_date))
    
    if not c.fetchone():
        if timestamp:
            c.execute('''
                INSERT INTO signals (symbol, price, signal_date, trend_prediction, timestamp, signal_strength)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (symbol, price, signal_date, trend_prediction, timestamp, signal_strength))
        else:
            c.execute('''
                INSERT INTO signals (symbol, price, signal_date, trend_prediction, signal_strength)
                VALUES (?, ?, ?, ?, ?)
            ''', (symbol, price, signal_date, trend_prediction, signal_strength))
            
        conn.commit()
        # print(f"Saved signal for {symbol} to DB.")
    
    conn.close()

def get_recent_signals(limit=50):
    """Fetches the most recent signals."""
    conn = sqlite3.connect(DB_FILE)
    # Return as dicts
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT symbol, price, signal_date, trend_prediction, timestamp, signal_strength 
        FROM signals 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def clear_db():
    """Clears all signals (useful for testing)."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM signals')
    conn.commit()
    conn.close()

def remove_signal(symbol):
    """Removes a signal from the database (e.g., if Sell signal triggered)."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM signals WHERE symbol = ?', (symbol,))
    conn.commit()
    conn.close()

# Initialize on module load
init_db()
