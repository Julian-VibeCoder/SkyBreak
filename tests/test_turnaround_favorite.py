"""Regression test: /api/turnarounds must flag a combination as a favorite
only when it matches a stored favorite on destination AND outbound/return flight
numbers, AND on the return trip date when the favorite specifies one.

Previously the favorite match was built as
``(out_date, dest, out_f, ret_f, ret_date, r[3])`` -- position 5 duplicated the
return flight number instead of the return date, and the match only compared
four fields -- so the return trip date was never checked. A favorite returning on
a different day was wrongly flagged as a favorite of a turn ending another day.
"""
import sqlite3
import sys

sys.path.insert(0, ".")
from skybreak.app import app
from skybreak.db import db_path


def _insert_flight(direction_icao, from_icao, to_icao, dt, flight_number):
    conn = sqlite3.connect(db_path(), timeout=30.0)
    conn.execute(
        "INSERT INTO flights "
        "(airport_icao, flight_direction, departure_time, arrival_time, "
        " flight_number, from_icao, to_icao) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (direction_icao, "departure", dt, dt, flight_number, from_icao, to_icao),
    )
    conn.commit()
    conn.close()


def _insert_favorite(out_date, out_fnum, dest, start, ret_date="", ret_fnum=""):
    conn = sqlite3.connect(db_path(), timeout=30.0)
    conn.execute(
        "INSERT INTO favorite_trips "
        "(outbound_trip_date, outbound_flight_number, destination_airport, "
        " start_airport, return_trip_date, return_flight_number) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (out_date, out_fnum, dest, start, ret_date, ret_fnum),
    )
    conn.commit()
    conn.close()


def _turnaround_flags(client, max_trip_days="14"):
    # Weekday filter is 0=Mon .. 6=Sun (the endpoint computes
    # `(strftime('%w')+6)%7`). Fixtures use Friday departures / Monday returns,
    # so pin start_days=4 (Fri) and end_days=0 (Mon) rather than relying on the
    # defaults, and max_trip_days=14 keeps both a 3-day and a 10-day Monday
    # return inside the search window.
    r = client.get("/api/turnarounds", query_string={
        "start": "2026-12-01", "end": "2026-12-15",
        "start_airport": "FRA", "min_trip_days": "1", "max_trip_days": max_trip_days,
        "start_days": "4", "end_days": "0",
    })
    assert r.status_code == 200, r.get_data(as_text=True)
    flags = {
        (t["hinflug_flight_number"], t["rueckflug_flight_number"]): t["is_favorite"]
        for t in r.get_json()["turnarounds"]
    }
    return flags


def test_favorite_match_considers_return_date(clean_db):
    # One outbound (Fri) and two Mondays returns -- same outbound flight, so both
    # are returned as combinations; only the matching return flight is a favorite.
    _insert_flight("FRA", "FRA", "BER", "2026-12-04 08:00:00", "LH100")   # Fri
    _insert_flight("BER", "BER", "FRA", "2026-12-07 14:00:00", "LH205")   # Mon, favorite
    _insert_flight("BER", "BER", "FRA", "2026-12-14 14:00:00", "LH203")   # Mon, not favorite

    # Favorite returns on 2026-12-07 with LH205 (outbound LH100, dest BER).
    _insert_favorite("2026-12-04", "LH100", "BER", "FRA",
                     ret_date="2026-12-07", ret_fnum="LH205")

    with app.test_client() as client:
        flags = _turnaround_flags(client)

    # Exact match on outbound + return flight number -> favorite.
    assert flags[("LH100", "LH205")] is True
    # A different return flight (same outbound) must not be flagged as favorite.
    assert flags[("LH100", "LH203")] is False


def test_favorite_return_date_discriminates(clean_db):
    # Same outbound + return flight number but TWO return dates. A favorite tied
    # to one return date must NOT flag the turnaround returning on a different
    # date -- this is what the old bug got wrong.
    _insert_flight("FRA", "FRA", "BER", "2026-12-04 08:00:00", "LH100")   # Fri
    _insert_flight("BER", "BER", "FRA", "2026-12-07 14:00:00", "LH205")   # Mon
    _insert_flight("BER", "BER", "FRA", "2026-12-14 14:00:00", "LH205")   # Mon, later
    _insert_favorite("2026-12-04", "LH100", "BER", "FRA",
                     ret_date="2026-12-07", ret_fnum="LH205")

    with app.test_client() as client:
        r = client.get("/api/turnarounds", query_string={
            "start": "2026-12-01", "end": "2026-12-15",
            "start_airport": "FRA", "min_trip_days": "1", "max_trip_days": "14",
            "start_days": "4", "end_days": "0",
        })
    by_date = {
        str(t["rueckflug_abflug_zeit"])[:10]: t["is_favorite"]
        for t in r.get_json()["turnarounds"]
        if t["hinflug_flight_number"] == "LH100" and t["rueckflug_flight_number"] == "LH205"
    }
    assert by_date.get("2026-12-07") is True     # returns on favorite date
    assert by_date.get("2026-12-14") is False    # different return date -> not fav


def test_favorite_requires_return_flight_when_absent(clean_db):
    # A favorite without a return flight number does NOT match a concrete return
    # flight -- matching is exact on all four legs (mirrors the pre-fix
    # semantics), which the fix preserves.
    _insert_flight("FRA", "FRA", "BER", "2026-12-04 08:00:00", "LH100")   # Fri
    _insert_flight("BER", "BER", "FRA", "2026-12-07 14:00:00", "LH205")   # Mon
    _insert_favorite("2026-12-04", "LH100", "BER", "FRA",
                     ret_date="", ret_fnum="")

    with app.test_client() as client:
        flags = _turnaround_flags(client)

    assert flags.get(("LH100", "LH205")) is False
