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
            # Parse departure / arrival from public API response
            dep_time = f.get("departure", f.get("scheduled_departure", ""))
            arr_time = f.get("arrival", f.get("scheduled_arrival", ""))
            dest = f.get("arrival", {}).get("icao") if isinstance(f.get("arrival"), dict) else f.get("arrival_icao", f.get("destination_icao", ""))
            direction = "departure" if airport_code == f.get("departure", {}).get("icao", airport_code) else "arrival"
            conn.execute(
                "INSERT OR IGNORE INTO flights (airport_icao, airport_name, destination_icao, destination_name, flight_direction, departure_time, year_ahead) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (airport_code, airport_code, dest or airport_code, dest or "", direction, dep_time or arr_time, 365)
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
