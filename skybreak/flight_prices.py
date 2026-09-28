"""Preisabfrage über fast-flights 3.x (v3-API)."""
import sqlite3, os, logging, json
from datetime import datetime
logger = logging.getLogger(__name__)
DB_PATH = os.environ.get("DB_FILE", "/data/skybreak.db")

CONSENT_COOKIES = {"SOCS": "CAESHAgBEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmRlIAEaBgiAo_CmBg"}

from fast_flights import FlightQuery, Passengers, create_query, get_flights
from fast_flights.fetcher import URL
from fast_flights.integrations import FetchIntegration
from primp import Client
from selectolax.lexbor import LexborHTMLParser

class DirectFetch(FetchIntegration):
    def __init__(self, proxy=None):
        self.client = Client(impersonate="chrome_145", impersonate_os="macos",
                             referer=True, proxy=proxy, cookie_store=True)
        self.client.set_cookies("https://www.google.com", CONSENT_COOKIES)
    def fetch_html(self, q, /):
        params = q.params() if hasattr(q, "params") else {"q": q}
        return self.client.get(URL, params=params).text

class PlaywrightFetch(FetchIntegration):
    def __init__(self, proxy=None, insecure=False):
        self.proxy = proxy; self.insecure = insecure
    def fetch_html(self, q, /):
        from playwright.sync_api import sync_playwright
        url = q.url() if hasattr(q, "url") else f"{URL}?q={q}"
        with sync_playwright() as p:
            browser = p.chromium.launch(proxy={"server": self.proxy} if self.proxy else None)
            try:
                ctx = browser.new_context(ignore_https_errors=self.insecure)
                ctx.add_cookies([{"name":k,"value":v,"domain":".google.com","path":"/"} for k,v in CONSENT_COOKIES.items()])
                page = ctx.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_selector(r"script.ds\:1", state="attached", timeout=30_000)
                return page.content()
            finally:
                browser.close()

def parse_offers(html):
    script = LexborHTMLParser(html).css_first(r"script.ds\:1")
    if script is None:
        title = LexborHTMLParser(html).css_first("title")
        raise RuntimeError("keine Flugdaten (Seite: %r)" % (title.text() if title else "?"))
    data = script.text().split("data:", 1)[1].rsplit(",", 1)[0]
    if data.endswith("errorHasStatus: true"):
        return []
    payload = json.loads(data)
    offers = []
    for section in (payload[2], payload[3]):
        for item in (section or [None])[0] or []:
            itinerary, price = item[0], item[1][0][1]
            segments = []
            for s in itinerary[2]:
                dep = (s[8] or []) + [None, None]
                arr = (s[10] or []) + [None, None]
                segments.append({
                    "flight": (s[22][0] + s[22][1]) if s[22] else None,
                    "from": s[3], "to": s[6],
                    "date": "%04d-%02d-%02d" % tuple(s[20]),
                    "dep": "%02d:%02d" % (dep[0] or 0, dep[1] or 0),
                    "arr": "%02d:%02d" % (arr[0] or 0, arr[1] or 0),
                    "aircraft": s[17],
                })
            offers.append({"price": price, "segments": segments})
    return offers

def fetch_prices_favorite(favorite_id, force=False):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        if not force:
            row = conn.execute("SELECT fetched_at FROM favorite_trip_prices WHERE favorite_id = ? ORDER BY fetched_at DESC LIMIT 1", (favorite_id,)).fetchone()
            if row and row[0]:
                fetched_dt = datetime.fromisoformat(str(row[0]).replace("Z", "+00:00")) if row[0] else None
                if fetched_dt:
                    age_hours = (datetime.now(fetched_dt.tzinfo) - fetched_dt).total_seconds()/3600 if fetched_dt.tzinfo else (datetime.now() - fetched_dt).total_seconds()/3600
                    if age_hours < 12:
                        conn.close(); return get_prices_for_favorite(favorite_id)
        conn.close()
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        row = conn.execute("SELECT trip_date, start_airport, destination_airport, outbound_trip_date, return_trip_date, outbound_flight_number, return_flight_number FROM favorite_trips WHERE id = ?", (favorite_id,)).fetchone()
        if not row:
            conn.close()
            return None
        trip_date, start_airport, dest_airport, out_trip_date, ret_trip_date = row[0], row[1], row[2], row[3], row[4]
        flight_no_filter = (row[5] or '').upper().replace(' ', '') if row[5] else ''
        ret_flight_no_filter = (row[6] or '').upper().replace(' ', '') if row[6] else ''
        if not start_airport or not dest_airport:
            logger.warning("Favorit %s fehlt Start-/Ziel-Flughafen", favorite_id)
            conn.close()
            return None
        conn.close()
        query_out = create_query(
            flights=[FlightQuery(date=str(out_trip_date or trip_date), from_airport=start_airport, to_airport=dest_airport, max_stops=0)],
            seat="economy", trip="one-way", passengers=Passengers(adults=1), currency="EUR", language="de")
        result_out = get_flights(query_out, integration=DirectFetch())
        price_out = None
        if result_out:
            for f in (result_out or []):
                try:
                    if not hasattr(f, 'flights') or not f.flights:
                        continue
                    if len(f.flights) != 1:
                        continue
                    price_str = f.price
                    try: price_out = float(''.join(ch for ch in str(price_str) if ch.isdigit() or ch == '.'))
                    except: pass
                    if price_out is not None:
                        break
                except Exception:
                    pass

        query_ret = create_query(
            flights=[FlightQuery(date=str(ret_trip_date or trip_date), from_airport=dest_airport, to_airport=start_airport, max_stops=0)],
            seat="economy", trip="one-way", passengers=Passengers(adults=1), currency="EUR", language="de")
        result_ret = get_flights(query_ret, integration=DirectFetch())
        price_ret = None
        if result_ret:
            for f in (result_ret or []):
                try:
                    if not hasattr(f, 'flights') or not f.flights:
                        continue
                    if len(f.flights) != 1:
                        continue
                    price_str = f.price
                    try: price_ret = float(''.join(ch for ch in str(price_str) if ch.isdigit() or ch == '.'))
                    except: pass
                    if price_ret is not None:
                        break
                except Exception:
                    pass
        total = (price_out or 0) + (price_ret or 0) if (price_out is not None or price_ret is not None) else None
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        conn.execute("INSERT OR REPLACE INTO favorite_trip_prices (favorite_id, price_outbound, price_return, price_total, currency, fetched_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)", (favorite_id, price_out, price_ret, total, "EUR"))
        conn.commit(); conn.close()
        return {"favorite_id": favorite_id, "price_outbound": price_out, "price_return": price_ret, "price_total": total, "currency": "EUR", "fetched_at": datetime.now().isoformat()}
    except Exception as e:
        logger.exception("fast-flights Fehler für Favorit %s: %s", favorite_id, e)
        return {"favorite_id": favorite_id, "error": str(e)}

def get_prices_for_favorite(favorite_id):
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    row = conn.execute("SELECT price_outbound, price_return, price_total, currency, fetched_at FROM favorite_trip_prices WHERE favorite_id = ? ORDER BY fetched_at DESC LIMIT 1", (favorite_id,)).fetchone()
    conn.close()
    if row: return {"favorite_id": favorite_id, "price_outbound": row[0], "price_return": row[1], "price_total": row[2], "currency": row[3], "fetched_at": row[4]}
    return None
