import requests
import json
import time
from datetime import datetime
from signal_engine import check_liquidity, check_tradeable, best_prices
from database import init_db, log_signal
from paper_trader import init_positions, open_position

# Your ID card. Replace the text below with your real key.
from config import API_KEY

headers = {"x-api-key": API_KEY}

init_db()
init_positions()

with open("watchlist.json") as f:
    watchlist = json.load(f)

markets = {}
for entry in watchlist:
    if entry["market_id"] not in markets:
        markets[entry["market_id"]] = (entry["question"], entry["outcome_name"])


# Fetch a market's order book. If the network hiccups, retry (up to 3 times).
# Returns the JSON, or None if it truly can't get through this round.
def fetch_book(market_id):
    url = f"https://api.predict.fun/v1/markets/{market_id}/orderbook"
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                return None
            return response.json()
        except requests.exceptions.RequestException:
            time.sleep(2)
    return None


print("Paper engine starting. Watching", len(markets),
      "markets. Press Ctrl+C to stop.")

while True:
    for market_id, (question, outcome_name) in markets.items():
        data = fetch_book(market_id)
        if data is None:
            continue  # skip this market this round; don't crash the engine

        book = data["data"]
        trap = check_liquidity(book)
        healthy = check_tradeable(book)

        prices = best_prices(book)
        market_price = round((prices[0] + prices[1]) / 2, 3) if prices else 0.0
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if healthy:
            log_signal(timestamp, market_id, "HEALTHY", 0.0, market_price, 0.0)
            open_position(timestamp, market_id, outcome_name, market_price)
        elif trap:
            log_signal(timestamp, market_id, "TRAP", 0.0, market_price, 0.0)

    print("--- round done, resting 15 seconds ---")
    time.sleep(15)