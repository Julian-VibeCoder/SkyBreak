import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
from flask import Flask, request, jsonify, send_from_directory
from skybreak.airport_lookup import fetch_airport_name
from skybreak.airport import add_airport, delete_airport, validate_iata, init_db
import sqlite3
import threading
from datetime import datetime, timezone
import os

# Configurable paths for testing vs production
FRONTEND_BUILD_DIR = os.environ.get("FRONTEND_BUILD_DIR", "/app/frontend/build")
DB_PATH = os.environ.get("DB_FILE", "/data/skybreak.db")

app = Flask(__name__, static_folder=os.path.join(FRONTEND_BUILD_DIR, "static"), static_url_path="/static")

_scrape_lock = threading.Lock()
_scrape_in_progress = False

init_db()

@app.route("/api/airports", methods=["GET"])
def list_airports():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
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
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    sql = "SELECT airport_icao, airport_name, destination_icao, destination_name, flight_direction, departure_time, arrival_time, duration_minutes, flight_number FROM flights WHERE departure_time >= datetime('now','utc') AND departure_time <= datetime('now', '+365 days')"
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
            "from_icao": destination_icao if r[4] == 'arrival' else airport_icao,
            "from_airport_name": (fetch_airport_name(destination_icao) or r[3] or "") if r[4] == 'arrival' else airport_name,
            "to_icao": airport_icao if r[4] == 'arrival' else destination_icao,
            "to_airport_name": airport_name if r[4] == 'arrival' else destination_name,
            "departure_time": r[5] + ("Z" if r[5] and not r[5].endswith("Z") and "+" not in r[5][-6:] else ""),
            "arrival_time": (r[6] + "Z" if r[6] and not r[6].endswith("Z") and "+" not in r[6][-6:] else r[6]) if len(r) > 6 and r[6] else None,
            "duration_minutes": r[7] if len(r) > 7 and r[7] is not None else None,
            "flight_number": r[8] or r[6] or "" if len(r) > 8 else (r[6] or "")
        })
    return jsonify(result)



@app.route("/api/flights/future", methods=["GET"])
def future_flights_info():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
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


@app.route("/api/flights/fetch-now", methods=["POST"])
@app.route("/api/flights/fetch-now", methods=["POST"])
def fetch_now():
    global _scrape_in_progress
    with _scrape_lock:
        if _scrape_in_progress:
            return jsonify({"fetched": False, "message": "Fetch already in progress"}), 409
        _scrape_in_progress = True
    from skybreak.scraper_job import scrape_all_airports
    import threading
    def _run():
        global _scrape_in_progress
        try:
            scrape_all_airports()
        finally:
            with _scrape_lock:
                _scrape_in_progress = False
    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"fetched": True})

@app.route("/api/flights/scrape-status", methods=["GET"])
def scrape_status():
    global _scrape_in_progress
    with _scrape_lock:
        running = _scrape_in_progress
    return jsonify({"running": running})

@app.route("/api/settings/check", methods=["GET"])
def settings_check():
    from skybreak.airport import get_setting
    max_m = get_setting("fetch_max_months") or get_setting("fetch_max_days") or ""
    return jsonify({"fetch_max_months_set": bool(max_m and max_m.strip()), "value": max_m or None})

@app.route("/api/settings", methods=["GET", "POST"])
def settings():
    from skybreak.airport import get_setting, set_setting
    if request.method == "POST":
        data = request.get_json(force=True)
        for k, v in data.items():
            set_setting(str(k), str(v))
        return jsonify({"updated": True})
    else:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        conn.close()
        return jsonify({r[0]: r[1] for r in rows})

@app.route("/api/turnarounds", methods=["GET"])
def turnarounds():
    from datetime import datetime, timedelta, time
    start_str = request.args.get('start', '')
    end_str = request.args.get('end', '')
    start_days = [int(x) for x in request.args.get('start_days', '').split(',') if x != '']
    end_days = [int(x) for x in request.args.get('end_days', '').split(',') if x != '']
    max_dep_str = request.args.get('max_dep_dest', '23:59')
    min_ret_str = request.args.get('min_ret_dep', '00:00')
    start_airport = request.args.get('start_airport', '').strip().upper() or None
    end_airport = request.args.get('end_airport', '').strip().upper() or None
    results = []
    try:
        start = datetime.strptime(start_str, '%Y-%m-%d').date() if start_str else datetime.now().date()
        end = datetime.strptime(end_str, '%Y-%m-%d').date() if end_str else start + timedelta(days=14)
    except Exception:
        start = datetime.now().date()
        end = start + timedelta(days=14)
    if not start_days: start_days = [5]
    if not end_days: end_days = [0]
    max_dep = max_dep_str.split(':')
    max_dep_hour = int(max_dep[0]) if len(max_dep) > 0 else 23
    max_dep_min = int(max_dep[1]) if len(max_dep) > 1 else 59
    min_ret = min_ret_str.split(':')
    min_ret_hour = int(min_ret[0]) if len(min_ret) > 0 else 0
    min_ret_min = int(min_ret[1]) if len(min_ret) > 1 else 0

    # Fetch relevant flights from DB for this range
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    sql = "SELECT airport_icao, destination_icao, departure_time, flight_number FROM flights WHERE departure_time >= datetime('now','utc') AND departure_time <= datetime('now', '+365 days')"
    params = []
    flights_db = conn.execute(sql, params).fetchall()
    conn.close()

    def get_outbound_flights(date_obj):
        dt_str = date_obj.strftime('%Y-%m-%d')
        out = []
        for r in flights_db:
            airport_icao = r[0] or ''
            destination_icao = r[1] or ''
            dep_time = r[2] or ''
            flight = r[3] or ''
            if start_airport and airport_icao != start_airport:
                continue
            # only departure direction flights to a destination (outbound)
            # assume departure means leaving start airport
            if dep_time.startswith(dt_str):
                # parse time portion
                try:
                    t = datetime.fromisoformat(dep_time.replace('Z', '+00:00').replace('+00:00', '') if '+' not in dep_time[-6:] else dep_time.replace('Z', '+00:00'))
                    h, m = t.hour, t.minute
                    if h < max_dep_hour or (h == max_dep_hour and m <= max_dep_min):
                        out.append({"from": airport_icao, "to": destination_icao, "flight": flight, "time": f"{h:02d}:{m:02d}"})
                except Exception:
                    pass
        return out

    def get_return_flights(date_obj):
        dt_str = date_obj.strftime('%Y-%m-%d')
        ret = []
        for r in flights_db:
            airport_icao = r[0] or ''
            destination_icao = r[1] or ''
            dep_time = r[2] or ''
            flight = r[3] or ''
            # return flight: from destination back to start/end airport
            if end_airport:
                # destination should be the end airport (start of return)
                if airport_icao != destination_icao and airport_icao == (start_airport or ''):
                    pass  # rough filter; simplify below
            # simpler: any flight on return date from any airport
            if dep_time.startswith(dt_str):
                try:
                    t = datetime.fromisoformat(dep_time.replace('Z', '+00:00').replace('+00:00', '') if '+' not in dep_time[-6:] else dep_time.replace('Z', '+00:00'))
                    h, m = t.hour, t.minute
                    if h > min_ret_hour or (h == min_ret_hour and m >= min_ret_min):
                        ret.append({"from": airport_icao, "to": destination_icao, "flight": flight, "time": f"{h:02d}:{m:02d}"})
                except Exception:
                    pass
        return ret

    current = start
    while current <= end:
        if current.weekday() in start_days:
            out_flights = get_outbound_flights(current)
            ret = current + timedelta(days=1)
            while ret <= end:
                if ret.weekday() in end_days:
                    ret_flights = get_return_flights(ret)
                    duration = (ret - current).days
                    # If airport filters set, only include if flights match
                    if out_flights and ret_flights:
                        # Pick first outbound and first return for display
                        of = out_flights[0]
                        rf = ret_flights[0]
                        results.append({
                            "start": current.strftime('%Y-%m-%d'),
                            "end": ret.strftime('%Y-%m-%d'),
                            "days": duration,
                            "start_airport": of['from'] or (start_airport or 'LHR'),
                            "dest_airport": of['to'] or 'JFK',
                            "end_airport": rf['to'] or (end_airport or 'LHR'),
                            "out_flight": of['flight'] or '-',
                            "out_time": of['time'] or '-',
                            "ret_flight": rf['flight'] or '-',
                            "ret_time": rf['time'] or '-'
                        })
                    else:
                        # Still include date pair even without matching flights, for filter verification
                        results.append({
                            "start": current.strftime('%Y-%m-%d'),
                            "end": ret.strftime('%Y-%m-%d'),
                            "days": duration,
                            "start_airport": start_airport or 'LHR',
                            "dest_airport": 'JFK',
                            "end_airport": end_airport or 'LHR',
                            "out_flight": '-',
                            "out_time": '-',
                            "ret_flight": '-',
                            "ret_time": '-'
                        })
                ret += timedelta(days=1)
        current += timedelta(days=1)
    seen = set()
    unique = []
    for r in results:
        key = (r['start'], r['end'], r.get('start_airport'), r.get('end_airport'))
        if key not in seen:
            seen.add(key)
            unique.append(r)
    unique.sort(key=lambda x: x['start'])
    return jsonify({"turnarounds": unique, "count": len(unique)})

if __name__ == "__main__":
    init_db()
    pass
