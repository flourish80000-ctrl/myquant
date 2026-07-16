import requests
import time
from data_store import MarketDataStore

# Hyperliquid: ONE url, POST, and we say what we want in the body.
URL = "https://api.hyperliquid.xyz/info"
COINS = ["BTC", "ETH", "SOL", "BNB",
  "DOGE",]

# The SAME memory class you built in Class 6 — the pattern transfers.
store = MarketDataStore()


def fetch_all_mids():
    for attempt in range(3):
        try:
            r = requests.post(URL, json={"type": "allMids"}, timeout=15)
            if r.status_code != 200:
                return None
            return r.json()
        except requests.exceptions.RequestException:
            time.sleep(2)
    return None


print("Hyperliquid poller starting. Watching", len(COINS), "coins. Ctrl+C to stop.")

while True:
    mids = fetch_all_mids()
    if mids is None:
        print("could not reach Hyperliquid - retrying next round")
        time.sleep(15)
        continue

    for coin in COINS:
        price_text = mids.get(coin)
        if price_text is None:
            print("  no price for", coin)
            continue

        # NEW FAILURE MODE: Hyperliquid sends prices as TEXT, not numbers.
        price = float(price_text)

        old = store.get_latest(coin)
        store.record(coin, price)
        change = 0.0 if old is None else price - old

        print(f"  {coin}: {price} | change {round(change, 4)}")

    print("--- round done, resting 15 seconds ---")
    time.sleep(15)