import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
from flask import Flask, request, jsonify, send_from_directory
from skybreak.airport_lookup import fetch_airport_name
from skybreak.airport import add_airport, delete_airport, validate_iata, init_db
import sqlite3
from datetime import datetime, timezone
import os

# Configurable paths for testing vs production
FRONTEND_BUILD_DIR = os.environ.get("FRONTEND_BUILD_DIR", "/app/frontend/build")
DB_PATH = os.environ.get("DB_FILE", "/data/skybreak.db")

app = Flask(__name__, static_folder=os.path.join(FRONTEND_BUILD_DIR, "static"), static_url_path="/static")

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
    return send_from_directory(FRONTEND_BUILD_DIR, "index.html")

@app.route("/api/flights", methods=["GET"])
def list_flights():
    airport = request.args.get("airport", "").strip().upper()
    conn = sqlite3.connect(DB_PATH)
    sql = "SELECT airport_icao, airport_name, destination_icao, destination_name, flight_direction, departure_time, flight_number FROM flights WHERE departure_time >= datetime('now','utc') AND departure_time <= datetime('now', '+365 days')"
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
            "departure_time": r[5] + ("Z" if r[5] and not r[5].endswith("Z") and "+" not in r[5][-6:] else ""),
            "flight_number": r[6] or ""
        })
    return jsonify(result)



@app.route("/api/flights/future", methods=["GET"])
def future_flights_info():
    conn = sqlite3.connect(DB_PATH)
    # For each airport shown in flights page, compute max departure_time from DB
    rows = conn.execute("SELECT airport_icao, MAX(departure_time) FROM flights WHERE departure_time >= datetime('now','utc') GROUP BY airport_icao").fetchall()
    conn.close()
    result = {}
    from datetime import datetime
    now = datetime.now(timezone.utc)
    for airport_icao, max_time_str in rows:
        if max_time_str:
            try:
                max_time = datetime.fromisoformat(max_time_str.replace('Z', '+00:00'))
                delta = max_time - now if max_time.tzinfo else max_time.replace(tzinfo=timezone.utc) - now
                # If max_time has no tzinfo, keep simple
                if max_time.tzinfo is None:
                    delta = max_time.replace(tzinfo=timezone.utc) - now
                result[airport_icao] = {
                    "max_departure_time": (max_time_str + "Z") if max_time_str and not max_time_str.endswith("Z") and "+" not in max_time_str[-6:] else max_time_str,
                    "days_ahead": round(delta.total_seconds() / 86400, 2)
                }
            except Exception:
                result[airport_icao] = {"max_departure_time": (max_time_str + "Z") if max_time_str and not max_time_str.endswith("Z") and "+" not in max_time_str[-6:] else max_time_str, "days_ahead": None}
        else:
            result[airport_icao] = {"max_departure_time": None, "days_ahead": None}
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
