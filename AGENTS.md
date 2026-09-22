# KI / Agent Anweisungen — Workflow
1. Vor Erstellen eines Feature-Branch: git pull origin main (main immer gepufft/aktuell)
2. Erst Design-Dokument unter `doc/designs/<Feature>.md` (kein globales DESIGN.md) — feature-basiert benannt
## Pflicht-Regeln (für alle Änderungen)
1. Immer Feature-Branch erstellen (`git checkout -b ...`)
2. Erst Design-Dokument unter `doc/designs/<Feature>.md`
3. Design-Review gegen User Stories (`doc/user-stories.md`) + Architektur (`doc/architecture.md`)
4. Iteriere Design + Review bis Kompatibilität bestätigt
5. Konkreter Implementierungsplan (`doc/plans/<Feature>.md`)
6. Plan-Review gegen restliche Doku + User Stories
7. Iteriere Plan + Review bis alles passt
8. Tests ZUERST schreiben (`tests/test_...`)
9. Feature implementieren
10. Tests ausführen (`python -m pytest`)
11. PR erstellen (`create_pull_request`)
12. GitHub Actions validieren (Workflow prüfen / `gh run`)
13. PR mergen wenn ok
14. PR nur mit expliziter Zustimmung des Benutzers erstellen (keine automatischen PRs)

## Design-Review-Checkliste
- [ ] User Stories abgedeckt?
- [ ] Architektur konsistent?
- [ ] CI/Workflow kompatibel?
- [ ] Dokumentation aktualisiert?

## Implementierungsplan-Checkliste
- [ ] Reihenfolge korrekt (Tests vor Code)?
- [ ] Keine fehlenden Abhängigkeiten?
- [ ] Review-Log aktualisiert?

## Database Migration Requirement
The container must handle an empty/missing database file.
The container must migrate an existing db on its own to the latest schema.
--- Session Learnings (2026-09-22) ---
ARCHITECTURE: React/Flask/SQLite (doc/architecture.md corrected); deleted doc/designs/ doc/plans/; preserved user-stories.md
DB/CONTAINER: DB_FILE=/data/skybreak.db; init_db() handles schema at startup; Dockerfile must NOT run init_db at build (user requirement)
DOCKER SOCKET: /var/run/docker.sock available; requires sudo (user openhands not in docker group)
FRONTEND: FRONTEND_BUILD_DIR=/app/frontend/build; Dockerfile builds via npm; Flask serves static correctly
VERIFICATION: pytest partial (18/21); Docker build ok (skybreak-local); container persistence verified via /data volume mount; DB tables persist after rm/recreate
CLEANUP: Remove test containers/volumes; keep production image; never commit DB/test artifacts
DB MIGRATION: Empty/missing /data/skybreak.db => create; existing => migrate (add airport_name, etc.)
- All 23 tests passing (fixed DB_PATH in tests, init_db schema, fixture dates, assertions)
