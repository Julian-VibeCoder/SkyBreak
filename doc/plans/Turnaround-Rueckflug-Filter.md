# Plan: Filter auch für Rückflug (end) gelten lassen

## Ziel
Der `end`-Parameter (z.B. 2027-04-03) soll nicht nur den Hinflug begrenzen, sondern auch den Rückflug — d.h. ein Trip darf nicht nach `end` zurückfliegen.

## Aktuelles Verhalten
- `zeitraum_bis` = `end_str` → Hinflug bis `end`
- `zeitraum_bis_rueck_str` = `end + max_trip_days` → Rückflug bis `end + max_dauer_tage`
- Ergebnis: Trips mit Rückflug am 7./8./9. April werden gefunden, wenn `max_trip_days=7`

## Neue Logik
- Rückflüge sollen nur bis `end_str` (oder optional `end_str + 1` für Tag-Übergang) gesucht werden
- Der `max_trip_days`-Break bleibt erhalten, aber der Rückflug-Zeitraum wird auf `zeitraum_bis` (nicht `+max_d`) eingeschränkt
- Alternative: `end` als harte Obergrenze für Rückflug-Departure

## Änderungsorte
- `skybreak/app.py`: `find_short_trips()` Zeile ~494 (`zeitraum_bis_rueck_str`) und SQL-Parameter
- `tests/`: Neues Test-Case hinzufügen

## Design-Review gegen User-Stories / Architektur
- Architektur: React/Flask/SQLite; Filter-Logik ist rein backend-seitig
- Kein DB-Migration nötig (nur Query-Logik)
- Keine Live-Patch-Regel verletzt (nur Code + Image-Deploy)
