# ---- Starting thresholds. EDUCATED GUESSES. We tune these later with data. ----
MAX_SPREAD = 0.10   # a spread wider than this = too wide to trade safely
MIN_DEPTH = 100     # fewer total shares than this = too thin


# Helper: best bid and best ask from a book, or None if a side is empty.
def best_prices(book):
    asks = book["asks"]
    bids = book["bids"]
    if not asks or not bids:
        return None
    best_bid = max(offer[0] for offer in bids)
    best_ask = min(offer[0] for offer in asks)
    return best_bid, best_ask


# Helper: total shares available on both sides = our rough "depth".
def total_depth(book):
    return (sum(offer[1] for offer in book["bids"])
            + sum(offer[1] for offer in book["asks"]))


# DETECTOR 1: bark "TRAP" on a bad market. Returns a reason, or None if fine.
def check_liquidity(book):
    prices = best_prices(book)
    if prices is None:
        return "TRAP: one side of the book is empty"
    best_bid, best_ask = prices
    spread = best_ask - best_bid
    depth = total_depth(book)
    if spread > MAX_SPREAD:
        return f"TRAP: spread {round(spread, 3)} too wide"
    if depth < MIN_DEPTH:
        return f"TRAP: depth {depth} too thin"
    return None


# DETECTOR 2: bark "HEALTHY" on a good market. Returns a reason, or None.
def check_tradeable(book):
    prices = best_prices(book)
    if prices is None:
        return None
    best_bid, best_ask = prices
    spread = best_ask - best_bid
    depth = total_depth(book)
    if spread <= MAX_SPREAD and depth >= MIN_DEPTH:
        return f"HEALTHY: spread {round(spread, 3)}, depth {depth}"
    return None


# ---- Self-test: one trap market, one healthy market. ----
if __name__ == "__main__":
    trap_book = {"asks": [[0.99, 300]], "bids": [[0.01, 200]]}
    healthy_book = {"asks": [[0.52, 500]], "bids": [[0.49, 500]]}

    print("trap    ->", check_liquidity(trap_book))
    print("trap    ->", check_tradeable(trap_book))
    print("healthy ->", check_liquidity(healthy_book))
    print("healthy ->", check_tradeable(healthy_book))