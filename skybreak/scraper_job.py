from datetime import datetime, timedelta, timezone
import logging
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from skybreak.flight_scraper import fetch_flights

DB_PATH = "/data/skybreak.db"
logger = logging.getLogger(__name__)

def get_latest_flight_time(airport_code):
    conn = sqlite3.connect(DB_PATH, timeout=5)
    # Latest flight in db for a given airport minus 6h as timestamp for each run
    row = conn.execute(
        "SELECT MAX(departure_time) FROM flights WHERE airport_icao = ?",
        (airport_code,)
    ).fetchone()
    conn.close()
    if row and row[0]:
        latest = row[0]
        # minus 6h
        dt = datetime.fromisoformat(str(latest).replace("Z", "+00:00"))
        # Assume DB stores UTC; keep tzinfo for arithmetic then format as UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (dt - timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M")
    return None

def save_flights(airport_code, flights):
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("CREATE TABLE IF NOT EXISTS flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_icao TEXT, airport_name TEXT, destination_icao TEXT, destination_name TEXT, flight_direction TEXT, departure_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, flight_number TEXT, year_ahead INTEGER DEFAULT 365, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    for f in flights:
        try:
            dep = f.get("departure") or {}
            arr = f.get("arrival") or {}
            dep_time_raw = dep.get("scheduledTime") or dep.get("scheduledTime", {})
            # Parse scheduledTime: could be string or dict with "utc"/"local" keys
            if isinstance(dep_time_raw, dict):
                dep_time = dep_time_raw.get("utc") or dep_time_raw.get("local", "")
            else:
                dep_time = dep_time_raw or ""
            # Normalize timezone suffix if it's a 19-char string without tz info
            if dep_time and not dep_time.endswith("Z") and "+" not in dep_time[-6:] and len(dep_time) == 19:
                dep_time += "+00:00"
            arr_time_raw = arr.get("scheduledTime") or arr.get("scheduledTime", {})
            if isinstance(arr_time_raw, dict):
                arr_time = arr_time_raw.get("utc") or arr_time_raw.get("local", "")
            else:
                arr_time = arr_time_raw or ""
            if arr_time and not arr_time.endswith("Z") and "+" not in arr_time[-6:] and len(arr_time) == 19:
                arr_time += "+00:00"
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
            flight_number = f.get("number") or f.get("flightNumber") or f.get("flight_number") or ""
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
                "INSERT OR IGNORE INTO flights (airport_icao, airport_name, destination_icao, destination_name, flight_direction, departure_time, flight_number, year_ahead) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (airport_code, airport_name, dest_icao, dest_name, direction, dep_time or arr_time, flight_number, 365)
            )
            logger.debug("Saved flight: %s->%s %s at %s", airport_code, dest_icao, flight_number, dep_time)
        except Exception as e:
            logger.warning("Failed to save flight for %s: %s", airport_code, e)
            continue
    conn.commit()
    conn.close()

def scrape_all_airports():
    import logging, sqlite3, time
    logger = logging.getLogger(__name__)
    conn = sqlite3.connect(DB_PATH, timeout=5)
    rows = conn.execute("SELECT code FROM airports").fetchall()
    conn.close()
    for (code,) in rows:
        try:
            # If there are missing flights (data not fetched completely for next 365 days) fetch until api restricts access due to rate limit
            max_days_raw = get_setting("fetch_max_days")
            try:
                max_days = int(max_days_raw)
            except Exception:
                max_days = 7
            max_days = max(1, min(max_days, 365))
            conn2 = sqlite3.connect(DB_PATH, timeout=5)
            row_max = conn2.execute("SELECT MAX(departure_time) FROM flights WHERE airport_icao = ?", (code,)).fetchone()
            conn2.close()
            # If there are no flights in the db, use "now" as start time stamp
            if row_max and row_max[0]:
                latest_dt = datetime.fromisoformat(str(row_max[0]).replace("Z", "+00:00"))
                if latest_dt.tzinfo is not None:
                    latest_dt = latest_dt.replace(tzinfo=None)
                # Use the latest flight in the db for a given airport minus 6h as timestamp for each run of the schedule
                start_dt = latest_dt - timedelta(hours=6)
            else:
                start_dt = datetime.now(timezone.utc)
            # We are still only able to fix 6 hours with a single api call
            # Fetch continuously until we cover 365 days ahead or rate limit stops us
            target_end = start_dt + timedelta(days=max_days)
            wait_time = 0  # start directly until first rate limit hits; then apply backoff
            # We must fetch all windows continuously; when successful, next 6h directly after previous
            current_start = start_dt
            fetched_any = False
            # Continue fetching until target 365 days ahead covered or persistent rate limit
            while True:
                current_end = current_start + timedelta(hours=6)
                # Stop if we've covered the full 365-day range
                if current_start >= target_end:
                    break
                start_str = current_start.strftime("%Y-%m-%dT%H:%M")
                end_str = current_end.strftime("%Y-%m-%dT%H:%M")
                try:
                    data = fetch_flights(code, start_time_str=start_str, end_time_str=end_str)
                    if data:
                        save_flights(code, data)
                        fetched_any = True
                        logger.info("Batch fetched %d flights for %s (window %s to %s)", len(data), code, start_str, end_str)
                        current_start = current_end
                        if current_start >= target_end:
                            break
                    else:
                        # Leere API-Antwort: Fenster nicht verschieben -> keine Lücke
                        # Aber harte fetch_max_days-Grenze nicht ignorieren
                        if current_start + timedelta(hours=6) >= target_end:
                            # Keine Daten mehr im erlaubten Fenster: abbrechen
                            current_start = current_end
                            break
                except Exception as e:
                    # Rate limit or other failure
                    logger.info("API call failed for %s at window %s: %s", code, start_str, e)
                    if "429" in str(e):
                        logger.warning("Rate limit (429) hit for %s at window %s; backing off %ds before retry", code, start_str, wait_time if wait_time > 0 else 30*60)
                    # Wait before retry; double each time rate limit still occurs
                    logger.info("Waiting %d seconds for %s before retry", wait_time, code)
                    # First rate limit: start at 30m, then double
                    if wait_time == 0:
                        wait_time = 30 * 60
                    time.sleep(wait_time)
                    wait_time *= 2
                    # Try same window again after wait; don't advance until successful
                    # Continue loop; same current_start and current_end
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
