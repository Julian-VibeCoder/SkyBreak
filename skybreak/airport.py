import logging, sqlite3, re
import os
from skybreak.airport_lookup import fetch_airport_name
from datetime import datetime, timezone
DB_PATH = os.environ.get("DB_FILE", "/data/skybreak.db")
logger = logging.getLogger(__name__)
import os

def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("CREATE TABLE IF NOT EXISTS airports (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    # Migration: remove old rapid api_key and fetch_months settings; keep only fetch_max_months
    conn.execute("DELETE FROM settings WHERE key IN (?, ?)", ("api_key", "fetch_months"))
    # Create flights table matching app.py expectations (departure_time, etc.)
    conn.execute("CREATE TABLE IF NOT EXISTS flights_new (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_icao TEXT, airport_name TEXT, destination_icao TEXT, destination_name TEXT, flight_direction TEXT, departure_time TEXT, arrival_time TEXT, duration_minutes INTEGER, flight_number TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    # Safe migration: if old schema (departure TIME instead of departure_time) exists, rebuild
    try:
        cursor = conn.execute("PRAGMA table_info(flights)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'departure' in columns and 'departure_time' not in columns:
            conn.execute("ALTER TABLE flights RENAME TO flights_old")
            conn.execute("CREATE TABLE flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_icao TEXT, airport_name TEXT, destination_icao TEXT, destination_name TEXT, flight_direction TEXT, departure_time TEXT, arrival_time TEXT, duration_minutes INTEGER, flight_number TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            try:
                conn.execute("INSERT INTO flights SELECT airport_icao, airport_name, destination_icao, destination_name, flight_direction, datetime(flight_date || ' ' || departure), datetime(flight_date || ' ' || arrival), duration_minutes, flight_number FROM flights_old")
            except Exception:
                pass
            conn.execute("DROP TABLE flights_old")
    except sqlite3.OperationalError:
        pass
    # Only rename if flights_new exists and flights does not
    try:
        conn.execute("SELECT 1 FROM flights_new LIMIT 1")
        conn.execute("SELECT 1 FROM flights LIMIT 1")
    except sqlite3.OperationalError:
        pass  # one missing
    try:
        conn.execute("SELECT 1 FROM flights LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE flights_new RENAME TO flights")
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_flights_airport ON flights (airport_icao, departure_time)")
    except sqlite3.OperationalError:
        pass  # column may not exist yet
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()
    conn.close()

def validate_iata(code: str) -> bool:
    return bool(re.fullmatch(r"[A-Z0-9]{3}", code))

def add_airport(code: str) -> int:
    if not validate_iata(code):
        raise ValueError(f"Invalid IATA code: {code}")
    init_db()
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    name = fetch_airport_name(code.upper()) or code.upper()
    cur = conn.execute("INSERT OR IGNORE INTO airports (code, name) VALUES (?, ?)", (code.upper(), name))
    conn.commit()
    conn.close()
    return cur.rowcount

def delete_airport(code: str) -> int:
    if not validate_iata(code):
        raise ValueError(f"Invalid IATA code: {code}")
    init_db()
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    cur = conn.execute("DELETE FROM airports WHERE code = ?", (code.upper(),))
    # Also clean up flights for this airport to avoid orphaned data per Story 11
    conn.execute("DELETE FROM flights WHERE airport_icao = ? OR destination_icao = ?", (code.upper(), code.upper()))
    conn.commit()
    conn.close()
    return cur.rowcount



def init_settings_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()
    conn.close()

def get_setting(key: str) -> str:
    init_settings_db()
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row[0] if row else ""

def set_setting(key: str, value: str):
    init_settings_db()
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()
