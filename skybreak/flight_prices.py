"""Preisabfrage über fast-flights 2.2 (v2-API)."""
import sqlite3, os, logging, json
from datetime import datetime
logger = logging.getLogger(__name__)
DB_PATH = os.environ.get("DB_FILE", "/data/skybreak.db")

from fast_flights import FlightData, Passengers, get_flights

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
        try:
            fd_out = FlightData(date=str(out_trip_date or trip_date), from_airport=start_airport, to_airport=dest_airport, max_stops=0)
            result_out = get_flights(flight_data=[fd_out], trip="one-way", passengers=Passengers(adults=1), seat="economy", fetch_mode="common")
        except Exception as e:
            logger.warning("fast-flights Hinflug Fehler: %s", e)
            result_out = None
        price_out = None
        if result_out and hasattr(result_out, 'flights'):
            flights_out = getattr(result_out, 'flights', None) or []
            for f in flights_out:
                try:
                    if len(flights_out) != 1:
                        continue
                    price_str = getattr(f, 'price', None)
                    if price_str is not None:
                        try: price_out = float(''.join(ch for ch in str(price_str) if ch.isdigit() or ch == '.'))
                        except: pass
                        if price_out is not None:
                            break
                except Exception:
                    pass

        try:
            fd_ret = FlightData(date=str(ret_trip_date or trip_date), from_airport=dest_airport, to_airport=start_airport, max_stops=0)
            result_ret = get_flights(flight_data=[fd_ret], trip="one-way", passengers=Passengers(adults=1), seat="economy", fetch_mode="common")
        except Exception as e:
            logger.warning("fast-flights Rückflug Fehler: %s", e)
            result_ret = None
        price_ret = None
        if result_ret and hasattr(result_ret, 'flights'):
            flights_ret = getattr(result_ret, 'flights', None) or []
            for f in flights_ret:
                try:
                    if len(flights_ret) != 1:
                        continue
                    price_str = getattr(f, 'price', None)
                    if price_str is not None:
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
