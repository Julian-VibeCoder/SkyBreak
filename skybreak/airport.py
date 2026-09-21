import sqlite3, re
DB_PATH = "skybreak.db"

def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("CREATE TABLE IF NOT EXISTS airports (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_icao TEXT, airport_name TEXT, destination_icao TEXT, destination_name TEXT, flight_direction TEXT, departure_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()

def validate_iata(code: str) -> bool:
    return bool(re.fullmatch(r"[A-Z0-9]{3}", code))

def add_airport(code: str) -> int:
    if not validate_iata(code):
        raise ValueError(f"Invalid IATA code: {code}")
    init_db()
    conn = sqlite3.connect(DB_PATH, timeout=5)
    cur = conn.execute("INSERT OR IGNORE INTO airports (code, name) VALUES (?, ?)", (code.upper(), code.upper()))
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
    conn.execute("DELETE FROM flights WHERE airport_icao = ?", (code.upper(),))
    conn.commit()
    conn.close()
    return cur.rowcount

def trigger_fetch_for_airport(code: str):
    import sqlite3
    from datetime import datetime, timedelta
    from skybreak.flight_scraper import fetch_flights
    from skybreak.scraper_job import save_flights
    conn = sqlite3.connect(DB_PATH, timeout=5)
    # Check if any flights exist for this airport within the next 7 days
    week_later = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    row = conn.execute("SELECT 1 FROM flights WHERE airport_icao = ? AND departure_time >= datetime('now') AND departure_time <= ? LIMIT 1", (code, week_later)).fetchone()
    conn.close()
    if row:
        # Data already available for the next week; skip API request
        return
    try:
        data = fetch_flights(code)
        if data:
            save_flights(code, data)
    except Exception:
        pass

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
