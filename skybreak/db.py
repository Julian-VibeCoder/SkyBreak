"""Shared SQLite access for the SkyBreak backend.

Every module opens the database through here so the path, default timeout and
the connection lifecycle live in one place and stay in agreement. The path is
read from the environment at call time, which keeps the test harness working:
``conftest`` sets ``DB_FILE`` to a temp path *before* any module is imported,
so a value captured at import time (and then reused) would not be honored by a
module that imports after the path is rebound.
"""
import contextlib
import os
import sqlite3

DEFAULT_DB_PATH = "/data/skybreak.db"
DEFAULT_TIMEOUT = 30.0


def db_path() -> str:
    """Current DB path from the environment (falls back to the container path)."""
    return os.environ.get("DB_FILE", DEFAULT_DB_PATH)


def connect_db(timeout: float = DEFAULT_TIMEOUT) -> sqlite3.Connection:
    """Open a new connection to the configured database."""
    return sqlite3.connect(db_path(), timeout=timeout)


@contextlib.contextmanager
def connection(timeout: float = DEFAULT_TIMEOUT):
    """Yield a shared connection and ensure it is closed when the block exits.

    Prefer this for new code so a connection can never leak on an error path::

        with connection() as conn:
            row = conn.execute("SELECT 1").fetchone()
    """
    conn = connect_db(timeout)
    try:
        yield conn
    finally:
        conn.close()


def _ensure_settings_table(conn) -> None:
    """Idempotent guard for the settings table, mirroring migration v1.

    The flights/airports schema is owned entirely by db_migrate (see
    ``apply_migrations``); this guard only guarantees the tiny key/value
    settings table exists so ``get_setting``/``set_setting`` are robust when
    called outside a migrated lifecycle.
    """
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")


def get_setting(key: str) -> str:
    conn = connect_db()
    _ensure_settings_table(conn)
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row[0] if row else ""


def set_setting(key: str, value: str) -> None:
    conn = connect_db()
    _ensure_settings_table(conn)
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()
