from datetime import datetime, timedelta
import logging
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from skybreak.flight_scraper import fetch_flights

DB_PATH = "skybreak.db"

def save_flights(airport_code, flights):
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("CREATE TABLE IF NOT EXISTS flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_icao TEXT, airport_name TEXT, destination_icao TEXT, destination_name TEXT, flight_direction TEXT, departure_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, year_ahead INTEGER DEFAULT 365, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    for f in flights:
        try:
            # RapidAPI nested format
            dep = f.get("departure") or {}
            arr = f.get("arrival") or {}
            dep_time_raw = dep.get("scheduledTime") or dep.get("scheduledTime", {})
            if isinstance(dep_time_raw, dict):
                dep_time = dep_time_raw.get("utc") or dep_time_raw.get("local", "")
            else:
                dep_time = dep_time_raw or ""
            # For arrival-based flows, also allow arrival time if departure missing
            arr_time_raw = arr.get("scheduledTime") or arr.get("scheduledTime", {})
            if isinstance(arr_time_raw, dict):
                arr_time = arr_time_raw.get("utc") or arr_time_raw.get("local", "")
            else:
                arr_time = arr_time_raw or ""
            dest_icao = (arr.get("airport") or {}).get("icao") or arr.get("icao") or f.get("arrival_icao") or f.get("destination_icao") or ""
            dest_name = (arr.get("airport") or {}).get("name") or arr.get("name") or ""
            # Direction: is this airport the departure airport of the flight?
            dep_airport_icao = (dep.get("airport") or {}).get("icao") or dep.get("icao") or f.get("departure_icao", airport_code)
            direction = "departure" if str(dep_airport_icao).upper() == str(airport_code).upper() else "arrival"
            conn.execute(
                "INSERT OR IGNORE INTO flights (airport_icao, airport_name, destination_icao, destination_name, flight_direction, departure_time, year_ahead) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (airport_code, airport_code, dest_icao or airport_code, dest_name or "", direction, dep_time or arr_time, 365)
            )
        except Exception:
            continue
    conn.commit()
    conn.close()

def scrape_all_airports():
    import logging, sqlite3
    logger = logging.getLogger(__name__)
    conn = sqlite3.connect(DB_PATH, timeout=5)
    rows = conn.execute("SELECT code FROM airports").fetchall()
    conn.close()
    for (code,) in rows:
        try:
            conn_check = sqlite3.connect(DB_PATH, timeout=5)
            week_later = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            row = conn_check.execute("SELECT 1 FROM flights WHERE airport_icao = ? AND departure_time >= datetime('now') AND departure_time <= ? LIMIT 1", (code, week_later)).fetchone()
            conn_check.close()
            if row:
                logger.info("Skipping API fetch for %s: first-week data already present in DB", code)
                continue
            data = fetch_flights(code)
            if data:
                save_flights(code, data)
                logger.info("Batch fetched %d flights for %s", len(data), code)
        except Exception as e:
            logger.info("Batch fetch failed for %s: %s", code, e)
            pass

def start_scheduler():
    from skybreak.airport import get_setting
    try:
        interval = int(get_setting("fetch_interval_minutes") or 30)
    except Exception:
        interval = 30
    import logging
    logging.getLogger(__name__).info("Scheduler interval set to %s minutes", interval)
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_all_airports, "interval", minutes=interval)
    scheduler.add_job(clean_old_flights, "interval", minutes=interval)
    scheduler.start()

def clean_old_flights():
    import sqlite3
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("DELETE FROM flights WHERE departure_time < datetime('now')")
    conn.commit()
    deleted = conn.total_changes
    conn.close()
    return deleted
