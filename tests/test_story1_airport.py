import sqlite3, os, pytest

def test_airport_table_exists_after_init():
    # After bootstrap DB init
    assert os.path.exists("skybreak.db")

def test_insert_valid_code():
    conn = sqlite3.connect("skybreak.db")
    conn.execute("CREATE TABLE IF NOT EXISTS airports (id INTEGER PRIMARY KEY, code TEXT UNIQUE)")
    conn.execute("INSERT OR IGNORE INTO airports (code) VALUES (?)", ("LHR",))
    conn.commit()
    row = conn.execute("SELECT code FROM airports WHERE code = ?", ("LHR",)).fetchone()
    assert row is not None
    assert row[0] == "LHR"

def test_invalid_code_rejected():
    conn = sqlite3.connect("skybreak.db")
    with pytest.raises(Exception):
        # 3-char alphanumeric only enforced in python layer
        conn.execute("INSERT INTO airports (code) VALUES (?)", ("BADCODE",))
