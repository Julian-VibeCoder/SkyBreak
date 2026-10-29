# Project Memory - SkyBreak (vacation)
- Stack: React frontend, Flask backend, SQLite DB at /data/skybreak.db
- Docker: socket at /var/run/docker.sock (sudo needed); image skybreak-local
- Design docs: doc/designs/ and doc/plans/ deleted per user; architecture.md updated
- DB init: container handles (not Dockerfile); init_db creates schema + migrates
- Cleanup protocol: rm -rf test containers/volumes; keep production image

# DB Access Layer (2026-10-29)
- skybreak/db.py is the single DB entry point: db_path() (call-time DB_FILE read), connect_db(timeout=30.0), connection() ctx-mgr, get_setting/set_setting.
- All source modules (app, airport, scraper_job, flight_prices, get_flight_price, db_migrate) open via db.py — NO raw sqlite3.connect / module-level DB_FILE constant outside db.py.
- db_migrate.apply_migrations(path=None): path defaults to db_path(); pass explicit path to migrate a specific file without env mutation (used by migration tests).
- get_setting/set_setting live in db.py (the settings table's home), not airport.py.
- Schema fully owned by db_migrate migration_v1..v12 (version-tracked in db_version table); no runtime DDL in data path.
- Tests set DB_FILE via conftest BEFORE import (call-time read is required; import-time capture breaks the harness).
- Dead-import sweep: AST check of skybreak/*.py + tests/*.py should report 0 unused imports.

# Frontend Structure (2026-10-29, Task 4)
- App.js is now a thin shell (~141 lines, was ~625): routing + responsive sidebar + shared airport list + scrape-status poll.
- Per-tab components (frontend/src/components/): AirportsTab, FlightsTab (owns flightData), TripsTab, SettingsTab, FavoriteTripPrices (owns ChartModal).
- Hooks (frontend/src/hooks/): useActiveTab(NAV) = tab routing, useAirports() = shared list + airportNames.
- utils/format.js: formatTime + formatTripDateTime (deduped the repeated IIFEs).
- Dead code removed: FavoriteTrips() def, checkScrape helper, `import Layout` (Layout was imported but NEVER used — pre-existing dead import).
- ORPHAN: frontend/src/components/Layout.jsx is now fully unused (zero imports). Left in place awaiting user call to delete.
- Build gate: `npm run build` in frontend/ (node_modules present; frontend/build is gitignored, served by Flask /app/frontend/build).
- tests/test_app_integration.py enforces the new wiring (asserts tab imports in App.js, ChartModal in FavoriteTripPrices, NO `import Layout`).
- Frontend has NO test framework (no jest/RTL) — verification is `npm run build` + browser smoke test only.
# WICHTIG — NIE LIVE PATCHEN
- DB-/Container-Patche sind VERBOTEN.
- Jede Migration, jede Settings-Änderung, jede Schema-Fix muss im Quellcode (init_db.py, scraper_job.py, app.py) stehen und durch Image-Deploy + Container-Neustart wirken.
- Wenn fetch_max_months / DB-Setting fehlt: im Code ergänzen, nicht via sqlite3 im laufenden Container.
- Wenn API 404 / DB leer: Code prüfen (route, query, Migration), nicht Container-Daten händisch editieren.
- Nach jedem Code-Change: docker build + docker rm + docker run (neues Image, neuer Container).
- Agents.md / MEMORY.md muss diese Regel enthalten, damit nicht wiederholt wird.

- NIE LIVE PATCHEN (DB/Container-Edits verboten).
- Migrationen/Schema-Fixes NUR im Code (init_db.py/scraper_job.py/app.py), dann docker build + redeploy.
- fetch_max_months = 1 muss als DB-Setting (init_db/settings) + Env-Var gesetzt sein.
- API 404 (scrape-status): Route in app.py ergänzen, nicht Container editieren.
- Insert-Konflikte: INSERT statt INSERT OR IGNORE, wenn DB leer / keine Konflikte erwartet.

# GitHub Auth Token
GITHUB_PERSONAL_ACCESS_TOKEN set for GitHub API access (gh / curl).
Use GH_TOKEN=\$GITHUB_TOKEN for gh CLI operations.
Token masked in output; never commit raw value.

# Container Config (2026-09-25)
- Port: 8088 (mapped to container 80)
- Mount: /opt/skybreak (DB_FILE=/opt/skybreak/skybreak.db)
- Container name: flightbreak
- Image: skybreak-local
