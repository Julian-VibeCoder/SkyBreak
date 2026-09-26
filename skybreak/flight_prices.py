"""Fast-flights Preisabfrage für Favoriten (Hinflug + Rückflug + Summe)."""
import sqlite3, os, logging
from datetime import datetime
logger = logging.getLogger(__name__)
DB_PATH = os.environ.get("DB_FILE", "/data/skybreak.db")

def fetch_prices_favorite(favorite_id):
    """Preise für einen Favoriten via fast-flights abrufen und speichern."""
    try:
        import fast_flights
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        row = conn.execute(
            "SELECT trip_date, start_airport, destination_airport FROM favorite_trips WHERE id = ?",
            (favorite_id,)).fetchone()
        conn.close()
        if not row:
            return None
        trip_date, start_airport, dest_airport = row
        if not start_airport or not dest_airport:
            logger.warning("Favorit %s fehlt Start-/Ziel-Flughafen", favorite_id)
            return None
        # Hinflug
        result_out = fast_flights.get_flights(
            flight_data=[fast_flights.FlightData(date=str(trip_date), from_airport=start_airport, to_airport=dest_airport)],
            trip="one-way", seat="economy", passengers=fast_flights.Passengers(adults=1), fetch_mode="local"
        )
        price_out = None
        if result_out and hasattr(result_out, "flights") and result_out.flights:
            price_str = result_out.flights[0].price
            def parse_price(p):
                if p is None: return None
                try: return float(''.join(ch for ch in str(p) if ch.isdigit() or ch == '.'))
                except: return None
            price_out = parse_price(price_str)
        # Rückflug
        result_ret = fast_flights.get_flights(
            flight_data=[fast_flights.FlightData(date=str(trip_date), from_airport=dest_airport, to_airport=start_airport)],
            trip="one-way", seat="economy", passengers=fast_flights.Passengers(adults=1), fetch_mode="local"
        )
        price_ret = None
        if result_ret and hasattr(result_ret, "flights") and result_ret.flights:
            price_ret_str = result_ret.flights[0].price
            def parse_price_ret(p):
                if p is None: return None
                try: return float(''.join(ch for ch in str(p) if ch.isdigit() or ch == '.'))
                except: return None
            price_ret = parse_price_ret(price_ret_str)
        total = (price_out or 0) + (price_ret or 0) if (price_out is not None or price_ret is not None) else None
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        conn.execute("""INSERT OR REPLACE INTO favorite_trip_prices (favorite_id, price_outbound, price_return, price_total, currency, fetched_at)
                      VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                      (favorite_id, price_out, price_ret, total, "EUR"))
        conn.commit()
        conn.close()
        return {"favorite_id": favorite_id, "price_outbound": price_out, "price_return": price_ret, "price_total": total, "currency": "EUR", "fetched_at": datetime.now().isoformat()}
    except Exception as e:
        logger.exception("fast-flights Fehler für Favorit %s: %s", favorite_id, e)
        return {"favorite_id": favorite_id, "error": str(e)}

def get_prices_for_favorite(favorite_id):
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    row = conn.execute("SELECT price_outbound, price_return, price_total, currency, fetched_at FROM favorite_trip_prices WHERE favorite_id = ? ORDER BY fetched_at DESC LIMIT 1", (favorite_id,)).fetchone()
    conn.close()
    if row:
        return {"favorite_id": favorite_id, "price_outbound": row[0], "price_return": row[1], "price_total": row[2], "currency": row[3], "fetched_at": row[4]}
    return None
