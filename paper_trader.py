import sqlite3

DB_FILE = "trades.db"


def init_positions():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS paper_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            market_id INTEGER,
            outcome_name TEXT,
            entry_price REAL,
            status TEXT
        )
    """)
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS one_open_per_market
        ON paper_positions (market_id)
        WHERE status = 'OPEN'
    """)
    conn.commit()
    conn.close()


def open_position(timestamp, market_id, outcome_name, entry_price):
    conn = sqlite3.connect(DB_FILE, timeout=30)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO paper_positions
            (timestamp, market_id, outcome_name, entry_price, status)
            VALUES (?, ?, ?, ?, 'OPEN')
        """, (timestamp, market_id, outcome_name, entry_price))
        conn.commit()
        print("OPENED position on market", market_id, "-", outcome_name)
    except sqlite3.IntegrityError:
        print("SKIPPED market", market_id, "- already holding an open position")
    conn.close()


def show_positions():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    cur = conn.cursor()
    print("--- paper_positions ---")
    for row in cur.execute("SELECT * FROM paper_positions"):
        print(row)
    conn.close()


if __name__ == "__main__":
    init_positions()
    open_position("2026-01-01 12:00:00", 111, "France", 0.25)
    open_position("2026-01-01 12:00:05", 111, "France", 0.26)
    show_positions()