import requests
from config import API_KEY

# The kitchen's address for the markets menu
url = "https://api.predict.fun/v1/markets"

# The note attached to our order: our ID card
headers = {"x-api-key": API_KEY}

# Our actual order: only OPEN markets. Never bark at ghosts.
params = {"status": "OPEN"}

# Send the waiter. Bring back the response.
response = requests.get(url, headers=headers, params=params)
print("Status code:", response.status_code)

# Unpack the JSON container into something Python can walk through.
data = response.json()

# The markets live in a list called "data".
# "for" means: do the next line once FOR each market in that list.
for market in data["data"][:10]:
    print("-", market["question"])