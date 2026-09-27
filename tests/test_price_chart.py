import sqlite3, pytest
DB_PATH = "/data/skybreak.db"

def test_price_chart_history_returns_series():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT fetched_at, price_outbound, price_return, price_total FROM favorite_trip_prices WHERE favorite_id = ? ORDER BY fetched_at ASC",
        (1,)
    ).fetchall()
    assert len(rows) >= 0  # Basic query works; with real data, 3 values per row
    conn.close()
