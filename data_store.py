class MarketDataStore:
    # __init__ runs ONCE when a new cabinet is built. It sets up empty drawers.
    def __init__(self):
        # self.latest_book = MY drawers. One drawer per market_id.
        self.latest_book = {}

    # HANDLE 1: file the newest order book into a market's drawer.
    def record(self, market_id, book):
        self.latest_book[market_id] = book

    # HANDLE 2: pull the latest book out of a market's drawer.
    # Returns None if nothing has been filed there yet.
    def get_latest(self, market_id):
        return self.latest_book.get(market_id)


# This test only runs when you run data_store.py DIRECTLY.
# It is skipped when another file borrows the class. (More on that next step.)
if __name__ == "__main__":
    # Build one cabinet from the blueprint.
    store = MarketDataStore()

    # Ask for market 695568 BEFORE filing anything. Should be None (empty drawer).
    print("Before filing:", store.get_latest(695568))

    # File a fake order book into that market's drawer.
    store.record(695568, {"asks": [[0.49, 100]], "bids": [[0.01, 50]]})

    # Ask again. Now the drawer holds our book.
    print("After filing:", store.get_latest(695568))