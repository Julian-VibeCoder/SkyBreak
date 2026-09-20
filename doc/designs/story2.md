# Story 2 — Load Departures and Arrivals (Public Flight API)

> **Spec für:** `doc/plans/story2.md`
**Ziel:** Flüge von erstellten Flughäfen über öffentliche API laden (1 Jahr Zukunft), DB-Schema anlegen, Rate-Limit mit Retry-Job.

## Architektur
- Öffentliche Flight-API (OpenFlights-Datensatz / AviationStack-Mock) ohne Key
- DB-Tabelle `flights` (`airport_code`, `scheduled_departure`, `scheduled_arrival`, `year_ahead`)
- `APScheduler`-Background-Job (`skybreak/scraper_job.py`) mit `tenacity`-Retry bei 429/503
- API-Endpoint `/api/flights` liefert Daten für alle gespeicherten Airports

## Tech Stack
- Python 3.13, Flask (bestehend), SQLite (`test.db` / `init_db.py`), APScheduler, tenacity, requests

## Global Constraints
- Keine externen Keys nötig (öffentliche Daten)
- Flüge nur 1 Jahr in Zukunft (`+365d` Filter)
- Rate-Limit-Retry alle 30 Min, max 5 Versuche
- Tests zuerst (`tests/test_story2_...`)
