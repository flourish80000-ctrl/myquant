import sqlite3

DB_FILE = "trades.db"

# The discipline line: fewer verdicts than this = NOT enough to tune. Noise.
MIN_SAMPLE = 20

conn = sqlite3.connect(DB_FILE)

total = conn.execute("SELECT COUNT(*) FROM resolutions").fetchone()[0]
wins = conn.execute("SELECT COUNT(*) FROM resolutions WHERE verdict = 'WIN'").fetchone()[0]
losses = conn.execute("SELECT COUNT(*) FROM resolutions WHERE verdict = 'LOSS'").fetchone()[0]

print("=== Resolution Analysis ===")
print("Total resolved verdicts:", total)
print("Wins:", wins, "| Losses:", losses)

if total > 0:
    win_rate = wins / total * 100
    print("Win rate:", round(win_rate, 1), "%")
else:
    print("Win rate: n/a (no verdicts yet)")

print()

# The honest gate: do we even have the right to tune?
if total < MIN_SAMPLE:
    print(f"VERDICT: INSUFFICIENT DATA ({total} verdicts, need at least {MIN_SAMPLE}).")
    print("Do NOT tune thresholds yet. Numbers this thin are noise, not evidence.")
    print("Keep the scanner running. Let real verdicts accumulate. Patience.")
else:
    print(f"VERDICT: {total} verdicts is enough to START studying patterns.")
    print("Now you may compare win rates and propose ONE change, defended with numbers.")

conn.close()