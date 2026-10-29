import sqlite3, sys
sys.path.insert(0, '.')
from skybreak.db import db_path
from skybreak.db_migrate import apply_migrations

def test_favorite_trips_table_exists_after_migration():
    # minimal: apply migrations and check table
    apply_migrations()
    conn = sqlite3.connect(db_path())
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='favorite_trips';")
    result = cur.fetchone()
    conn.close()
    assert result is not None
