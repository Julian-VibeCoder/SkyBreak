from skybreak.scraper_job import save_flights

def test_save_flights_parses_nested():
    flights = [{
        "departure": {"scheduledTime": {"utc": "2026-09-21 10:25Z"}, "airport": {"icao": "FKB"}},
        "arrival": {"airport": {"icao": "LEPA"}, "scheduledTime": {"utc": "2026-09-21 11:20Z"}},
        "number": "EW 6805"
    }]
    save_flights("FKB", flights)
    import sqlite3
    conn = sqlite3.connect("/data/skybreak.db")
    rows = conn.execute("SELECT airport_icao, destination_icao, flight_direction, departure_time FROM flights WHERE airport_icao='FKB'").fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0][0] == "FKB"
    assert rows[0][1] == "LEPA"
    assert rows[0][2] == "departure"
