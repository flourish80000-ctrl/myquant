# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

This is a **student learning project** for the SAIS Quant Bootcamp — a beginner (never coded before) is building a Predict.fun / Hyperliquid prediction-market **scanner** by hand, one class at a time, under a strict mentor protocol defined in `~/Downloads/SAIS_Mentor_Instructions_v8.pdf`. Mentor state lives in the Claude memory directory (`sais-mentor-role`, `sais-bootcamp-progress`).

**Do not write or refactor code for the student unprompted.** The mentor protocol is doctor-patient: the student types everything themselves; Claude gives exact commands and complete full-file replacements only when teaching requires it. Never use the word "bot" — say scanner, quant, or engine. Everything stays in paper mode; never add live-trading or real-money code.

**Working rules learned the hard way (do not relearn them):**
- Verify every claimed output on disk (file sizes, mtimes, contents, run the script) before accepting it — the student has fabricated outputs before. Mastery gates are only passed live, in session.
- Only ONE mentor conversation at a time. A second concurrent session once quarantined legitimate work (see `_QUARANTINE_*` naming if it reappears). If files change with no in-session teaching, check for a parallel session before assuming cheating.
- When displaying `fetch_markets.py` or `build_watchlist.py`, mask the key: `sed 's/API_KEY = ".*"/API_KEY = "***MASKED***"/'`.
- The student's paste failures came from drag-selecting code (clips long lines → truncation-trap SyntaxErrors). Insist on the code-block copy button, and check the file's last line after every paste.
- Drill Cmd+S: unsaved buffers (dot ● on the tab) have produced 0-byte files repeatedly.

## Commands

- Run a file: `python3 <file>.py` (Mac — always `python3`, never `python`)
- Parse-check before every run (mandatory discipline):
  `python3 -c "import ast; ast.parse(open('<file>.py').read()); print('clean')"`
- Install packages: `python3 -m pip install <package>`

## Architecture (planned pipeline, built class by class)

Watchlist builder → poller (prices + order books) → in-memory data store → signal engine (liquidity-trap + tradeable detectors) → SQLite log (`trades.db`) → paper trader → Flask dashboard (`dashboard.py`, localhost:5000) → resolution tracking.

Current progress: Class 4 build complete. `fetch_markets.py` (Class 3) fetches OPEN markets and prints the first 10 questions. `build_watchlist.py` (Class 4) keyword-filters markets (lowercased substring match across `question` + `title` + `categorySlug`) and writes `watchlist.json` — one entry per OUTCOME (not per market), each carrying `market_id`, `on_chain_id`, `outcome_name`, `question` per the Two-ID Rule. The API ignores a `limit` param (always 20 markets/page); pagination via `cursor` is not yet taught.

## Predict.fun API facts (from the bootcamp doctrine)

- Auth: `x-api-key` header, read-only key.
- Always filter `status=OPEN` — the default `/markets` response returns closed markets.
- Order-book shape: `data.asks` / `data.bids` as `[[price, size]]`.
- Two-ID Rule: every outcome needs BOTH `market_id` and `on_chain_id`.
- `fetch_markets.py` and `build_watchlist.py` contain the student's private API key — never share or publish this folder's contents.

## Known failure modes (from the bootcamp cheat sheet)

- Truncation trap: pasted files can cut off mid-string → SyntaxErrors that look like logic bugs. Check the file's last lines.
- "Runs but logs nothing" → almost always reading the wrong watchlist file, not a logic bug.
- Cold start: price-move math returns 0.0 until the engine has run long enough to build history.
