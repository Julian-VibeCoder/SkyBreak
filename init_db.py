import os
import sqlite3

def _migrate_flights(conn):
    # New schema aligned with kayak_direct JSON fields
    conn.execute("CREATE TABLE IF NOT EXISTS flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_icao TEXT, airport_name TEXT, destination_icao TEXT, destination_name TEXT, flight_direction TEXT, flight_date TEXT, flight_number TEXT, from_icao TEXT, to_icao TEXT, departure TIME, arrival TIME, arrival_date TEXT, duration_minutes INTEGER, month_key TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_flights_airport_month ON flights (airport_icao, month_key)")
    # Migration: add airport_name if missing from old schema
    try:
        conn.execute("SELECT airport_name FROM flights LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE flights ADD COLUMN airport_name TEXT")
        conn.execute("ALTER TABLE flights ADD COLUMN destination_name TEXT")

DB_FILE = os.environ.get("DB_FILE", "/data/skybreak.db")
conn = sqlite3.connect(DB_FILE)
# Migration: remove old rapid api_key and fetch_months; keep only fetch_max_months
conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
conn.execute("DELETE FROM settings WHERE key IN (?, ?)", ("api_key", "fetch_months"))
_migrate_flights(conn)
conn.execute("CREATE TABLE IF NOT EXISTS airports (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
conn.commit()
conn.close()
print("DB OK")
