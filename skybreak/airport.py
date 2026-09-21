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
    trigger_fetch_for_airport(code.upper())
    return cur.rowcount

def trigger_fetch_for_airport(code: str):
    from skybreak.flight_scraper import fetch_flights
    from skybreak.scraper_job import save_flights
    try:
        data = fetch_flights(code)
        if data:
            save_flights(code, data)
    except Exception:
        pass
