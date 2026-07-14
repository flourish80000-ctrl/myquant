from flask import Flask
import sqlite3

app = Flask(__name__)
DB_FILE = "trades.db"


# Read-only helper: run a SELECT and hand back the rows.
def fetch(query):
    conn = sqlite3.connect(DB_FILE)
    rows = list(conn.execute(query))
    conn.close()
    return rows


@app.route("/")
def home():
    positions = fetch(
        "SELECT market_id, outcome_name, entry_price, timestamp "
        "FROM paper_positions WHERE status = 'OPEN' ORDER BY id DESC"
    )
    signals = fetch(
        "SELECT timestamp, market_id, signal_type, market_price "
        "FROM trades ORDER BY id DESC LIMIT 20"
    )

    # Build the web page as one big text string.
    html = "<html><head><title>SAIS Signal Desk</title>"
    html += "<meta http-equiv='refresh' content='10'>"  # auto-refresh every 10s
    html += "<style>body{font-family:sans-serif;margin:40px;background:#111;color:#eee;}"
    html += "table{border-collapse:collapse;margin-bottom:30px;}"
    html += "td,th{border:1px solid #444;padding:6px 14px;text-align:left;}"
    html += "th{background:#222;} h1{color:#4ade80;}</style></head><body>"
    html += "<h1>SAIS Signal Desk</h1>"

    html += "<h2>Open Paper Positions</h2>"
    html += "<table><tr><th>Market</th><th>Outcome</th><th>Entry</th><th>Opened</th></tr>"
    for market_id, outcome, price, ts in positions:
        html += f"<tr><td>{market_id}</td><td>{outcome}</td><td>{price}</td><td>{ts}</td></tr>"
    html += "</table>"

    html += "<h2>Latest 20 Signals</h2>"
    html += "<table><tr><th>Time</th><th>Market</th><th>Type</th><th>Price</th></tr>"
    for ts, market_id, stype, price in signals:
        html += f"<tr><td>{ts}</td><td>{market_id}</td><td>{stype}</td><td>{price}</td></tr>"
    html += "</table>"

    html += "</body></html>"
    return html


if __name__ == "__main__":
    app.run(port=5000)