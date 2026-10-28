"""Settings must survive DB migration: in particular the price scheduler reads
``price_fetch_interval_hours``, which the old whitelist deleted on every restart.
"""
import pathlib
import sqlite3

import skybreak.db_migrate as m

WHITELIST = {
    "scrape_delay_ms",
    "fetch_max_months",
    "fetch_max_days",
    "favorite_max_items",
    "google_consent_cookie",
    "price_fetch_interval_hours",
}


def _fresh_db(tmp_path):
    db = str(tmp_path / "settings.db")
    if pathlib.Path(db).exists():
        pathlib.Path(db).unlink()
    m.DB_FILE = db
    m.apply_migrations()  # create schema + seed
    return db


def _keys(db):
    conn = sqlite3.connect(db)
    keys = {r[0] for r in conn.execute("SELECT key FROM settings")}
    conn.close()
    return keys


def test_price_interval_survives_migration(tmp_path):
    db = _fresh_db(tmp_path)
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)",
                 ("price_fetch_interval_hours", "12"))
    conn.commit()
    conn.close()

    m.apply_migrations()

    assert "price_fetch_interval_hours" in _keys(db)


def test_non_whitelisted_settings_are_removed(tmp_path):
    db = _fresh_db(tmp_path)
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)",
                 ("legacy_junk_key", "whatever"))
    conn.commit()
    conn.close()

    m.apply_migrations()

    assert "legacy_junk_key" not in _keys(db)


def test_google_consent_cookie_is_seeded(tmp_path):
    db = _fresh_db(tmp_path)
    assert "google_consent_cookie" in _keys(db)
