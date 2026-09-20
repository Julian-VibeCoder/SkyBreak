import sqlite3, re
DB_PATH = "skybreak.db"

def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("CREATE TABLE IF NOT EXISTS airports (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()

def validate_iata(code: str) -> bool:
    return bool(re.fullmatch(r"[A-Z0-9]{3}", code))

def add_airport(code: str) -> int:
    if not validate_iata(code):
        raise ValueError(f"Invalid IATA code: {code}")
    init_db()
    conn = sqlite3.connect(DB_PATH, timeout=5)
    cur = conn.execute("INSERT OR IGNORE INTO airports (code) VALUES (?)", (code.upper(),))
    conn.commit()
    conn.close()
    return cur.rowcount

def delete_airport(code: str) -> int:
    if not validate_iata(code):
        raise ValueError(f"Invalid IATA code: {code}")
    init_db()
    conn = sqlite3.connect(DB_PATH, timeout=5)
    cur = conn.execute("DELETE FROM airports WHERE code = ?", (code.upper(),))
    conn.commit()
    conn.close()
    return cur.rowcount
