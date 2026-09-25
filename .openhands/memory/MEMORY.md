# Project Memory - SkyBreak (vacation)
- Stack: React frontend, Flask backend, SQLite DB at /data/skybreak.db
- Docker: socket at /var/run/docker.sock (sudo needed); image skybreak-local
- Design docs: doc/designs/ and doc/plans/ deleted per user; architecture.md updated
- DB init: container handles (not Dockerfile); init_db creates schema + migrates
- Cleanup protocol: rm -rf test containers/volumes; keep production image
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
