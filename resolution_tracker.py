import requests
import sqlite3
import time
from datetime import datetime

# Your ID card. Replace the text below with your real key.
from config import API_KEY

headers = {"x-api-key": API_KEY}
DB_FILE = "trades.db"


def init_resolutions():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS resolutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checked_at TEXT,
            market_id INTEGER,
            outcome_held TEXT,
            winning_outcome TEXT,
            verdict TEXT
        )
    """)
    conn.commit()
    conn.close()


def record_verdict(market_id, outcome_held, winning_outcome, verdict):
    conn = sqlite3.connect(DB_FILE, timeout=30)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO resolutions
        (checked_at, market_id, outcome_held, winning_outcome, verdict)
        VALUES (?, ?, ?, ?, ?)
    """, (ts, market_id, outcome_held, winning_outcome, verdict))
    conn.execute("""
        UPDATE paper_positions SET status = 'CLOSED'
        WHERE market_id = ? AND status = 'OPEN'
    """, (market_id,))
    conn.commit()
    conn.close()


# Fetch one market. If the network hiccups, retry (up to 3 times).
def fetch_market(market_id):
    url = f"https://api.predict.fun/v1/markets/{market_id}"
    for attempt in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code != 200:
                return None
            return r.json()
        except requests.exceptions.RequestException:
            time.sleep(2)
    return None


def check_all():
    init_resolutions()

    conn = sqlite3.connect(DB_FILE, timeout=30)
    open_positions = list(conn.execute(
        "SELECT market_id, outcome_name FROM paper_positions WHERE status = 'OPEN'"
    ))
    conn.close()

    print("Checking", len(open_positions), "open positions for resolution...")

    for market_id, outcome_held in open_positions:
        data = fetch_market(market_id)
        if data is None:
            print("  could not reach market", market_id, "- will retry next run")
            continue

        market = data["data"]

        if market.get("status") != "RESOLVED":
            print(f"  market {market_id}: still open - no verdict yet (patience)")
            continue

        winning_outcome = None
        for o in market.get("outcomes", []):
            if o.get("status") == "WON":
                winning_outcome = o.get("name")

        verdict = "WIN" if winning_outcome == outcome_held else "LOSS"
        record_verdict(market_id, outcome_held, winning_outcome, verdict)
        print(f"  market {market_id}: RESOLVED - winner '{winning_outcome}', "
              f"we held '{outcome_held}' -> {verdict}")


if __name__ == "__main__":
    check_all()