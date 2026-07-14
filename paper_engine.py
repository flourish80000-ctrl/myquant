import requests
import json
import time
from datetime import datetime
from signal_engine import check_liquidity, check_tradeable, best_prices
from database import init_db, log_signal
from paper_trader import init_positions, open_position
from compass import coin_from_question, direction_for
from config import API_KEY

headers = {"x-api-key": API_KEY}

init_db()
init_positions()

with open("watchlist.json") as f:
    watchlist = json.load(f)

markets = {}
for entry in watchlist:
    if entry["market_id"] not in markets:
        markets[entry["market_id"]] = entry["question"]


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


print("Compass engine starting. Watching", len(markets),
      "markets. Press Ctrl+C to stop.")

while True:
    # Check the wind ONCE per round for each coin (saves API calls).
    wind = {
        "bitcoin": direction_for("bitcoin"),
        "ethereum": direction_for("ethereum"),
        "bnb": direction_for("bnb"),
    }
    print("compass this round:", wind)

    for market_id, question in markets.items():
        data = fetch_book(market_id)
        if data is None:
            continue

        book = data["data"]
        trap = check_liquidity(book)
        healthy = check_tradeable(book)

        prices = best_prices(book)
        market_price = round((prices[0] + prices[1]) / 2, 3) if prices else 0.0
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if healthy:
            # THE COMPASS: bet the way the wind blows, not always "Up".
            coin = coin_from_question(question)
            direction = wind.get(coin)
            if direction is None:
                continue  # compass unsure — skip, never guess
            log_signal(timestamp, market_id, "HEALTHY", 0.0, market_price, 0.0)
            open_position(timestamp, market_id, direction, market_price)
        elif trap:
            log_signal(timestamp, market_id, "TRAP", 0.0, market_price, 0.0)

    print("--- round done, resting 15 seconds ---")
    time.sleep(15)