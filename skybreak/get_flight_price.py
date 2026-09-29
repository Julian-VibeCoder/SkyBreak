"""Preis eines Direktflugs per Flugnummer über fast-flights 3.x.

Aufruf:
    from flight_price import get_flight_price
    get_flight_price("ARN", "FRA", "2026-10-04", "LH805")  # -> 183.0 oder None
"""
import json, logging, os, re, sqlite3

from fast_flights import FlightQuery, Passengers, create_query
from primp import Client
from selectolax.lexbor import LexborHTMLParser

logger = logging.getLogger(__name__)
DB_PATH = os.environ.get("DB_FILE", "/data/skybreak.db")
FLIGHTS_URL = "https://www.google.com/travel/flights"

_client = None

def _load_cookie():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        row = conn.execute("SELECT value FROM settings WHERE key='google_consent_cookie'").fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None

def _get_client():
    global _client
    if _client is None:
        _client = Client(impersonate="chrome_145", impersonate_os="macos", referer=True, cookie_store=True, verify=False)
        cookie = _load_cookie()
        if cookie:
            _client.set_cookies("https://www.google.com", {"SOCS": cookie})
        else:
            logger.info("Kein Cookie in DB")
    return _client

def _normalize_flight_number(value):
    """'LH805' / 'lh 0805' -> ('LH', '805')."""
    # Airline-Code: IATA (2 Zeichen, mind. ein Buchstabe, z. B. LH, U2, 4U) oder ICAO (3 Buchstaben)
    m = re.fullmatch(r"([A-Z]{2,3}|[A-Z]\d|\d[A-Z])\s*0*(\d{1,4})", str(value or "").strip().upper())
    if not m:
        raise ValueError(f"Ungültige Flugnummer: {value!r}")
    return m.group(1), m.group(2)

def _load_payload(html):
    """JSON-Array aus <script class="ds:1"> (AF_initDataCallback({... data: [...], sideChannel: {}}))."""
    script = LexborHTMLParser(html).css_first(r"script.ds\:1")
    if script is None:
        raise RuntimeError("Keine Flugdaten in der Antwort (script ds:1 fehlt)")
    data = script.text().split("data:", 1)[1].rsplit(",", 1)[0]
    if data.endswith("errorHasStatus: true"):
        return None
    return json.loads(data)

def _iter_entries(payload):
    """Einträge aus payload[3][0] ('Beste Flüge') und payload[2][0] ('Weitere Flüge')."""
    for idx in (3, 2):
        block = payload[idx] if len(payload) > idx else None
        if block and block[0]:
            yield from block[0]

def get_flight_price(from_airport, to_airport, date, flight_number):
    """Günstigster Economy-Preis (EUR, 1 Erwachsener) für einen Direktflug.

    date: 'YYYY-MM-DD'. Gibt None zurück, wenn der Flug nicht im Suchergebnis ist.
    Wirft RuntimeError bei HTTP-Fehlern oder Consent-Seite.
    """
    carrier, number = _normalize_flight_number(flight_number)
    wanted_date = [int(p) for p in date.split("-")]
    q = create_query(flights=[FlightQuery(date=date, from_airport=from_airport.upper(), to_airport=to_airport.upper(), max_stops=0)], seat="economy", trip="one-way", passengers=Passengers(adults=1), language="de", currency="EUR")
    res = _get_client().get(FLIGHTS_URL, params=q.params())
    if res.status_code != 200:
        raise RuntimeError(f"HTTP {res.status_code}")
    if "consent.google.com" in str(res.url):
        raise RuntimeError("Google Consent-Seite erhalten (SOCS-Cookie fehlt/ungültig)")
    payload = _load_payload(res.text)
    if payload is None:
        return None
    prices = []
    for k in _iter_entries(payload):
        try:
            segments = k[0][2]
            if len(segments) != 1:
                continue
            seg = segments[0]
            # seg[22] = ["LH", "805", None, "Lufthansa"], seg[20] = [2026, 10, 4]
            if seg[22][0].upper() != carrier or seg[22][1].lstrip("0") != number or list(seg[20]) != wanted_date:
                continue
            price = k[1][0][1]
            if price is not None:
                prices.append(float(price))
        except (IndexError, TypeError, AttributeError) as e:
            logger.debug("Eintrag übersprungen: %s", e)
    return min(prices) if prices else None
