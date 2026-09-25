from skybreak.scraper_job import save_flights
import os, sqlite3

def test_save_flights_parses_nested():
    flights = [{
        "departure": {"scheduledTime": {"utc": "2026-09-21 10:25Z"}, "airport": {"icao": "FKB"}},
        "arrival": {"airport": {"icao": "LEPA"}, "scheduledTime": {"utc": "2026-09-21 11:20Z"}},
        "number": "EW 6805"
    }]
    save_flights("FKB", flights)
    import sqlite3
    conn = sqlite3.connect(os.environ.get("DB_FILE", "/opt/skybreak/skybreak.db"))
    rows = conn.execute("SELECT airport_icao, destination_icao, flight_direction, departure_time FROM flights WHERE airport_icao='FKB' AND destination_icao='LEPA' AND flight_direction='departure'").fetchall()
    conn.close()
    assert len(rows) >= 1
    assert rows[0][0] == "FKB"
    assert rows[0][1] == "LEPA"
    assert rows[0][2] == "departure"
