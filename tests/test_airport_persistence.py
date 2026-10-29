import os
from skybreak.airport import add_airport
from skybreak.db import db_path, connect_db

def test_airports_persist_in_correct_db():
    # The DB path comes from the environment (conftest sets it to a writable temp
    # file in tests; the container sets /data/skybreak.db). db_path() reads the
    # env at call time, so it must match the test harness's setting.
    assert db_path() == os.environ["DB_FILE"]
    conn = connect_db()
    conn.execute("DELETE FROM airports WHERE code IN ('TST', 'TMP')")
    conn.commit()
    conn.close()
    add_airport("TST")
    conn = connect_db()
    row = conn.execute("SELECT code, name FROM airports WHERE code = ?", ("TST",)).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "TST"
    assert row[1]  # name should be fetched (or fall back to the code), not empty
