import sqlite3
DB_PATH = "skybreak.db"

def test_flights_table_exists():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='flights'")
    assert cursor.fetchone() is not None, "flights table missing"
    conn.close()

def test_flights_columns():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("PRAGMA table_info(flights)")
    rows = cursor.fetchall()
    conn.close()
    cols = {r[1]: r for r in rows}
    for c in ["id","airport_code","destination_icao","scheduled_departure","scheduled_arrival","flight_direction","year_ahead","created_at"]:
        assert c in cols, f"Spalte {c} fehlt"
