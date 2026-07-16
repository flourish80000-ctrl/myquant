import sqlite3

DB_FILE = "trades.db"


def init_db():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            market_id INTEGER,
            signal_type TEXT,
            signal_strength REAL,
            market_price REAL,
            price_move_pct REAL
        )
    """)

    # MIGRATION: add new columns only if they're missing.
    # Old rows automatically get the DEFAULT — that's our backfill.
    existing = [row[1] for row in cur.execute("PRAGMA table_info(trades)")]

    if "venue" not in existing:
        cur.execute("ALTER TABLE trades ADD COLUMN venue TEXT DEFAULT 'predict.fun'")
        print("migration: added 'venue' column (old rows tagged 'predict.fun')")

    if "symbol" not in existing:
        # Hyperliquid has no numeric market_id — it uses names like 'BTC'.
        cur.execute("ALTER TABLE trades ADD COLUMN symbol TEXT")
        print("migration: added 'symbol' column")

    conn.commit()
    conn.close()


def log_signal(timestamp, market_id, signal_type, signal_strength,
               market_price, price_move_pct, venue="predict.fun", symbol=None):
    conn = sqlite3.connect(DB_FILE, timeout=30)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trades
        (timestamp, market_id, signal_type, signal_strength,
         market_price, price_move_pct, venue, symbol)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, market_id, signal_type, signal_strength,
          market_price, price_move_pct, venue, symbol))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    conn = sqlite3.connect(DB_FILE, timeout=30)
    cur = conn.cursor()
    print("--- venue tally ---")
    for row in cur.execute("SELECT venue, COUNT(*) FROM trades GROUP BY venue"):
        print(row)
    conn.close()