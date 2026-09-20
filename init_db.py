import sqlite3
conn=sqlite3.connect("skybreak.db")
conn.execute("CREATE TABLE IF NOT EXISTS airports (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.commit(); conn.close(); print("DB OK")
# Story 2: flights table init
try:
    conn.execute("CREATE TABLE IF NOT EXISTS flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_icao TEXT, destination_icao TEXT, flight_direction TEXT, departure_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
except Exception:
    pass
