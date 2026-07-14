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
    conn.commit()
    conn.close()


def log_signal(timestamp, market_id, signal_type,
               signal_strength, market_price, price_move_pct):
    conn = sqlite3.connect(DB_FILE, timeout=30)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trades
        (timestamp, market_id, signal_type, signal_strength, market_price, price_move_pct)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (timestamp, market_id, signal_type, signal_strength, market_price, price_move_pct))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    log_signal("2026-01-01 12:00:00", 999999, "TRAP", 0.98, 0.5, 0.0)

    conn = sqlite3.connect(DB_FILE, timeout=30)
    cur = conn.cursor()
    for row in cur.execute("SELECT * FROM trades"):
        print(row)
    conn.close()