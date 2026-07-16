import requests
import time
from datetime import datetime
from signal_engine import check_liquidity, check_tradeable, best_prices
from database import init_db, log_signal
from paper_trader import init_positions, open_position
from compass import coin_from_question, direction_for
from config import API_KEY

headers = {"x-api-key": API_KEY}
BASE_URL = "https://api.predict.fun/v1/markets"

KEYWORDS = ["up or down"]
MAX_MARKETS = 12            # only watch what we can watch well
REFRESH_ROUNDS = 20         # rebuild the market list every ~5 min
WIND_REFRESH_ROUNDS = 4     # check the wind once a minute (not every round)

init_db()
init_positions()


def get_page(cursor):
    params = {"status": "OPEN"}
    if cursor:
        params["after"] = cursor
    for attempt in range(3):
        try:
            r = requests.get(BASE_URL, headers=headers, params=params, timeout=15)
            return r.json()
        except requests.exceptions.RequestException:
            time.sleep(2)
    return None


# Ask Predict.fun what is open RIGHT NOW. Returns {market_id: question}.
def fetch_current_markets():
    found = {}
    cursor = None
    page = 0
    while True:
        data = get_page(cursor)
        if data is None:
            break
        page_markets = data.get("data", [])
        if not page_markets:
            break
        for m in page_markets:
            text = (str(m["question"]) + " " + str(m["title"]) + " "
                    + str(m["categorySlug"])).lower()
            for word in KEYWORDS:
                if word in text and m["id"] not in found:
                    found[m["id"]] = m["question"]
                    break
        page += 1
        if len(found) >= MAX_MARKETS:
            break
        cursor = data.get("cursor")
        if not cursor or page >= 100:
            break
        time.sleep(0.4)
    return found


def fetch_book(market_id):
    url = f"{BASE_URL}/{market_id}/orderbook"
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                return None
            return response.json()
        except requests.exceptions.RequestException:
            time.sleep(2)
    return None


print("Self-refreshing compass engine starting. Press Ctrl+C to stop.")

markets = fetch_current_markets()
print("Loaded", len(markets), "live markets.")
wind = {}
rounds = 0

while True:
    # Every REFRESH_ROUNDS, find what's live now.
    if rounds > 0 and rounds % REFRESH_ROUNDS == 0:
        markets = fetch_current_markets()
        print(">>> refreshed watchlist:", len(markets), "live markets")

    # Check the wind once a minute — the wind doesn't change every 15 seconds.
    if rounds % WIND_REFRESH_ROUNDS == 0:
        wind = {
            "bitcoin": direction_for("bitcoin"),
            "ethereum": direction_for("ethereum"),
            "bnb": direction_for("bnb"),
        }
        print("compass:", wind)

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
            coin = coin_from_question(question)
            direction = wind.get(coin)
            if direction is None:
                continue
            log_signal(timestamp, market_id, "HEALTHY", 0.0, market_price, 0.0)
            open_position(timestamp, market_id, direction, market_price)
        elif trap:
            log_signal(timestamp, market_id, "TRAP", 0.0, market_price, 0.0)

    rounds += 1
    print("--- round", rounds, "done, resting 15 seconds ---")
    time.sleep(15)