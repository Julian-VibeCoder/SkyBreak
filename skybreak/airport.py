import re
from skybreak.airport_lookup import fetch_airport_name
from skybreak.db import connect_db

def validate_iata(code: str) -> bool:
    return bool(re.fullmatch(r"[A-Z0-9]{3}", code))

def add_airport(code: str) -> int:
    if not validate_iata(code):
        raise ValueError(f"Invalid IATA code: {code}")
    conn = connect_db()
    name = fetch_airport_name(code.upper()) or code.upper()
    cur = conn.execute("INSERT OR IGNORE INTO airports (code, name) VALUES (?, ?)", (code.upper(), name))
    conn.commit()
    conn.close()
    return cur.rowcount

def delete_airport(code: str) -> int:
    if not validate_iata(code):
        raise ValueError(f"Invalid IATA code: {code}")
    conn = connect_db()
    cur = conn.execute("DELETE FROM airports WHERE code = ?", (code.upper(),))
    # Also clean up flights for this airport to avoid orphaned data per Story 11
    conn.execute("DELETE FROM flights WHERE airport_icao = ? OR destination_icao = ?", (code.upper(), code.upper()))
    conn.commit()
    conn.close()
    return cur.rowcount

