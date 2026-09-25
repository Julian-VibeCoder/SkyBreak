import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
from flask import Flask, request, jsonify, send_from_directory
from skybreak.airport_lookup import fetch_airport_name
from skybreak.airport import add_airport, delete_airport, validate_iata
import sqlite3
import threading
from datetime import datetime, timezone
import os

# Configurable paths for testing vs production
FRONTEND_BUILD_DIR = os.environ.get("FRONTEND_BUILD_DIR", "/app/frontend/build")
DB_PATH = os.environ.get("DB_FILE", "/opt/skybreak/skybreak.db")

app = Flask(__name__, static_folder=os.path.join(FRONTEND_BUILD_DIR, "static"), static_url_path="/static")

_scrape_lock = threading.Lock()
_scrape_in_progress = False

from skybreak.db_migrate import apply_migrations
apply_migrations()

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
    max_day = None
    for airport_icao, max_time_str in rows:
        if max_time_str:
            try:
                max_time = datetime.fromisoformat(max_time_str.replace('Z', '+00:00'))
                if max_time.tzinfo is None:
                    max_time = max_time.replace(tzinfo=timezone.utc)
                result[airport_icao] = {
                    "max_departure_time": max_time_str,
                    "max_departure_day": max_time.strftime('%Y-%m-%d')
                }
                if max_day is None or max_time > max_day:
                    max_day = max_time
            except Exception:
                result[airport_icao] = {"max_departure_time": max_time_str, "max_departure_day": None}
        else:
            result[airport_icao] = {"max_departure_time": None, "max_departure_day": None}
    result['_max_loaded_day'] = max_day.strftime('%Y-%m-%d') if max_day else None
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

@app.route("/api/settings/delay-ms", methods=["GET", "POST"])
def settings_delay_ms():
    from skybreak.airport import get_setting, set_setting
    if request.method == "POST":
        data = request.get_json(force=True)
        val = data.get("delay_ms")
        if val is not None:
            val_int = int(val)
            set_setting("scrape_delay_ms", str(val_int))
            return jsonify({"updated": True, "value": val_int})
        return jsonify({"updated": False, "error": "missing delay_ms"}), 400
    else:
        val_str = get_setting("scrape_delay_ms") or "500"
        return jsonify({"delay_ms": int(val_str)})

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
def find_short_trips():
    # Neuer Algorithmus: SQL-Filter + Two-Pointer/Hash-Join (Pseudocode-Implementierung)
    from datetime import datetime, timedelta, time
    start_str = request.args.get('start', '')
    end_str = request.args.get('end', '')
    start_days = [int(x) for x in request.args.get('start_days', '').split(',') if x != '']
    if not start_days: start_days = [4]
    end_days = [int(x) for x in request.args.get('end_days', '').split(',') if x != '']
    if not end_days: end_days = [1]
    max_dep_str = request.args.get('max_dep_dest', '23:59')
    min_ret_str = request.args.get('min_ret_dep', '00:00')
    start_airport = request.args.get('start_airport', '').strip().upper() or None
    max_trip_days_str = request.args.get('max_trip_days', '')
    max_trip_days = int(max_trip_days_str) if max_trip_days_str and max_trip_days_str.strip().isdigit() else None
    min_trip_days_str = request.args.get('min_trip_days', '')
    min_trip_days = int(min_trip_days_str) if min_trip_days_str and min_trip_days_str.strip().isdigit() else 1
    max_dep_hour, max_dep_min = 23, 59
    try:
        max_dep = max_dep_str.split(':')
        max_dep_hour = int(max_dep[0]) if len(max_dep) > 0 else 23
        max_dep_min = int(max_dep[1]) if len(max_dep) > 1 else 59
    except Exception:
        pass
    min_ret_hour, min_ret_min = 0, 0
    try:
        min_ret = min_ret_str.split(':')
        min_ret_hour = int(min_ret[0]) if len(min_ret) > 0 else 0
        min_ret_min = int(min_ret[1]) if len(min_ret) > 1 else 0
    except Exception:
        pass

    try:
        zeitraum_von = datetime.strptime(start_str, '%Y-%m-%d').strftime('%Y-%m-%d') if start_str else datetime.now().strftime('%Y-%m-%d')
        zeitraum_bis = datetime.strptime(end_str, '%Y-%m-%d').strftime('%Y-%m-%d') if end_str else (datetime.strptime(zeitraum_von, '%Y-%m-%d') + timedelta(days=14)).strftime('%Y-%m-%d')
    except Exception:
        zeitraum_von = datetime.now().strftime('%Y-%m-%d')
        zeitraum_bis = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')

    flughafen = start_airport
    max_dauer_tage = max_trip_days if max_trip_days is not None else 7
    min_dauer_tage = min_trip_days if min_trip_days is not None else 1
    spaeteste_hinzeit = f"{max_dep_hour:02d}:{max_dep_min:02d}:00"
    frueheste_rueckzeit = f"{min_ret_hour:02d}:{min_ret_min:02d}:00"

    start_days_str = ','.join(str(d) for d in start_days)
    end_days_str = ','.join(str(d) for d in end_days)

    # 1. SQL-Abfrage Hinflüge (Abflüge vom Startflughafen)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    sql_hin = f"""SELECT id, to_icao AS ziel, flight_number, departure_time AS abflug_zeit
                   FROM flights
                   WHERE airport_icao = ?
                     AND departure_time >= ?
                     AND departure_time <= ?
                     AND ((CAST(strftime('%w', departure_time) AS INTEGER) + 6) % 7) IN ({start_days_str})
                     AND time(departure_time) <= ?
                   ORDER BY to_icao, departure_time"""
    hinfluege_rows = conn.execute(sql_hin, (flughafen or '', zeitraum_von + ' 00:00:00', zeitraum_bis + ' 23:59:59', spaeteste_hinzeit)).fetchall()

    # 2. SQL-Abfrage Rückflüge (von Ziel zurück zum Startflughafen)
    zeitraum_bis_dt = datetime.strptime(zeitraum_bis, '%Y-%m-%d') + timedelta(days=max_dauer_tage)
    zeitraum_bis_rueck_str = zeitraum_bis_dt.strftime('%Y-%m-%d')
    sql_rueck = f"""SELECT id, from_icao AS start_flughafen, flight_number, departure_time AS abflug_zeit
                     FROM flights
                     WHERE to_icao = ?
                       AND departure_time >= ?
                       AND departure_time <= ?
                       AND ((CAST(strftime('%w', departure_time) AS INTEGER) + 6) % 7) IN ({end_days_str})
                       AND time(departure_time) >= ?
                     ORDER BY from_icao, departure_time"""
    rueckfluege_rows = conn.execute(sql_rueck, (flughafen or '', zeitraum_von + ' 00:00:00', zeitraum_bis_rueck_str + ' 23:59:59', frueheste_rueckzeit)).fetchall()
    conn.close()

    # 3. In-Memory Hash-Join (Gruppierung Rückflüge nach Destination)
    rueckfluege_by_destination = {}
    for flug in rueckfluege_rows:
        ziel_key = flug[1]
        if ziel_key not in rueckfluege_by_destination:
            rueckfluege_by_destination[ziel_key] = []
        rueckfluege_by_destination[ziel_key].append({
            "id": flug[0],
            "start_flughafen": flug[1],
            "flight_number": flug[2],
            "abflug_zeit": flug[3]
        })

    # 4. Lineares Matching (Two-Pointer-Prinzip mit Break bei zu später Rückflugzeit)
    ergebnisse = []
    for hin in hinfluege_rows:
        ziel = hin[1]
        if ziel not in rueckfluege_by_destination:
            continue
        moegliche_rueck = rueckfluege_by_destination[ziel]
        for rueck in moegliche_rueck:
            try:
                hin_zeit = datetime.fromisoformat(str(hin[3]).replace('Z', '+00:00'))
                rueck_zeit = datetime.fromisoformat(str(rueck["abflug_zeit"]).replace('Z', '+00:00'))
                dauer_stunden = (rueck_zeit - hin_zeit).total_seconds() / 3600.0
            except Exception:
                continue
            if dauer_stunden < 0:
                continue  # Rückflug vor Hinflug
            if min_dauer_tage is not None and dauer_stunden < (min_dauer_tage * 24):
                continue  # Unter Mindestlänge
            if max_dauer_tage is not None and dauer_stunden > (max_dauer_tage * 24):
                break  # Weitere Rückflüge für dieses Ziel zu spät (sortiert)
            ergebnisse.append({
                "destination": ziel,
                "hinflug_id": hin[0],
                "hinflug_ziel": ziel,
                "hinflug_flight_number": hin[2] or "",
                "hinflug_ziel_name": fetch_airport_name(ziel) or ziel,
                "hinflug_abflug_zeit": hin[3],
                "rueckflug_id": rueck["id"],
                "rueckflug_start": rueck["start_flughafen"],
                "rueckflug_start_name": fetch_airport_name(rueck["start_flughafen"]) or rueck["start_flughafen"],
                "rueckflug_abflug_zeit": rueck["abflug_zeit"],
                "rueckflug_flight_number": rueck.get("flight_number") or "",
                "dauer_tage": round(dauer_stunden / 24.0, 2)
            })
    ergebnisse.sort(key=lambda x: x.get("hinflug_abflug_zeit", ""))
    return jsonify({"turnarounds": ergebnisse, "count": len(ergebnisse), "algorithm": "sql_filter_hash_join"})

if __name__ == "__main__":
    apply_migrations()
    app.run(host="0.0.0.0", port=80)
