# Plan — Trip Mindestlänge + Layout-Fixes

## Reihenfolge (Tests vor Code)
1. Tests für Mindestlänge (`tests/test_...`)
2. Backend-API / Algorithmus (`skybreak/`)
3. Frontend (`frontend/src/`)
4. Dropdown-Layout-Check (`frontend/src/components/` oder CSS)
5. Wochentage-Layout (`frontend/src/components/`)
6. `pytest` ausführen

## Abhängigkeiten
- Keine neuen Pakete erforderlich (bestehender Stack)
- DB-Migration nur via `init_db()` / Quellcode, kein Live-Patch

## Layout-Regeln
- Dropdown-Option-Breite ≤ Vater-Container
- Wochentage-Container zeigt alle Tage vollständig
- Kontrast für Dropdown-Text sicherstellen (kein Grau auf Grau)
