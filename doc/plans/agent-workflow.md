# Implementierungsplan — Agent Workflow

## Phase 1: Design (erledigt — DESIGN.md)
- Design-Dokument erstellt
- Review gegen User Stories + Architektur: BESTANDEN

## Phase 2: Implementierungsplan (dieses Dokument)
- Plan gegen Dokumentation geprüft
- Keine Abweichungen gefunden

## Phase 3: Tests (TDD — zuerst!)
- `tests/test_agent_workflow.py` erstellen
- Prüfen: Feature-Branch, Design-Doc, Review-Schritte, TDD, PR, Actions, Merge

## Phase 4: Implementierung
- `.agents/skills/` / AGENTS.md aktualisieren
- Workflow-Anweisungen schreiben

## Phase 5: Tests ausführen
- `python -m pytest tests/`
- Alle Tests müssen grün sein

## Phase 6: PR
- Feature-Branch `agent-workflow-instructions`
- PR gegen `main`

## Phase 7: GitHub Actions validieren
- Workflow `vacation.yml` / `ci.yml` prüfen

## Phase 8: Merge
- PR mergen wenn Actions OK

## Review-Log (Plan)
- Iteration 1: Plan erstellt — OK
