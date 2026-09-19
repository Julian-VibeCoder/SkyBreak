# Agent / KI Workflow — Design-Dokument

## Ziel
Alle Änderungen folgen einem strikten Feature-Branch-Workflow mit Design-First-Ansatz.

## Anforderungen (aus User Story / Architektur)
- Feature-Branch für jede Änderung
- Design-Dokument vor Code
- Design-Review gegen User Stories (`doc/user-stories.md`) und Architektur (`doc/architecture.md`)
- Iteration bis Kompatibilität bestätigt
- Implementierungsplan mit Review
- Tests vor Implementierung (TDD)
- GitHub Actions validieren
- PR erstellen und mergen

## Kompatibilitätsprüfung (nach Review)
- User Stories: Filter, Price-Anzeige, Date-Filter abgedeckt
- Architektur: CI, Workflow, Dokumentation konsistent
- Status: KOMPATIBEL (nach Iteration)

## Implementierungsplan
1. Feature-Branch erstellen (`agent-workflow-instructions`)
2. Design-Dokument (`AGENTS.md`) erstellen
3. Design-Review durchführen
4. Implementierungsplan schreiben (`PLAN.md`)
5. Plan-Review durchführen
6. Tests schreiben (`tests/test_workflow.py`)
7. Feature implementieren (`.agents/skills/` + `AGENTS.md`)
8. Tests ausführen
9. PR erstellen
10. GitHub Actions prüfen
11. PR mergen

## Design-Review-Log
- Iteration 1: Design erstellt — Kompatibilität geprüft — OK
- Keine Abweichungen von User Stories / Architektur gefunden.
