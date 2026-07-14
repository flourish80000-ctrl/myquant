import requests
import json
import time
from datetime import datetime
from data_store import MarketDataStore
from signal_engine import check_liquidity, check_tradeable, best_prices
from database import init_db, log_signal

# Your ID card. Replace the text below with your real key.
from config import API_KEY

headers = {"x-api-key": API_KEY}

# Make sure the diary exists before we write to it.
init_db()

# Load the watchlist and collect each market once.
with open("watchlist.json") as f:
    watchlist = json.load(f)

markets = {}
for entry in watchlist:
    markets[entry["market_id"]] = entry["question"]

# Memory: remembers each market's last mid price, for the move calculation.
store = MarketDataStore()

print("Engine starting. Watching", len(markets),
      "markets. Logging to trades.db. Press Ctrl+C to stop.")

while True:
    for market_id, question in markets.items():
        url = f"https://api.predict.fun/v1/markets/{market_id}/orderbook"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print("problem", response.status_code, "on:", question[:35])
            continue

        book = response.json()["data"]

        # Run both detectors on the live book.
        trap = check_liquidity(book)
        healthy = check_tradeable(book)

        if trap:
            signal_type = "TRAP"
            reason = trap
        elif healthy:
            signal_type = "HEALTHY"
            reason = healthy
        else:
            continue  # no signal fired — nothing to log

        # Work out the price and the spread for the diary.
        prices = best_prices(book)
        if prices is None:
            market_price = 0.0
            spread = 0.0
        else:
            best_bid, best_ask = prices
            market_price = round((best_bid + best_ask) / 2, 3)
            spread = round(best_ask - best_bid, 4)

        # Compare with memory to get the price move percent (cold start = 0.0).
        old_price = store.get_latest(market_id)
        store.record(market_id, market_price)
        if old_price is None or old_price == 0:
            price_move_pct = 0.0
        else:
            price_move_pct = round((market_price - old_price) / old_price * 100, 3)

        # Stamp the moment and write the row into the diary.
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_signal(timestamp, market_id, signal_type, spread, market_price, price_move_pct)

        print(timestamp, "|", signal_type, "|", question[:30], "|", reason)

    print("--- round logged, resting 15 seconds ---")
    time.sleep(15)