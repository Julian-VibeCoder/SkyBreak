from flask import Flask, request, jsonify, render_template
from skybreak.airport import add_airport, delete_airport, validate_iata, init_db
import sqlite3
app = Flask(__name__, template_folder="frontend", static_folder="frontend/build", static_url_path="/static")
DB_PATH = "skybreak.db"
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
    from flask import render_template
    # Serve the React build output; fallback for missing template folder
    import os
    build_path = os.path.join("frontend", "build", "index.html")
    if os.path.exists(build_path):
        with open(build_path) as f:
            return f.read()
    return render_template("index.html")

@app.route("/api/flights", methods=["GET"])
def list_flights():
    airport = request.args.get("airport", "").strip().upper()
    conn = sqlite3.connect(DB_PATH)
    sql = "SELECT airport_icao, airport_name, destination_icao, destination_name, flight_direction FROM flights WHERE departure_time >= datetime('now') AND departure_time <= datetime('now', '+365 days')"
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
    result = [{"airport_icao": r[0], "airport_name": r[1] or "", "destination_icao": r[2], "destination_name": r[3] or "", "direction": r[4]} for r in rows]
    return jsonify(result)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000)
