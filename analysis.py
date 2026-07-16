import sqlite3
import math

DB_FILE = "trades.db"

# The bar YOU set, while you are still honest. Your future self cannot lower it
# without editing this file — and if he does that, he'll know exactly what he did.
MIN_SAMPLE = 100     # minimum compass verdicts before we judge at all
MIN_DOWN = 30        # minimum Down bets — proves BOTH market regimes were tested

conn = sqlite3.connect(DB_FILE, timeout=30)
rows = list(conn.execute(
    "SELECT outcome_held, verdict FROM resolutions WHERE market_id > 760000"
))
conn.close()

n = len(rows)
wins = sum(1 for r in rows if r[1] == "WIN")
downs = [r for r in rows if r[0] == "Down"]
ups = [r for r in rows if r[0] == "Up"]

print("=== COMPASS EDGE REPORT ===")
print("total verdicts:", n, "| wins:", wins, "| losses:", n - wins)
print("Up-bets:", len(ups), "| Down-bets:", len(downs))

if n == 0:
    print("No verdicts yet. Keep the engine running.")
    raise SystemExit

p = wins / n
se = math.sqrt(p * (1 - p) / n)      # how much luck could be moving this number
low = p - 1.96 * se                  # pessimistic edge of the range
high = p + 1.96 * se                 # optimistic edge of the range

print(f"win rate: {round(p * 100, 1)}%")
print(f"95% confidence range: {round(low * 100, 1)}% to {round(high * 100, 1)}%")
print()

check_sample = n >= MIN_SAMPLE
check_down = len(downs) >= MIN_DOWN
check_edge = low > 0.50

print("  " + ("PASS" if check_sample else "FAIL"),
      f"- enough verdicts ({n}/{MIN_SAMPLE})")
print("  " + ("PASS" if check_down else "FAIL"),
      f"- enough Down bets ({len(downs)}/{MIN_DOWN})")
print("  " + ("PASS" if check_edge else "FAIL"),
      f"- range clears 50% (bottom is {round(low * 100, 1)}%)")
print()

if check_sample and check_down and check_edge:
    print("VERDICT: your data supports an edge claim.")
    print("Even so: going live is YOUR decision alone, with money you can lose.")
else:
    print("VERDICT: DATA NOT COMPLETE. No edge claim. No live trading.")
    print("Keep the engine running. Come back later.")