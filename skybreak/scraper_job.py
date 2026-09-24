import json, logging, sqlite3, subprocess, sys, os
from datetime import datetime, timedelta
from skybreak.airport import get_setting, fetch_airport_name, init_db
DB_PATH = os.environ.get("DB_FILE", "/data/skybreak.db")
logger = logging.getLogger(__name__)

def _run_kayak(airport, month, delay=None):
    # Baumhöhe: DB-Delayed-Wert (ms) lesen, falls nicht gesetzt Fallback 0.5
    if delay is None:
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30)
            row = conn.execute("SELECT value FROM settings WHERE key = ?", ("scrape_delay_ms",)).fetchone()
            conn.close()
            delay = float(row[0]) / 1000.0 if row and row[0] else 0.5
        except Exception:
            delay = 0.5
    cmd = [sys.executable, "skybreak/kayak_direct.py", airport, "-m", month, "-d", "both", "--delay", str(delay)]
    env = os.environ.copy(); env["PYTHONPATH"] = "."
    try:
        res = subprocess.run(cmd, stdout=None, stderr=None, timeout=300, env=env)
        logger.info("kayak %s %s finished (returncode %s)", airport, month, res.returncode)
        return res
    except Exception as e:
        logger.warning("subprocess %s %s: %s", airport, month, e)
        return None

def _import_kayak_json(airport):
    path = f"{airport.upper()}_direct.json"
    if not os.path.exists(path): return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("flights", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    except Exception as e:
        logger.warning("read json %s: %s", path, e)
        return []

def _clear_month(airport, month):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(flights)").fetchall()]
    except: cols = []
    if "month_key" not in cols:
        for col in ("month_key", "flight_date", "from_icao", "to_icao", "arrival_date", "airport_name", "destination_name", "flight_number", "departure", "arrival"):
            try:
                col_type = "TIME" if col in ("departure","arrival") else "TEXT"
                conn.execute(f"ALTER TABLE flights ADD COLUMN {col} {col_type}")
            except: pass
    conn.execute("DELETE FROM flights WHERE airport_icao = ? AND (month_key = ? OR flight_date LIKE ?)", (airport.upper(), month, month+"-%"))
    conn.commit(); conn.close()

def _save_kayak(airport, flights, month):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("CREATE TABLE IF NOT EXISTS flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_icao TEXT, airport_name TEXT, destination_icao TEXT, destination_name TEXT, flight_direction TEXT, flight_date TEXT, flight_number TEXT, from_icao TEXT, to_icao TEXT, departure TIME, arrival TIME, arrival_date TEXT, duration_minutes INTEGER, month_key TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    # Migration: sicherstellen, dass alle neuen Spalten existieren
    required = {"airport_name":"TEXT","destination_name":"TEXT","flight_date":"TEXT","flight_number":"TEXT","from_icao":"TEXT","to_icao":"TEXT","arrival_date":"TEXT","month_key":"TEXT","departure":"TIME","arrival":"TIME"}
    try:
        cols = {r[1]: r[2] for r in conn.execute("PRAGMA table_info(flights)").fetchall()}
    except Exception:
        cols = {}
    for col, col_type in required.items():
        if col not in cols:
            try:
                conn.execute(f"ALTER TABLE flights ADD COLUMN {col} {col_type}")
                logger.info("Migrated: added column %s to flights", col)
            except Exception as e:
                logger.warning("Migration failed for %s: %s", col, e)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_flights_airport_month ON flights (airport_icao, month_key)")
    airport_name = fetch_airport_name(airport.upper()) or airport.upper()
    for f in flights:
        try:
            date_str = f.get("date") or f.get("flight_date") or ""
            if not date_str: continue
            month_key = str(date_str)[:7] if len(str(date_str))>=7 else month
            flight_number = f.get("flight_number") or f.get("flightNumber") or ""
            from_icao = f.get("from") or f.get("from_icao") or airport.upper()
            to_icao = f.get("to") or f.get("to_icao") or ""
            departure_str = f.get("departure") or ""
            arrival_str = f.get("arrival") or ""
            arrival_date = f.get("arrival_date") or f.get("arrivalDate") or date_str
            duration = f.get("duration_min") or f.get("duration_minutes") or f.get("duration")
            try: duration_minutes = int(duration) if duration is not None else None
            except: duration_minutes = None
            direction = "departure" if str(from_icao).upper()==str(airport.upper()).upper() else "arrival"
            dest_icao = to_icao if direction=="departure" else from_icao
            if str(dest_icao or "").upper()==str(airport.upper()).upper(): continue
            from skybreak.airport_lookup import fetch_airport_name as lookup_name
            dest_name = lookup_name(dest_icao) or dest_icao
            conn.execute("INSERT INTO flights (airport_icao, airport_name, destination_icao, destination_name, flight_direction, flight_date, flight_number, from_icao, to_icao, departure, arrival, departure_time, arrival_time, arrival_date, duration_minutes, month_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (airport.upper(), airport_name, dest_icao, dest_name, direction, date_str, flight_number, from_icao, to_icao, departure_str, arrival_str, (date_str + " " + departure_str) if date_str and departure_str else None, (date_str + " " + arrival_str) if date_str and arrival_str else None, arrival_date, duration_minutes, month_key))
        except Exception as e:
            logger.warning("save flight %s: %s", f, e)
    conn.commit(); conn.close()

def scrape_all_airports():
    init_db()
    conn = sqlite3.connect(DB_PATH, timeout=30)
    rows = conn.execute("SELECT code FROM airports").fetchall()
    conn.close()
    max_raw = get_setting("fetch_max_months") or get_setting("fetch_max_days") or "3"
    try: max_months = int(max_raw)
    except: max_months = 3
    max_months = max(1, min(max_months, 12))
    now = datetime.now()
    months = sorted({(now + timedelta(days=30*i)).strftime("%Y-%m") for i in range(max_months)})
    for (code,) in rows:
        airport = code.upper()
        try:
            for month in months:
                logger.info("Kayak fetch %s %s", airport, month)
                _clear_month(airport, month)
                res = _run_kayak(airport, month)
                flights = _import_kayak_json(airport)
                _save_kayak(airport, flights, month)
                logger.info("Saved %d flights for %s %s", len(flights), airport, month)
        except Exception as e:
            logger.info("Kayak fetch failed %s: %s", airport, e)

def start_scheduler():
    from apscheduler.schedulers.background import BackgroundScheduler
    try: interval = int(get_setting("fetch_interval_minutes") or "30")
    except: interval = 30
    if interval == 0: logger.info("Scheduler disabled"); return
    interval = max(1, min(interval, 10080))
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_all_airports, "interval", minutes=interval)
    scheduler.start()

def clean_old_flights():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("DELETE FROM flights WHERE flight_date < date('now') OR (flight_date IS NULL AND departure < datetime('now'))")
    conn.commit(); conn.close()
