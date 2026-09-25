# Design — Trip Mindestlänge + Layout-Fixes

## Anforderungen
1. Mindestlänge in Tagen für Trip-Berechnung (Frontend-API + Algorithmus)
2. Trip-Seite: Dropdown Start-/End-Flughafen Text lesbar (evtl. Grau auf Grau)
3. Wochentage-Auswahl: alle Tage sichtbar
4. Layout: keine Option breiter als Vater-Container

## Bezug zu User Stories / Architektur
- Story 3 (Turn-arounds) / Story 4 (Days Off)
- Architektur: React-Frontend, Flask-Backend, SQLite
- Keine Live-Patches (DB/Container nur via Code + Build + Redeploy)

## Plan-Links
- doc/plans/Trip-Mindestlaenge-Layout.md
