import requests
import time

# CoinGecko's official names for our three coins.
COIN_IDS = {
    "bitcoin": "bitcoin",
    "ethereum": "ethereum",
    "bnb": "binancecoin",
}


# Which coin is this market about? Read it from the question text.
def coin_from_question(question):
    q = question.lower()
    if "bitcoin" in q or "btc" in q:
        return "bitcoin"
    if "ethereum" in q or "eth" in q:
        return "ethereum"
    if "bnb" in q:
        return "bnb"
    return None


# Which way is the wind blowing for this coin right now?
# "Up" if price is above its recent average, "Down" if below. None if unsure.
def direction_for(coin_key):
    coin_id = COIN_IDS.get(coin_key)
    if coin_id is None:
        return None
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": "1"}
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.status_code != 200:
                return None
            prices = [point[1] for point in r.json().get("prices", [])]
            if len(prices) < 21:
                return None
            current = prices[-1]
            average = sum(prices[-21:-1]) / 20   # average of the previous 20
            return "Up" if current > average else "Down"
        except requests.exceptions.RequestException:
            time.sleep(2)
    return None


# Self-test: check the wind for all three coins.
if __name__ == "__main__":
    for q in ["Bitcoin Up or Down", "Ethereum Up or Down", "BNB Up or Down"]:
        coin = coin_from_question(q)
        print(q, "->", coin, "->", direction_for(coin))