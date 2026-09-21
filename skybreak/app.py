import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
from flask import Flask, request, jsonify, send_from_directory
from skybreak.airport_lookup import fetch_airport_name
from skybreak.airport import add_airport, delete_airport, validate_iata, init_db
import sqlite3
app = Flask(__name__, static_folder="/app/frontend/build/static", static_url_path="/static")
DB_PATH = "/data/skybreak.db"

init_db()
from skybreak.scraper_job import start_scheduler
start_scheduler()

@app.route("/api/airports", methods=["GET"])
def list_airports():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT code, name FROM airports").fetchall()
    conn.close()
    return jsonify([{"code": r[0], "name": r[1] or ""} for r in rows])
@app.route("/api/airports", methods=["POST"])
def create_airport():
    data = request.get_json(force=True)
    code = data.get("code", "").strip().upper()
    if not validate_iata(code):
        return jsonify({"error": "Invalid IATA"}), 400
    add_airport(code)
    return jsonify({"added": code})

@app.route("/api/airports/<code>", methods=["DELETE"])
def remove_airport(code):
    code = code.strip().upper()
    if not validate_iata(code):
        return jsonify({"error": "Invalid IATA"}), 400
    delete_airport(code)
    return jsonify({"deleted": code})

@app.route("/")
def index():
    return send_from_directory("/app/frontend/build", "index.html")

@app.route("/api/flights", methods=["GET"])
def list_flights():
    airport = request.args.get("airport", "").strip().upper()
    conn = sqlite3.connect(DB_PATH)
    sql = "SELECT airport_icao, airport_name, destination_icao, destination_name, flight_direction, departure_time FROM flights WHERE departure_time >= datetime('now') AND departure_time <= datetime('now', '+365 days')"
    params = []
    if airport:
        sql += " AND airport_icao = ?"
        params.append(airport)
    if request.args.get('date'):
        date_filter = request.args.get('date').strip()
        sql += " AND date(departure_time) = ?"
        params.append(date_filter)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    result = []
    for r in rows:
        airport_icao = r[0]
        destination_icao = r[2]
        airport_name = fetch_airport_name(airport_icao) or r[1] or ""
        destination_name = fetch_airport_name(destination_icao) or r[3] or ""
        result.append({
            "airport_icao": airport_icao,
            "airport_name": airport_name,
            "destination_icao": destination_icao,
            "destination_name": destination_name,
            "direction": r[4],
            "departure_time": r[5]
        })
    return jsonify(result)


@app.route("/api/settings/check", methods=["GET"])
def settings_check():
    from skybreak.airport import get_setting
    key = get_setting("api_key")
    return jsonify({"has_key": bool(key and key.strip())})

@app.route("/api/settings", methods=["GET", "POST"])
def settings():
    from skybreak.airport import get_setting, set_setting
    if request.method == "POST":
        data = request.get_json(force=True)
        for k, v in data.items():
            set_setting(str(k), str(v))
        return jsonify({"updated": True})
    else:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        conn.close()
        return jsonify({r[0]: r[1] for r in rows})

if __name__ == "__main__":
    init_db()
    from skybreak.scraper_job import start_scheduler
    start_scheduler()
    app.run(host="0.0.0.0", port=80)
