"""Preis eines Direktflugs per Flugnummer über fast-flights 3.x.

Aufruf:
    from flight_price import get_flight_price
    get_flight_price("ARN", "FRA", "2026-10-04", "LH805")  # -> 183.0 oder None
"""
import json, logging, os, random, re, sqlite3, threading, time
from collections import OrderedDict

from fast_flights import FlightQuery, Passengers, create_query
from primp import Client
from selectolax.lexbor import LexborHTMLParser

logger = logging.getLogger(__name__)
DB_PATH = os.environ.get("DB_FILE", "/data/skybreak.db")
FLIGHTS_URL = "https://www.google.com/travel/flights"

# Backoff bei 429: 15 s, 45 s, 2:15, 6:45, ~20 min, dann 60 min (je ±20 % Jitter)
BACKOFF_BASE = 15.0
BACKOFF_FACTOR = 3.0
BACKOFF_MAX = 3600.0
MAX_RATE_LIMIT_RETRIES = 8  # pro Aufruf; danach RuntimeError

_client = None
# Globaler Cooldown: gilt für alle Aufrufe, damit die Batch-Schleife nicht weiterhämmert
_rl_lock = threading.Lock()
_blocked_until = 0.0     # time.monotonic()
_consecutive_429 = 0     # wird erst nach erfolgreichem Request zurückgesetzt

# Cache der Suchergebnisse pro (from, to, date): mehrere Flugnummern derselben Suche -> 1 Request
CACHE_MAX_ENTRIES = 500
CACHE_TTL = 3600.0
_cache = OrderedDict()   # key -> (time.monotonic(), Preistabelle); älteste zuerst
_cache_lock = threading.Lock()

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

def _retry_after_seconds(res):
    """Retry-After-Header in Sekunden (nur Zahlenform), sonst None."""
    try:
        value = res.headers.get("retry-after") or res.headers.get("Retry-After")
        return max(0.0, float(value)) if value else None
    except (AttributeError, TypeError, ValueError):
        return None

def _wait_for_cooldown():
    with _rl_lock:
        remaining = _blocked_until - time.monotonic()
    if remaining > 0:
        logger.info("Rate-Limit-Cooldown aktiv, warte %.0f s", remaining)
        time.sleep(remaining)

def _register_rate_limit(res):
    """Cooldown verlängern (exponentiell über aufeinanderfolgende 429) und Session verwerfen."""
    global _blocked_until, _consecutive_429, _client
    with _rl_lock:
        _consecutive_429 += 1
        delay = min(BACKOFF_MAX, BACKOFF_BASE * BACKOFF_FACTOR ** (_consecutive_429 - 1))
        delay *= random.uniform(0.8, 1.2)
        retry_after = _retry_after_seconds(res)
        if retry_after is not None:
            delay = max(delay, retry_after)
        _blocked_until = max(_blocked_until, time.monotonic() + delay)
        _client = None  # neue Session/Cookies beim nächsten Versuch
        logger.warning("Rate-Limit von Google (%d. in Folge), Cooldown %.0f s", _consecutive_429, delay)

def _fetch(params):
    """GET mit globalem Cooldown und Backoff bei 429 / Google-'sorry'-Seite. Blockiert ggf. lange."""
    global _consecutive_429
    for _ in range(MAX_RATE_LIMIT_RETRIES + 1):
        _wait_for_cooldown()
        res = _get_client().get(FLIGHTS_URL, params=params)
        if res.status_code == 429 or "/sorry/" in str(res.url):
            _register_rate_limit(res)
            continue
        with _rl_lock:
            _consecutive_429 = 0
        return res
    raise RuntimeError(f"Rate-Limit: nach {MAX_RATE_LIMIT_RETRIES} Wiederholungen weiterhin HTTP 429")

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

def _search(from_airport, to_airport, date):
    q = create_query(flights=[FlightQuery(date=date, from_airport=from_airport, to_airport=to_airport, max_stops=0)], seat="economy", trip="one-way", passengers=Passengers(adults=1), language="de", currency="EUR")
    res = _fetch(q.params())
    if res.status_code != 200:
        raise RuntimeError(f"HTTP {res.status_code}")
    if "consent.google.com" in str(res.url):
        raise RuntimeError("Google Consent-Seite erhalten (SOCS-Cookie fehlt/ungültig)")
    return _load_payload(res.text)

def _extract_prices(payload):
    """Suchergebnis -> {(carrier, number, (y, m, d)): günstigster Preis} für alle Direktflüge."""
    prices = {}
    for k in _iter_entries(payload or []):
        try:
            segments = k[0][2]
            if len(segments) != 1:
                continue
            seg = segments[0]
            # seg[22] = ["LH", "805", None, "Lufthansa"], seg[20] = [2026, 10, 4]
            key = (seg[22][0].upper(), seg[22][1].lstrip("0"), tuple(seg[20]))
            price = k[1][0][1]
            if price is not None:
                prices[key] = min(float(price), prices.get(key, float("inf")))
        except (IndexError, TypeError, AttributeError) as e:
            logger.debug("Eintrag übersprungen: %s", e)
    return prices

def _get_prices(from_airport, to_airport, date):
    """Preistabelle aus dem Cache (max. CACHE_TTL alt) oder frisch von Google. Fehler werden nicht gecacht."""
    key = (from_airport, to_airport, date)
    with _cache_lock:
        hit = _cache.get(key)
        if hit and time.monotonic() - hit[0] < CACHE_TTL:
            _cache.move_to_end(key)
            logger.debug("Cache-Treffer %s", key)
            return hit[1]
    prices = _extract_prices(_search(from_airport, to_airport, date))
    with _cache_lock:
        _cache[key] = (time.monotonic(), prices)
        _cache.move_to_end(key)
        while len(_cache) > CACHE_MAX_ENTRIES:
            _cache.popitem(last=False)
    return prices

def get_flight_price(from_airport, to_airport, date, flight_number):
    """Günstigster Economy-Preis (EUR, 1 Erwachsener) für einen Direktflug.

    date: 'YYYY-MM-DD'. Gibt None zurück, wenn der Flug nicht im Suchergebnis ist.
    Wirft RuntimeError bei HTTP-Fehlern oder Consent-Seite. Bei Rate-Limit (429) wird
    intern mit Backoff gewartet und wiederholt; der Aufruf kann dann lange blockieren.
    Suchergebnisse werden pro Route/Datum bis zu 1 h zwischengespeichert (max. 500 Einträge).
    """
    carrier, number = _normalize_flight_number(flight_number)
    wanted_date = tuple(int(p) for p in date.split("-"))
    prices = _get_prices(from_airport.upper(), to_airport.upper(), date)
    return prices.get((carrier, number, wanted_date))
