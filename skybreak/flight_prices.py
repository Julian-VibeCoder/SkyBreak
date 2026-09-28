"""Preisabfrage über fast-flights 3.x (keine Fallbacks/Playwright)."""
import sqlite3, os, logging
from datetime import datetime
logger = logging.getLogger(__name__)
DB_PATH = os.environ.get("DB_FILE", "/data/skybreak.db")

def _load_cookie():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        row = conn.execute("SELECT value FROM settings WHERE key='google_consent_cookie'").fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None

from fast_flights import FlightQuery, Passengers, Query, create_query
from fast_flights.exceptions import FlightsNotFound
from fast_flights.parser import parse

FLIGHTS_URL = "https://www.google.com/travel/flights"

_cookie_value = _load_cookie()
from primp import Client
_client = Client(impersonate="chrome_145", impersonate_os="macos", referer=True, cookie_store=True, verify=False)
if _cookie_value:
    _client.set_cookies("https://www.google.com", {"SOCS": _cookie_value})
    logger.info("Cookie gesetzt")
else:
    logger.info("Kein Cookie in DB")

def _split_date_time(value):
    """'2026-10-02 12:05' / '2026-10-02T12:05' -> ('2026-10-02', (12, 5)); ohne Uhrzeit -> (date, None)."""
    s = str(value or "").strip().replace("T", " ")
    date_part, _, time_part = s.partition(" ")
    if not time_part:
        return date_part, None
    hh, mm = time_part.split(":")[:2]
    return date_part, (int(hh), int(mm))

def _get_exact_price(q: Query, dep_time=None):
    """Günstigster Preis der Suche; mit dep_time=(h, m) nur Flüge mit genau dieser Abflugzeit."""
    res = _client.get(FLIGHTS_URL, params=q.params())
    assert res.status_code == 200, f"{res.status_code}"
    if "consent.google.com" in str(res.url):
        raise RuntimeError("Google Consent-Seite erhalten (SOCS-Cookie fehlt/ungültig)")
    try:
        result = parse(res.text)
    except FlightsNotFound:
        return None
    prices = [
        float(f.price) for f in result
        if f.price is not None and f.flights
        and (dep_time is None or tuple(f.flights[0].departure.time) == tuple(dep_time))
    ]
    return min(prices) if prices else None

def fetch_prices_favorite(favorite_id, force=False):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        if not force:
            row = conn.execute("SELECT fetched_at FROM favorite_trip_prices WHERE favorite_id = ? ORDER BY fetched_at DESC LIMIT 1", (favorite_id,)).fetchone()
            if row and row[0]:
                fetched_dt = datetime.fromisoformat(str(row[0]).replace("Z","+00:00")) if row[0] else None
                if fetched_dt:
                    age = (datetime.now(fetched_dt.tzinfo)-fetched_dt).total_seconds()/3600 if fetched_dt.tzinfo else (datetime.now()-fetched_dt).total_seconds()/3600
                    if age < 12:
                        conn.close(); return get_prices_for_favorite(favorite_id)
        row = conn.execute("SELECT trip_date, start_airport, destination_airport, outbound_trip_date, return_trip_date, return_time FROM favorite_trips WHERE id = ?", (favorite_id,)).fetchone()
        conn.close()
        if not row: return {"favorite_id":favorite_id,"error":"Favorit nicht gefunden"}
        trip_date, start_airport, dest_airport, out_trip_date, ret_trip_date, return_time_db = row
        if not start_airport or not dest_airport: return {"favorite_id":favorite_id,"error":"Flughafen fehlt"}
        out_date, out_time = _split_date_time(out_trip_date or trip_date)
        ret_date, _ret_time_from_date = _split_date_time(ret_trip_date or trip_date)
        # Rückflug-Abflugzeit explizit aus Favorit-Spalte return_time bevorzugen
        ret_time = None
        if return_time_db and isinstance(return_time_db, str) and ":" in str(return_time_db):
            time_str = str(return_time_db).strip()
            # Wenn nur Uhrzeit (z.B. 16:35) ohne Datum, mit ret_date kombinieren
            if len(time_str) <= 5 and time_str.count(':') == 1:
                combined = f"{ret_date or trip_date} {time_str}"
                _, ret_time = _split_date_time(combined)
            else:
                _, ret_time = _split_date_time(str(return_time_db))
        elif _ret_time_from_date:
            ret_time = _ret_time_from_date
        q_out = create_query(flights=[FlightQuery(date=out_date, from_airport=str(start_airport), to_airport=str(dest_airport), max_stops=0)], seat="economy", trip="one-way", passengers=Passengers(adults=1), language="de", currency="EUR")
        q_ret = create_query(flights=[FlightQuery(date=ret_date, from_airport=str(dest_airport), to_airport=str(start_airport), max_stops=0)], seat="economy", trip="one-way", passengers=Passengers(adults=1), language="de", currency="EUR")
        price_out = None
        price_ret = None
        try:
            price_out = _get_exact_price(q_out, out_time)
        except Exception as e: logger.warning("Hinflug Fehler: %s", e)
        try:
            price_ret = _get_exact_price(q_ret, ret_time)
        except Exception as e: logger.warning("Rückflug Fehler: %s", e)
        total = (price_out or 0)+(price_ret or 0) if (price_out is not None or price_ret is not None) else None
        if price_out is not None or price_ret is not None:
            conn = sqlite3.connect(DB_PATH, timeout=30.0)
            conn.execute("INSERT OR REPLACE INTO favorite_trip_prices (favorite_id, price_outbound, price_return, price_total, currency, fetched_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)", (favorite_id, price_out, price_ret, total, "EUR"))
            conn.commit(); conn.close()
        return {"favorite_id":favorite_id,"price_outbound":price_out,"price_return":price_ret,"price_total":total,"currency":"EUR","fetched_at":datetime.now().isoformat()}
    except Exception as e:
        logger.exception("Fehler %s: %s", favorite_id, e)
        return {"favorite_id":favorite_id,"error":str(e)}
def get_prices_for_favorite(favorite_id):
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    row = conn.execute("SELECT price_outbound, price_return, price_total, currency, fetched_at FROM favorite_trip_prices WHERE favorite_id = ? ORDER BY fetched_at DESC LIMIT 1", (favorite_id,)).fetchone()
    conn.close()
    if row: return {"favorite_id":favorite_id,"price_outbound":row[0],"price_return":row[1],"price_total":row[2],"currency":row[3],"fetched_at":row[4]}
    return None
