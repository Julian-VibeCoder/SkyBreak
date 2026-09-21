import sqlite3, os
from skybreak.airport import add_airport, delete_airport, DB_PATH

def test_airports_persist_in_correct_db():
    # Ensure DB file is at container-mounted path
    assert DB_PATH == "/data/skybreak.db"
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM airports WHERE code IN ('TST', 'TMP')")
    conn.commit()
    conn.close()
    add_airport("TST")
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT code, name FROM airports WHERE code = ?", ("TST",)).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "TST"
    assert row[1]  # name should be fetched, not just code
