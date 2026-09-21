# Fix airport persistence

Issues:
- `skybreak/airport.py` uses relative `DB_PATH = "skybreak.db"` instead of `/data/skybreak.db`
- `add_airport()` ignores real airport name; uses `INSERT OR IGNORE` with `name=code`
- `init_db()` missing `settings` table creation
- `delete_airport()` OK
- `app.py` has duplicate `if __name__ == "__main__"` block

Plan: align DB paths, fix name insertion, remove duplicate block.
