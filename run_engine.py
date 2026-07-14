import requests
import json
from signal_engine import check_liquidity, check_tradeable

# Your ID card. Replace the text below with your real key.
from config import API_KEY

headers = {"x-api-key": API_KEY}

# Load the watchlist and collect each market once.
with open("watchlist.json") as f:
    watchlist = json.load(f)

markets = {}
for entry in watchlist:
    markets[entry["market_id"]] = entry["question"]

print("Scanning", len(markets), "markets...")
print()

for market_id, question in markets.items():
    url = f"https://api.predict.fun/v1/markets/{market_id}/orderbook"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("problem", response.status_code, "on:", question[:40])
        continue

    book = response.json()["data"]

    # Run BOTH detectors on the live book.
    trap = check_liquidity(book)
    healthy = check_tradeable(book)

    # Whichever one barked, show it. If both are silent, say so.
    if trap:
        print(question[:45], "->", trap)
    elif healthy:
        print(question[:45], "->", healthy)
    else:
        print(question[:45], "-> (no signal)")

print()
print("--- scan done ---")