import requests
import json
import time
from data_store import MarketDataStore

# Your ID card. Replace the text below with your real key.
from config import API_KEY

headers = {"x-api-key": API_KEY}

# Load the watchlist — WHAT the scanner watches.
with open("watchlist.json") as f:
    watchlist = json.load(f)

# The order book lives at the MARKET level. Collect each market once.
markets = {}
for entry in watchlist:
    markets[entry["market_id"]] = entry["question"]

# The scanner's memory is now a proper filing cabinet, not a loose note.
store = MarketDataStore()


# A small helper: compute the mid price from a book, or None if a side is empty.
def mid_of(book):
    asks = book["asks"]
    bids = book["bids"]
    if not asks or not bids:
        return None
    best_ask = min(offer[0] for offer in asks)
    best_bid = max(offer[0] for offer in bids)
    return (best_ask + best_bid) / 2


print("Poller starting. Watching", len(markets), "markets. Press Ctrl+C to stop.")

while True:
    for market_id, question in markets.items():
        url = f"https://api.predict.fun/v1/markets/{market_id}/orderbook"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print("problem", response.status_code, "on:", question[:40])
            continue

        new_book = response.json()["data"]

        # Pull the OLD book from the cabinet BEFORE filing the new one.
        old_book = store.get_latest(market_id)

        # File the fresh book into the cabinet.
        store.record(market_id, new_book)

        new_mid = mid_of(new_book)
        old_mid = mid_of(old_book) if old_book else None

        if new_mid is None:
            print("empty book on:", question[:40])
            continue

        if old_mid is None:
            change = 0.0
        else:
            change = new_mid - old_mid

        print(question[:40], "| old", old_mid, "| new", round(new_mid, 3),
              "| change", round(change, 4))

    print("--- round done, resting 10 seconds ---")
    time.sleep(10)