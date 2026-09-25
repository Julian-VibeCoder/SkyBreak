"""Streamlined DB migration: version saved in db, steps per schema change, applied at startup."""
import sqlite3, os, logging
logger = logging.getLogger(__name__)
DB_FILE = os.environ.get("DB_FILE", "/opt/skybreak/skybreak.db")

def get_current_version(conn):
    try:
        row = conn.execute("SELECT version FROM db_version LIMIT 1").fetchone()
        return row[0] if row else 0
    except sqlite3.OperationalError:
        return 0

def migration_v1(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS airports (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    # Check if flights exists with full schema; if missing columns, rebuild
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(flights)").fetchall()}
    except:
        cols = set()
    full_flights_cols = {"id","airport_icao","airport_name","destination_icao","destination_name","flight_direction","departure_time","arrival_time","duration_minutes","flight_number","from_icao","to_icao","created_at"}
    if cols and not full_flights_cols.issubset(cols):
        # Partial schema: rebuild
        conn.execute("ALTER TABLE flights RENAME TO flights_old")
        conn.execute("CREATE TABLE flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_icao TEXT, airport_name TEXT, destination_icao TEXT, destination_name TEXT, flight_direction TEXT, departure_time TEXT, arrival_time TEXT, duration_minutes INTEGER, flight_number TEXT, from_icao TEXT, to_icao TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        try:
            conn.execute("INSERT INTO flights (airport_icao, airport_name, destination_icao, destination_name, flight_direction, departure_time, arrival_time, duration_minutes, flight_number, from_icao, to_icao, created_at) SELECT airport_icao, airport_name, destination_icao, destination_name, flight_direction, departure_time, arrival_time, duration_minutes, flight_number, from_icao, to_icao, CURRENT_TIMESTAMP FROM flights_old")
        except Exception:
            pass
        conn.execute("DROP TABLE flights_old")
    else:
        conn.execute("CREATE TABLE IF NOT EXISTS flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_icao TEXT, airport_name TEXT, destination_icao TEXT, destination_name TEXT, flight_direction TEXT, departure_time TEXT, arrival_time TEXT, duration_minutes INTEGER, flight_number TEXT, from_icao TEXT, to_icao TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        # If table exists but missing created_at specifically
        if 'created_at' not in cols:
            conn.execute("ALTER TABLE flights RENAME TO flights_old")
            conn.execute("CREATE TABLE flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_icao TEXT, airport_name TEXT, destination_icao TEXT, destination_name TEXT, flight_direction TEXT, departure_time TEXT, arrival_time TEXT, duration_minutes INTEGER, flight_number TEXT, from_icao TEXT, to_icao TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            try:
                common = [r[1] for r in conn.execute("PRAGMA table_info(flights_old)").fetchall() if r[1] != 'id']
                common_str = ", ".join(common) if common else "airport_icao"
                conn.execute(f"INSERT INTO flights ({common_str}, created_at) SELECT {common_str}, CURRENT_TIMESTAMP FROM flights_old")
            except Exception:
                pass
            conn.execute("DROP TABLE flights_old")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_flights_airport ON flights (airport_icao, departure_time)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fluege_matching ON flights(airport_icao, to_icao, departure_time)")
    conn.execute("CREATE TABLE IF NOT EXISTS db_version (version INTEGER PRIMARY KEY)")
    conn.execute("DELETE FROM db_version")
    conn.execute("INSERT INTO db_version (version) VALUES (1)")
    logger.info("Applied migration v1")


def apply_migrations():
    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    current = get_current_version(conn)
    if current < 1:
        migration_v1(conn)
    conn.execute("DELETE FROM settings WHERE key NOT IN (?, ?, ?)", ("scrape_delay_ms", "fetch_max_months", "fetch_max_days"))
    conn.commit()
    conn.close()
    logger.info("DB at version %d", get_current_version(sqlite3.connect(DB_FILE, timeout=30.0)))

if __name__ == "__main__":
    apply_migrations()
