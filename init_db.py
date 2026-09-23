import os
import sqlite3

def _migrate_flights(conn):
    cols = {r[1] for r in conn.execute("PRAGMA table_info(flights)").fetchall()}
    if "arrival_time" not in cols:
        conn.execute("ALTER TABLE flights ADD COLUMN arrival_time TIMESTAMP")
    if "duration_minutes" not in cols:
        conn.execute("ALTER TABLE flights ADD COLUMN duration_minutes INTEGER")
    conn.commit()

DB_FILE = os.environ.get("DB_FILE", "/data/skybreak.db")
conn = sqlite3.connect(DB_FILE)
_migrate_flights(conn)
conn.execute("CREATE TABLE IF NOT EXISTS airports (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
conn.execute("CREATE TABLE IF NOT EXISTS flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_icao TEXT, airport_name TEXT, destination_icao TEXT, destination_name TEXT, flight_direction TEXT, departure_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, arrival_time TIMESTAMP, duration_minutes INTEGER, year_ahead INTEGER DEFAULT 365, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.commit()
conn.close()
print("DB OK")
