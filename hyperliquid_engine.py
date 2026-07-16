import requests
import time
from datetime import datetime
from signal_engine import best_prices          # reuse the brain's helper
from database import init_db, log_signal
from data_store import MarketDataStore         # reuse the memory (Class 6!)

URL = "https://api.hyperliquid.xyz/info"
COINS = ["BTC", "ETH", "SOL", "BNB", "DOGE"]
VENUE = "hyperliquid"

# EDUCATED GUESSES for THIS venue. Prices here are dollars, not 0-1 probabilities,
# so we measure the spread as a PERCENTAGE — comparable across coins and venues.
MAX_SPREAD_PCT = 0.001      # wider than 0.1% = too wide
MIN_NOTIONAL = 10000        # at least $10,000 of real orders resting

init_db()
store = MarketDataStore()


def fetch_book(coin):
    for attempt in range(3):
        try:
            r = requests.post(URL, json={"type": "l2Book", "coin": coin}, timeout=15)
            if r.status_code != 200:
                return None
            return r.json()
        except requests.exceptions.RequestException:
            time.sleep(2)
    return None


# THE ADAPTER: turn Hyperliquid's shape into the shape our engine already speaks.
def to_standard_book(hl_book):
    levels = hl_book.get("levels")
    if not levels or len(levels) < 2:
        return None
    bids = [[float(x["px"]), float(x["sz"])] for x in levels[0]]
    asks = [[float(x["px"]), float(x["sz"])] for x in levels[1]]
    return {"bids": bids, "asks": asks}


print("Hyperliquid engine starting. Logging to trades.db as venue =", VENUE)

while True:
    for coin in COINS:
        raw = fetch_book(coin)
        if raw is None:
            print("  could not reach", coin)
            continue

        book = to_standard_book(raw)
        if book is None:
            continue

        prices = best_prices(book)          # the SAME helper Predict.fun uses
        if prices is None:
            print("  empty book:", coin)
            continue

        best_bid, best_ask = prices
        mid = (best_bid + best_ask) / 2
        spread_pct = (best_ask - best_bid) / mid
        notional = (sum(p * s for p, s in book["bids"])
                    + sum(p * s for p, s in book["asks"]))

        # Same LOGIC as your Predict.fun detectors. Different NUMBERS.
        if spread_pct > MAX_SPREAD_PCT or notional < MIN_NOTIONAL:
            signal_type = "TRAP"
        else:
            signal_type = "HEALTHY"

        old = store.get_latest(coin)
        store.record(coin, mid)
        move = 0.0 if not old else round((mid - old) / old * 100, 4)

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_signal(ts, 0, signal_type, round(spread_pct, 6),
                   round(mid, 4), move, VENUE, coin)

        print(f"  {coin:5} {signal_type:8} spread {round(spread_pct*100, 4)}% "
              f"| mid {round(mid, 2)} | move {move}%")

    print("--- round done, resting 15 seconds ---")
    time.sleep(15)