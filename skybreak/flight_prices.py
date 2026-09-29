"""Preisdaten pro Favorit aus DB lesen; Einzelpreis über get_flight_price abfragen."""
import sqlite3, os, logging
from datetime import datetime
from skybreak.get_flight_price import get_flight_price

logger = logging.getLogger(__name__)
DB_PATH = os.environ.get("DB_FILE", "/data/skybreak.db")

def fetch_prices_favorite(favorite_id, force=False):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        row = conn.execute("SELECT id, start_airport, destination_airport, outbound_trip_date, return_trip_date, outbound_flight_number, return_flight_number FROM favorite_trips WHERE id = ?", (favorite_id,)).fetchone()
        conn.close()
        if not row:
            return {"favorite_id": favorite_id, "error": "Favorit nicht gefunden"}
        fav_id, start_airport, dest_airport, out_trip_date, ret_trip_date, out_fnum, ret_fnum = row
        if not start_airport or not dest_airport:
            return {"favorite_id": favorite_id, "error": "Flughafen fehlt"}
        out_date = out_trip_date or ""
        ret_date = ret_trip_date or ""
        price_out = None
        price_ret = None
        if out_date and out_fnum:
            try:
                price_out = get_flight_price(str(start_airport), str(dest_airport), out_date, str(out_fnum))
            except Exception as e:
                logger.warning("Hinflug Fehler: %s", e)
        if ret_date and ret_fnum:
            try:
                price_ret = get_flight_price(str(dest_airport), str(start_airport), ret_date, str(ret_fnum))
            except Exception as e:
                logger.warning("Rückflug Fehler: %s", e)
        out_available = bool(out_date and out_fnum)
        ret_available = bool(ret_date and ret_fnum)
        out_has_price = price_out is not None
        ret_has_price = price_ret is not None
        # Wenn ein Flug eines Trips keinen Preis hat -> Gesamtpreis = none
        if (out_available and not out_has_price) or (ret_available and not ret_has_price):
            total = None
        else:
            total = (price_out or 0) + (price_ret or 0) if (price_out is not None or price_ret is not None) else None
        if price_out is not None or price_ret is not None:
            conn = sqlite3.connect(DB_PATH, timeout=30.0)
            conn.execute("INSERT OR REPLACE INTO favorite_trip_prices (favorite_id, price_outbound, price_return, price_total, currency, fetched_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)", (favorite_id, price_out, price_ret, total, "EUR"))
            conn.commit()
            conn.close()
        return {"favorite_id": favorite_id, "price_outbound": price_out, "price_return": price_ret, "price_total": total, "currency": "EUR", "fetched_at": datetime.now().isoformat()}
    except Exception as e:
        logger.exception("Fehler %s: %s", favorite_id, e)
        return {"favorite_id": favorite_id, "error": str(e)}

def get_prices_for_favorite(favorite_id):
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    row = conn.execute("SELECT price_outbound, price_return, price_total, currency, fetched_at FROM favorite_trip_prices WHERE favorite_id = ? ORDER BY fetched_at DESC LIMIT 1", (favorite_id,)).fetchone()
    conn.close()
    if row:
        return {"favorite_id": favorite_id, "price_outbound": row[0], "price_return": row[1], "price_total": row[2], "currency": row[3], "fetched_at": row[4]}
    return None
