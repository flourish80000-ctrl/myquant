from flask import Flask, redirect
import sqlite3, subprocess, os, math
from datetime import datetime

app = Flask(__name__)
DB_FILE = "trades.db"
ENGINE  = "paper_engine.py"
LOGFILE = "engine.log"

# ---------- read-only database helper ----------
def fetch(query):
    conn = sqlite3.connect(DB_FILE, timeout=30)
    rows = list(conn.execute(query))
    conn.close()
    return rows

def one(query):
    r = fetch(query)
    return r[0][0] if r else 0

# ---------- engine process control ----------
def engine_pids():
    out = subprocess.run(["pgrep", "-f", ENGINE], capture_output=True, text=True).stdout
    return [int(p) for p in out.split()]

def engine_running():
    return len(engine_pids()) > 0

# ---------- small formatters ----------
def money(x):
    return f"{float(x):.3f}" if x is not None else "--"

def age_of(ts, now):
    try:
        t = datetime.strptime(str(ts)[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return "-"
    s = (now - t).total_seconds()
    if s < 60:    return f"{int(s)}s"
    if s < 3600:  return f"{int(s//60)}m"
    if s < 86400: return f"{int(s//3600)}h"
    return f"{int(s//86400)}d"

# ---------- buttons: start / stop the engine ----------
@app.route("/start", methods=["POST"])
def start_engine():
    if not engine_running():
        log = open(LOGFILE, "a")
        subprocess.Popen(["python3", ENGINE], stdout=log, stderr=log, start_new_session=True)
    return redirect("/")

@app.route("/stop", methods=["POST"])
def stop_engine():
    for pid in engine_pids():
        try:
            os.kill(pid, 15)
        except Exception:
            pass
    return redirect("/")

# ---------- the dashboard ----------
@app.route("/")
def home():
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    positions = fetch("SELECT market_id, outcome_name, entry_price, timestamp "
                      "FROM paper_positions WHERE status='OPEN' ORDER BY id DESC")
    open_count = len(positions)
    open_today = sum(1 for p in positions if str(p[3]).startswith(today))
    open_held  = open_count - open_today

    pos_rows = ""
    for mid, outcome, price, ts in positions:
        d = "up" if str(outcome).lower() == "up" else "down"
        arrow = "▲" if d == "up" else "▼"
        pos_rows += (f'<tr><td class="mkt">{mid}</td>'
                     f'<td><span class="chip {d}">{arrow} {outcome}</span></td>'
                     f'<td class="num">{money(price)}</td>'
                     f'<td class="num age">{age_of(ts, now)}</td></tr>')

    signals = fetch("SELECT timestamp, market_id, signal_type, market_price, venue "
                    "FROM trades ORDER BY id DESC LIMIT 12")
    sig_rows = ""
    for ts, mid, stype, price, venue in signals:
        healthy = str(stype).upper().startswith("HEALTHY")
        cls   = "healthy" if healthy else "trap"
        label = "Healthy" if healthy else "Trap"
        sig_rows += (f'<div class="sig {cls}"><span class="time">{str(ts)[11:19]}</span>'
                     f'<div class="mid"><span class="badge">{label}</span>'
                     f'<span class="venue">{mid} · {venue}</span></div>'
                     f'<div class="price">{money(price)}<small>mid</small></div></div>')

    verd_total = one("SELECT COUNT(*) FROM resolutions")
    verd_w     = one("SELECT COUNT(*) FROM resolutions WHERE verdict='WIN'")
    verd_l     = verd_total - verd_w
    verd_pct   = round(100*verd_w/verd_total, 1) if verd_total else 0

    comp_total = one("SELECT COUNT(*) FROM resolutions WHERE market_id>760000")
    comp_w     = one("SELECT COUNT(*) FROM resolutions WHERE market_id>760000 AND verdict='WIN'")
    comp_l     = comp_total - comp_w
    comp_pct   = round(100*comp_w/comp_total, 1) if comp_total else 0
    down_bets  = one("SELECT COUNT(*) FROM resolutions WHERE market_id>760000 AND outcome_held='Down'")

    if comp_total:
        p  = comp_w/comp_total
        se = math.sqrt(p*(1-p)/comp_total)
        lo = int(round(100*(p - 1.96*se)))
        hi = int(round(100*(p + 1.96*se)))
    else:
        lo = hi = 0

    g_sample = comp_total >= 100
    g_down   = down_bets  >= 30
    g_ci     = lo > 50
    headline = "EDGE FOUND" if (g_sample and g_down and g_ci) else "NO EDGE"

    def gate(ok, label, val):
        return (f'<div class="gate"><span class="tick {"ok" if ok else "no"}">'
                f'{"✓" if ok else "✕"}</span><span class="g-lbl">{label}</span>'
                f'<span class="g-val">{val}</span></div>')
    gates = (gate(g_sample, "Sample ≥ 100", comp_total)
             + gate(g_down, "Down-bets ≥ 30", down_bets)
             + gate(g_ci,  "CI lower > 50%", f"{lo}%"))

    sig_total = one("SELECT COUNT(*) FROM trades")
    venue = dict(fetch("SELECT venue, COUNT(*) FROM trades GROUP BY venue"))
    pf = venue.get("predict.fun", 0)
    hl = venue.get("hyperliquid", 0)
    pf_pct = round(100*pf/sig_total, 1) if sig_total else 0
    hl_pct = round(100*hl/sig_total, 1) if sig_total else 0

    last = one("SELECT MAX(timestamp) FROM trades")
    updated = str(last)[11:19] if last else now.strftime("%H:%M:%S")

    running = engine_running()
    status = ('<span class="estat on"><span class="dot"></span> ENGINE LIVE</span>'
              if running else '<span class="estat off">● ENGINE OFF</span>')
    controls = (f'<div class="ctrl">{status}'
                f'<form method="post" action="/start" style="margin:0">'
                f'<button class="ebtn start"{" disabled" if running else ""}>▶ Start</button></form>'
                f'<form method="post" action="/stop" style="margin:0">'
                f'<button class="ebtn stop"{"" if running else " disabled"}>■ Stop</button></form></div>')

    page = open("desk_template.html").read()
    fill = {
        "<!--UPDATED-->": updated,
        "<!--ENGINE_CONTROLS-->": controls,
        "<!--EDGE_HEADLINE-->": headline,
        "<!--COMPASS_TOTAL-->": str(comp_total),
        "<!--DOWNBETS-->": str(down_bets),
        "<!--COMPASS_PCT-->": str(comp_pct),
        "<!--CI_LOWER-->": str(lo),
        "<!--CI_UPPER-->": str(hi),
        "<!--GATES-->": gates,
        "<!--DONUT_P-->": str(comp_pct),
        "<!--COMPASS_W-->": str(comp_w),
        "<!--COMPASS_L-->": str(comp_l),
        "<!--OPEN_COUNT-->": str(open_count),
        "<!--OPEN_TODAY-->": str(open_today),
        "<!--OPEN_HELD-->": str(open_held),
        "<!--VERD_TOTAL-->": str(verd_total),
        "<!--VERD_W-->": str(verd_w),
        "<!--VERD_L-->": str(verd_l),
        "<!--VERD_PCT-->": str(verd_pct),
        "<!--SIG_TOTAL-->": f"{sig_total:,}",
        "<!--PF_PCT-->": str(pf_pct),
        "<!--HL_PCT-->": str(hl_pct),
        "<!--PF_COUNT-->": f"{pf:,}",
        "<!--HL_COUNT-->": f"{hl:,}",
        "<!--POSITIONS_ROWS-->": pos_rows,
        "<!--SIG_SHOWN-->": str(len(signals)),
        "<!--SIGNAL_ROWS-->": sig_rows,
    }
    for k, v in fill.items():
        page = page.replace(k, v)
    return page

if __name__ == "__main__":
    app.run(port=5050)
