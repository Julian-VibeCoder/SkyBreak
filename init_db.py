import sqlite3
conn=sqlite3.connect("skybreak.db")
conn.execute("CREATE TABLE IF NOT EXISTS airports (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.commit(); conn.close(); print("DB OK")
