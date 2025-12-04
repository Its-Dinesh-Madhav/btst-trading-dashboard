import sqlite3
import pandas as pd

def check_db():
    conn = sqlite3.connect("signals.db")
    c = conn.cursor()
    
    # Count signals
    c.execute("SELECT count(*) FROM signals")
    count = c.fetchone()[0]
    print(f"Total Signals in DB: {count}")
    
    if count > 0:
        print("\nLast 10 Signals:")
        df = pd.read_sql_query("SELECT * FROM signals ORDER BY timestamp DESC LIMIT 10", conn)
        print(df)
    else:
        print("Database is empty.")
        
    conn.close()

if __name__ == "__main__":
    check_db()
