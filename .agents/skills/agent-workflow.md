# KI / Agent Anweisungen — Workflow

## Pflicht-Regeln (für alle Änderungen)
- Feature-Branch + PR sind nicht immer notwendig (z.B. Hotfixes, Dependency-Updates, direkte Main-Fixes nach expliziter Zustimmung).
- Für größere Features gelten weiterhin: Design-Dokument, Review, Tests zuerst, dann Implementierung und PR.
1. Feature-Branch erstellen, wenn angemessen (`git checkout -b ...`) — nicht für jeden Hotfix erforderlich
2. Erst Design-Dokument (`DESIGN.md` / `AGENTS.md`) — bei Features und signifikanten Änderungen
3. Design-Review gegen User Stories (`doc/user-stories.md`) + Architektur (`doc/architecture.md`)
4. Iteriere Design + Review bis Kompatibilität bestätigt
5. Konkreter Implementierungsplan (`PLAN.md`)
6. Plan-Review gegen restliche Doku + User Stories
7. Iteriere Plan + Review bis alles passt
8. Tests ZUERST schreiben (`tests/test_...`)
9. Feature implementieren
10. Tests ausführen (`python -m pytest`)
11. PR erstellen (`create_pull_request`) — nur wenn erforderlich (Feature/Release); direkte Push nur bei expliziter Zustimmung
12. GitHub Actions validieren (Workflow prüfen / `gh run`) — bei PRs oder nach direktem Push
13. PR mergen wenn ok / bei direktem Push auf Main: sofortige Validierung

## Design-Review-Checkliste
- [ ] User Stories abgedeckt?
- [ ] Architektur konsistent?
- [ ] CI/Workflow kompatibel?
- [ ] Dokumentation aktualisiert?

## Implementierungsplan-Checkliste
- [ ] Reihenfolge korrekt (Tests vor Code)?
- [ ] Keine fehlenden Abhängigkeiten?
- [ ] Review-Log aktualisiert?
