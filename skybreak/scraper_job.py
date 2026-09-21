from datetime import datetime, timedelta
import logging
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from skybreak.flight_scraper import fetch_flights

DB_PATH = "/data/skybreak.db"

def get_latest_flight_time(airport_code):
    conn = sqlite3.connect(DB_PATH, timeout=5)
    row = conn.execute(
        "SELECT departure_time FROM flights WHERE airport_icao = ? ORDER BY departure_time DESC LIMIT 1",
        (airport_code,)
    ).fetchone()
    conn.close()
    return row[0] if row else None

def save_flights(airport_code, flights):
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("CREATE TABLE IF NOT EXISTS flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_icao TEXT, airport_name TEXT, destination_icao TEXT, destination_name TEXT, flight_direction TEXT, departure_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, year_ahead INTEGER DEFAULT 365, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    for f in flights:
        try:
            dep = f.get("departure") or {}
            arr = f.get("arrival") or {}
            dep_time_raw = dep.get("scheduledTime") or dep.get("scheduledTime", {})
            if isinstance(dep_time_raw, dict):
                dep_time = dep_time_raw.get("utc") or dep_time_raw.get("local", "")
            else:
                dep_time = dep_time_raw or ""
            arr_time_raw = arr.get("scheduledTime") or arr.get("scheduledTime", {})
            if isinstance(arr_time_raw, dict):
                arr_time = arr_time_raw.get("utc") or arr_time_raw.get("local", "")
            else:
                arr_time = arr_time_raw or ""
            dep_airport_icao = (dep.get("airport") or {}).get("icao") or dep.get("icao") or f.get("departure_icao") or airport_code
            direction = "departure" if str(dep_airport_icao).upper() == str(airport_code).upper() else "arrival"
            if direction == "departure":
                dest_icao = (arr.get("airport") or {}).get("icao") or arr.get("icao") or f.get("arrival_icao") or f.get("destination_icao") or ""
                dest_name = (arr.get("airport") or {}).get("name") or arr.get("name") or ""
                if not dest_icao or str(dest_icao).upper() == str(airport_code).upper():
                    continue
            else:
                dest_icao = dep_airport_icao
                dest_name = (dep.get("airport") or {}).get("name") or dep.get("name") or ""
                if not dest_icao or str(dest_icao).upper() == str(airport_code).upper():
                    continue
            from skybreak.airport_lookup import fetch_airport_name
            airport_name = fetch_airport_name(airport_code) or airport_code
            # Avoid duplicates: check if exact departure+airport+direction+destination exists
            existing = conn.execute(
                "SELECT 1 FROM flights WHERE airport_icao = ? AND destination_icao = ? AND flight_direction = ? AND departure_time = ? LIMIT 1",
                (airport_code, dest_icao, direction, dep_time or arr_time)
            ).fetchone()
            if existing:
                continue
            conn.execute(
                "INSERT OR IGNORE INTO flights (airport_icao, airport_name, destination_icao, destination_name, flight_direction, departure_time, year_ahead) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (airport_code, airport_name, dest_icao, dest_name, direction, dep_time or arr_time, 365)
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
            latest_str = get_latest_flight_time(code)
            if latest_str:
                start_str = (datetime.fromisoformat(latest_str.replace("Z", "+00:00")).replace(tzinfo=None) - timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M")
            else:
                start_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
            end_str = (datetime.utcnow() + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M")
            # Keep fetching next 6h windows until rate limit stops us
            wait_time = 30 * 60
            max_attempts = 10
            attempts = 0
            fetched_any = False
            while attempts < max_attempts:
                attempts += 1
                try:
                    data = fetch_flights(code, start_time_str=start_str, end_time_str=end_str)
                    if data:
                        save_flights(code, data)
                        fetched_any = True
                        logger.info("Batch fetched %d flights for %s (window %s to %s)", len(data), code, start_str, end_str)
                    # After a successful call, advance window by 6h for next request
                    try:
                        end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                        if end_dt.tzinfo is not None:
                            end_dt = end_dt.replace(tzinfo=None)
                        start_dt = end_dt + timedelta(hours=6)
                        start_str = start_dt.strftime("%Y-%m-%dT%H:%M")
                        end_dt = start_dt + timedelta(hours=6)
                        end_str = end_dt.strftime("%Y-%m-%dT%H:%M")
                    except Exception:
                        pass
                    # If no data returned but call succeeded, break (nothing more in range?)
                    # Actually keep fetching until rate limit. Continue.
                    if not data:
                        # No flights in this window; still try next window (may be empty gaps)
                        pass
                except Exception as e:
                    logger.info("Batch fetch failed for %s: %s", code, e)
                    # Rate limit may occur; apply exponential wait
                    logger.info("Waiting %d seconds before retry for %s", wait_time, code)
                    import time
                    time.sleep(wait_time)
                    wait_time *= 2
                    break  # Exit inner loop, schedule will retry next run
            if not fetched_any:
                logger.info("No new flights fetched for %s in this run", code)
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
