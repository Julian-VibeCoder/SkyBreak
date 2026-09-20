import sqlite3
conn = sqlite3.connect("skybreak.db")
conn.execute("CREATE TABLE IF NOT EXISTS airports (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.execute("CREATE TABLE IF NOT EXISTS flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_code TEXT NOT NULL, destination_icao TEXT NOT NULL, scheduled_departure TIMESTAMP, scheduled_arrival TIMESTAMP, flight_direction TEXT NOT NULL, year_ahead INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.commit()
conn.close()
print("DB OK")
