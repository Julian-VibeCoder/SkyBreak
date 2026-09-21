import logging, sqlite3, re
from skybreak.airport_lookup import fetch_airport_name
DB_PATH = "/data/skybreak.db"
logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("CREATE TABLE IF NOT EXISTS airports (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_icao TEXT, airport_name TEXT, destination_icao TEXT, destination_name TEXT, flight_direction TEXT, departure_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    # Ensure columns exist for older DBs
    try:
        conn.execute("SELECT airport_name FROM flights LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE flights ADD COLUMN airport_name TEXT")
    try:
        conn.execute("SELECT destination_name FROM flights LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE flights ADD COLUMN destination_name TEXT")
    try:
        conn.execute("SELECT flight_number FROM flights LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE flights ADD COLUMN flight_number TEXT")
    try:
        conn.execute("SELECT year_ahead FROM flights LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE flights ADD COLUMN year_ahead INTEGER DEFAULT 365")
    conn.commit()
    conn.close()

def validate_iata(code: str) -> bool:
    return bool(re.fullmatch(r"[A-Z0-9]{3}", code))

def add_airport(code: str) -> int:
    if not validate_iata(code):
        raise ValueError(f"Invalid IATA code: {code}")
    init_db()
    conn = sqlite3.connect(DB_PATH, timeout=5)
    name = fetch_airport_name(code.upper()) or code.upper()
    cur = conn.execute("INSERT OR IGNORE INTO airports (code, name) VALUES (?, ?)", (code.upper(), name))
    conn.commit()
    conn.close()
    trigger_fetch_for_airport(code.upper())
    return cur.rowcount

def delete_airport(code: str) -> int:
    if not validate_iata(code):
        raise ValueError(f"Invalid IATA code: {code}")
    init_db()
    conn = sqlite3.connect(DB_PATH, timeout=5)
    cur = conn.execute("DELETE FROM airports WHERE code = ?", (code.upper(),))
    # Also clean up flights for this airport to avoid orphaned data per Story 11
    conn.execute("DELETE FROM flights WHERE airport_icao = ? OR destination_icao = ?", (code.upper(), code.upper()))
    conn.commit()
    conn.close()
    return cur.rowcount

def trigger_fetch_for_airport(code: str):
    import sqlite3, time
    from skybreak.scraper_job import get_latest_flight_time, save_flights
    from datetime import datetime, timedelta
    from skybreak.flight_scraper import fetch_flights

    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn2 = sqlite3.connect(DB_PATH, timeout=5)
    row_max = conn2.execute("SELECT MAX(departure_time) FROM flights WHERE airport_icao = ?", (code,)).fetchone()
    conn2.close()
    if row_max and row_max[0]:
        latest_dt = datetime.fromisoformat(str(row_max[0]).replace("Z", "+00:00"))
        if latest_dt.tzinfo is not None:
            latest_dt = latest_dt.replace(tzinfo=None)
        start_dt = latest_dt - timedelta(hours=6)
    else:
                start_dt = datetime.utcnow()
    max_days_raw = get_setting("fetch_max_days")
    try:
        max_days = int(max_days_raw)
    except Exception:
        max_days = 7
    max_days = max(1, min(max_days, 365))
    target_end = start_dt + timedelta(days=max_days)
    wait_time = 0  # start directly until first rate limit hits; then apply backoff
    current_start = start_dt
    fetched_any = False
    while True:
        current_end = current_start + timedelta(hours=6)
        if current_start >= target_end:
            break
        start_str = current_start.strftime("%Y-%m-%dT%H:%M")
        end_str = current_end.strftime("%Y-%m-%dT%H:%M")
        try:
            data = fetch_flights(code, start_time_str=start_str, end_time_str=end_str)
            if data:
                save_flights(code, data)
                fetched_any = True
            current_start = current_end
            if current_start >= target_end:
                break
        except Exception as e:
            # Rate limit retry with backoff
            if "429" in str(e):
                logger.info("Rate limit (429) hit for %s at window %s; backing off %ds", code, start_str, wait_time if wait_time > 0 else 30*60)
            # First rate limit: start at 30m, then double
            if wait_time == 0:
                wait_time = 30 * 60
            time.sleep(wait_time)
            wait_time *= 2
    conn.close()

def init_settings_db():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()
    conn.close()

def get_setting(key: str) -> str:
    init_settings_db()
    conn = sqlite3.connect(DB_PATH, timeout=5)
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row[0] if row else ""

def set_setting(key: str, value: str):
    init_settings_db()
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()
