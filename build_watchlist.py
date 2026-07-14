import requests
import json
import time

# Your ID card. Replace the text below with your real key.
from config import API_KEY

KEYWORDS = ["up or down"]
MAX_MARKETS = 12          # never watch more markets than we can poll well

BASE_URL = "https://api.predict.fun/v1/markets"
headers = {"x-api-key": API_KEY}


# Fetch one page. If the network hiccups, wait and retry (up to 3 times).
def get_page(cursor):
    params = {"status": "OPEN"}
    if cursor:
        params["after"] = cursor
    for attempt in range(3):
        try:
            response = requests.get(BASE_URL, headers=headers, params=params, timeout=15)
            return response.json()
        except requests.exceptions.RequestException as e:
            print("  network hiccup, retrying...", e.__class__.__name__)
            time.sleep(2)
    return None


watchlist = []
seen_markets = set()
cursor = None
page = 0

while True:
    data = get_page(cursor)
    if data is None:
        print("Gave up on a page after repeated failures — stopping here.")
        break

    markets_page = data.get("data", [])
    if not markets_page:
        break

    for market in markets_page:
        text = (str(market["question"]) + " "
                + str(market["title"]) + " "
                + str(market["categorySlug"])).lower()
        for word in KEYWORDS:
            if word in text and market["id"] not in seen_markets:
                seen_markets.add(market["id"])
                for outcome in market["outcomes"]:
                    watchlist.append({
                        "market_id": market["id"],
                        "on_chain_id": outcome["onChainId"],
                        "outcome_name": outcome["name"],
                        "question": market["question"],
                    })
                break

    page += 1

    # Stop as soon as we have enough markets to watch.
    if len(seen_markets) >= MAX_MARKETS:
        print("Reached", MAX_MARKETS, "markets — enough to watch well.")
        break

    cursor = data.get("cursor")
    if not cursor:
        break
    if page >= 100:
        break
    time.sleep(0.4)


print("Scanned", page, "pages. Markets in watchlist:", len(seen_markets))
print("Watchlist entries:", len(watchlist))

with open("watchlist.json", "w") as f:
    json.dump(watchlist, f, indent=2)

print("Saved to watchlist.json")