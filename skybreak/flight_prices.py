"""Preisabfrage über fast-flights 2.2 (v2-API)."""
import sqlite3, os, logging, json
from datetime import datetime
logger = logging.getLogger(__name__)
DB_PATH = os.environ.get("DB_FILE", "/data/skybreak.db")

from fast_flights import get_flights
from fast_flights.querying import Query, Passengers
try:
    from fast_flights import FlightQuery
except ImportError:
    FlightQuery = None
from fast_flights.pb import flights_pb2
FlightData = flights_pb2.FlightData
from fast_flights.pb.flights_pb2 import Airport

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
        # Filterwerte extrahieren (Flugnummer + Uhrzeit)
        out_fnum_filter = flight_no_filter  # z.B. DE1409
        ret_fnum_filter = ret_flight_no_filter
        # Uhrzeit-Filter basierend auf Favoriten-Daten oder Standard (z.B. 14-20 Uhr)
        earliest_dep_hour = 14 if out_fnum_filter else None
        latest_dep_hour = 20 if out_fnum_filter else None
        try:
            fd_out = FlightData(date=str(out_trip_date or trip_date), from_airport=Airport(airport=start_airport), to_airport=Airport(airport=dest_airport), max_stops=0, earliest_departure_hour=(earliest_dep_hour or 14), latest_departure_hour=(latest_dep_hour or 20))
            q_out = Query(flight_data=[fd_out], trip="one-way", passengers=[Passengers(adults=1)], seat="economy")
            result_out = get_flights(q_out)
        except Exception as e:
            logger.warning("fast-flights Hinflug Fehler: %s", e)
            result_out = None
        price_out = None
        if result_out and hasattr(result_out, 'flights'):
            flights_out = getattr(result_out, 'flights', None) or []
            for f in flights_out:
                try:
                    # Filter nach Flugnummer (falls angegeben) und Uhrzeit
                    f_flight_no = getattr(f, 'flight_no', '') or ''
                    f_departure = getattr(f, 'departure', '') or ''
                    # Wenn Favorit eine Flugnummer hat, nur diesen berücksichtigen
                    if out_fnum_filter:
                        if out_fnum_filter not in str(f_flight_no).replace(' ', ''):
                            continue
                    # Uhrzeit-Filter (z.B. 16:00-17:10 Bereich für 16:35)
                    price_str = getattr(f, 'price', None)
                    if price_str is not None:
                        try:
                            price_out_val = float(''.join(ch for ch in str(price_str) if ch.isdigit() or ch == '.'))
                        except:
                            price_out_val = None
                        if price_out_val is not None:
                            price_out = price_out_val
                            break
                except Exception:
                    pass

        try:
            earliest_ret_hour = 14 if ret_fnum_filter else None
            latest_ret_hour = 20 if ret_fnum_filter else None
            fd_ret = FlightData(date=str(ret_trip_date or trip_date), from_airport=Airport(airport=dest_airport), to_airport=Airport(airport=start_airport), max_stops=0, earliest_departure_hour=(earliest_ret_hour or 14), latest_departure_hour=(latest_ret_hour or 20))
            q_ret = Query(flight_data=[fd_ret], trip="one-way", passengers=[Passengers(adults=1)], seat="economy")
            result_ret = get_flights(q_ret)
        except Exception as e:
            logger.warning("fast-flights Rückflug Fehler: %s", e)
            result_ret = None
        price_ret = None
        if result_ret and hasattr(result_ret, 'flights'):
            flights_ret = getattr(result_ret, 'flights', None) or []
            for f in flights_ret:
                try:
                    f_flight_no = getattr(f, 'flight_no', '') or ''
                    if ret_fnum_filter:
                        if ret_fnum_filter not in str(f_flight_no).replace(' ', ''):
                            continue
                    price_str = getattr(f, 'price', None)
                    if price_str is not None:
                        try:
                            price_ret_val = float(''.join(ch for ch in str(price_str) if ch.isdigit() or ch == '.'))
                        except:
                            price_ret_val = None
                        if price_ret_val is not None:
                            price_ret = price_ret_val
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
