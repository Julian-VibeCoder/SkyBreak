# KI / Agent Anweisungen — Workflow
2. Erst Design-Dokument unter `doc/designs/<Feature>.md` (kein globales DESIGN.md) — feature-basiert benannt
## Pflicht-Regeln (für alle Änderungen)
1. Immer Feature-Branch erstellen (`git checkout -b ...`)
2. Erst Design-Dokument (`DESIGN.md` / `AGENTS.md`)
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

## Design-Review-Checkliste
- [ ] User Stories abgedeckt?
- [ ] Architektur konsistent?
- [ ] CI/Workflow kompatibel?
- [ ] Dokumentation aktualisiert?

## Implementierungsplan-Checkliste
- [ ] Reihenfolge korrekt (Tests vor Code)?
- [ ] Keine fehlenden Abhängigkeiten?
- [ ] Review-Log aktualisiert?
