import sqlite3, os
DB_PATH = os.environ.get("DB_FILE", "/data/skybreak.db")

def test_flights_table_exists():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='flights'")
    assert cursor.fetchone() is not None, "flights table missing"
    conn.close()
