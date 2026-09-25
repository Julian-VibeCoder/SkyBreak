# Design: Trip-Berechnung DB-Optimierung (/opt/skybreak)

## Ziel
Trip-Berechnung (`/api/turnarounds`) beschleunigen und CPU-Last senken bei DB `/opt/skybreak/skybreak.db` (196.492 Zeilen, 4 Airports).

## Analyse
- `turnarounds` lädt ALLE Flüge (`WHERE departure_time >= datetime('now','utc')` + 365 Tage) → 196k Zeilen in Python
- Filter (`airport_icao`, `from_icao`, `to_icao`) erfolgt in-memory (Python-Loop)
- Bestehende Indexe: `idx_flights_airport (airport_icao, departure_time)`, `idx_flights_airport_month`
- Keine DB-Filterung auf `from_icao`/`to_icao` → Full-Table-Scan + Python-Verarbeitung

## Lösung (nach NIE LIVE PATCHEN Regel)
1. Indexe in `init_db.py`: `(from_icao)`, `(to_icao)`, `(flight_date, departure_time, airport_icao)`
2. `app.py` (`turnarounds`): Query auf DB-Filter (`airport_icao = ?`, `departure_time` Range) + `from_icao` Filter umstellen
3. Migration nur via Code (`CREATE INDEX IF NOT EXISTS`), dann Container-Rebuild

## Kompatibilität
- Bestehende Endpunkte (`/api/flights`, `/api/turnarounds`, `/api/airports`) bleiben unverändert
- `init_db()` läuft beim Container-Start und erstellt/migriert DB automatisch
- Keine Live-Edits an `/opt/skybreak/skybreak.db`
