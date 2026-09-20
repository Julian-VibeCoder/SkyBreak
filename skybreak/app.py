from flask import Flask, request, jsonify
from skybreak.airport import add_airport, validate_iata, init_db
import sqlite3
app = Flask(__name__)
DB_PATH = "skybreak.db"
@app.route("/api/airports", methods=["GET"])
def list_airports():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT code FROM airports").fetchall()
    conn.close()
    return jsonify([r[0] for r in rows])
@app.route("/api/airports", methods=["POST"])
def create_airport():
    data = request.get_json(force=True)
    code = data.get("code", "").strip().upper()
    if not validate_iata(code):
        return jsonify({"error": "Invalid IATA"}), 400
    add_airport(code)
    return jsonify({"added": code})
@app.route("/")
def index():
    return open("frontend/index.html").read()

@app.route("/api/flights", methods=["GET"])
def list_flights():
    airport = request.args.get("airport", "").strip().upper()
    conn = sqlite3.connect(DB_PATH)
    sql = "SELECT airport_icao, destination_icao, flight_direction FROM flights WHERE departure_time >= datetime('now') AND departure_time <= datetime('now', '+365 days')"
    params = []
    if airport:
        sql += " AND airport_icao = ?"
        params.append(airport)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    result = [{"airport_icao": r[0], "destination_icao": r[1], "direction": r[2]} for r in rows]
    return jsonify(result)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000)
