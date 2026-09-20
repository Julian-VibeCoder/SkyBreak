import sqlite3
<<<<<<< HEAD
conn = sqlite3.connect("skybreak.db")
conn.execute("CREATE TABLE IF NOT EXISTS airports (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_code TEXT NOT NULL, destination_icao TEXT NOT NULL, scheduled_departure TIMESTAMP, scheduled_arrival TIMESTAMP, flight_direction TEXT NOT NULL, year_ahead INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.commit()
conn.close()
print("DB OK")
=======
conn=sqlite3.connect("skybreak.db")
conn.execute("CREATE TABLE IF NOT EXISTS airports (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.commit(); conn.close(); print("DB OK")
# Story 2: flights table init
try:
    conn.execute("CREATE TABLE IF NOT EXISTS flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_icao TEXT, airport_name TEXT, destination_icao TEXT, destination_name TEXT, flight_direction TEXT, departure_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
except Exception:
    pass
>>>>>>> feature/story2-complete
