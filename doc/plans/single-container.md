# Plan: Single-Container Redesign

## Reihenfolge (wie Workflow: Design → Tests → Implementierung)
1. Design-Review: `doc/designs/single-container-architecture.md` (erledigt)
2. Tests zuerst: `tests/test_single_container.py` — prüfen, dass nur 1 Service in docker-compose, Port 80, SQLite-Mount existiert
3. Implementierung:
   a. `Dockerfile`: Python 3.11 + Node, React-Build, Flask-Expose 80
   b. `docker-compose.yml`: 1 service (`app`), port 80, volume `./skybreak.db:/data/skybreak.db`
   c. `skybreak/app.py`: Flask auf Port 80, `/` liefert `frontend/dist/index.html`, `/api/*` JSON
   d. `frontend/`: React-Source bleibt, Build-Output wird von Flask serviert; keine statische `index.html` im Repo als Hauptdatei (nur Source + Build im Image)
4. Tests ausführen (`python -m pytest`)
5. Commit

## Abhängigkeiten
- `frontend/package.json` existiert, `npm run build` muss funktionieren
- SQLite ist stdlib, kein pip-paket nötig

## Review-Log
- Design: OK (1 Container, Port 80, SQLite-Mount, kein statisches HTML)
- Plan: OK
