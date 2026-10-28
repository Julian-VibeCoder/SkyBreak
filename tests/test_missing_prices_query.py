"""The /api/prices/missing path joins favorite_trips against favorite_trip_prices.
A previous version referenced a non-existent `ftp.id` column, raising in the
background thread. This guards that the query is valid SQL.
"""
import sqlite3

import skybreak.db_migrate as m

QUERY = (
    "SELECT DISTINCT ft.id FROM favorite_trips ft "
    "LEFT JOIN favorite_trip_prices ftp ON ft.id = ftp.favorite_id "
    "WHERE ftp.favorite_id IS NULL OR ftp.price_outbound IS NULL OR ftp.price_return IS NULL"
)


def test_missing_prices_query_is_valid(tmp_path):
    db = str(tmp_path / "mp.db")
    m.DB_FILE = db
    m.apply_migrations()
    conn = sqlite3.connect(db)
    # Must run without error (favorite_trip_prices has no `id` column).
    assert conn.execute(QUERY).fetchall() == []
    conn.close()
