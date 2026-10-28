"""DB migration tests: v11 must reach and persist, drop the stale columns,
recreate the unique index, be idempotent, and run cleanly as a script.
"""
import os
import pathlib
import sqlite3
import subprocess
import sys

import skybreak.db_migrate as m


def _fresh_db(tmp_path):
    db = str(tmp_path / "mig.db")
    if pathlib.Path(db).exists():
        pathlib.Path(db).unlink()
    m.DB_FILE = db
    return db


def _cols(db, table="favorite_trips"):
    conn = sqlite3.connect(db)
    cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
    conn.close()
    return cols


def _version(db):
    conn = sqlite3.connect(db)
    (v,) = conn.execute("SELECT version FROM db_version").fetchone()
    conn.close()
    return v


def test_fresh_db_reaches_v11(tmp_path):
    db = _fresh_db(tmp_path)
    m.apply_migrations()
    assert _version(db) == 11


def test_v11_drops_stale_columns(tmp_path):
    db = _fresh_db(tmp_path)
    m.apply_migrations()
    cols = _cols(db)
    for c in ("start_time", "return_time", "trip_date"):
        assert c not in cols, f"{c} should have been dropped by v11"


def test_v11_recreates_unique_index(tmp_path):
    db = _fresh_db(tmp_path)
    m.apply_migrations()
    conn = sqlite3.connect(db)
    idx = {r[1] for r in conn.execute("PRAGMA index_list(favorite_trips)")}
    conn.close()
    assert "idx_favorite_unique" in idx


def test_migration_is_idempotent(tmp_path):
    db = _fresh_db(tmp_path)
    m.apply_migrations()
    m.apply_migrations()  # must not raise on a second run
    assert _version(db) == 11


def test_migrate_runs_as_script(tmp_path):
    db = _fresh_db(tmp_path)
    env = dict(os.environ)
    env["DB_FILE"] = db
    res = subprocess.run(
        [sys.executable, "-m", "skybreak.db_migrate"],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(pathlib.Path.cwd()),
    )
    assert res.returncode == 0, f"stderr: {res.stderr}"
    assert _version(db) == 11
