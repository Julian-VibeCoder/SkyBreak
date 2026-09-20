# Story 2 — Load Departures and Arrivals (Public Flight API)

> **Für agentic workers:** Implementiere task-by-task, TDD (Tests zuerst), commit nach jeder Task.
**Ziel:** Öffentliche API laden, DB-Schema `flights`, Rate-Limit-Job, 1 Jahr Zukunft.
**Architektur:** Flask-Endpoint `/api/flights` → Scraper (`requests` + `tenacity`) + `APScheduler`-Job (`skybreak/scraper_job.py`) → SQLite `flights`.
**Tech Stack:** Python 3.13, Flask (bestehend), SQLite, APScheduler, tenacity, requests
**Spec:** `doc/designs/story2.md`

## Global Constraints
- Keine externen API-Keys (öffentliche Daten / Mock)
- Flüge nur `scheduled_departure >= today + 365d`
- Rate-Limit: max 5 Retries, Backoff 30 Min (`tenacity`)
- Tests zuerst (`tests/test_story2_...`)
- Feature-Branch: `feature/story2-flight-api`

## Review Focus
- API 429/503 → Retry-Logik funktioniert?
- Datum-Filter (+365d) korrekt angewendet?
- DB-Schema konsistent (`airport_code`, `scheduled_departure`, `scheduled_arrival`)?
- Job läuft periodisch ohne Crash bei fehlender DB?
- Keine Orphaned-Flights bei gelöschtem Airport?

---

### Task 1: DB-Schema `flights`
**Files:** Create `init_db.py` (modify), `tests/test_story2_schema.py`
**Interfaces:** DB-Tabelle `flights`
- [ ] Step 1: Failing test `tests/test_story2_schema.py` (prüft `CREATE TABLE flights` existiert)
- [ ] Step 2: Run `pytest` → FAIL
- [ ] Step 3: Modify `init_db.py`: `CREATE TABLE IF NOT EXISTS flights (...)`
- [ ] Step 4: `pytest` → PASS
- [ ] Step 5: `git add ...; git commit -m "feat(story2): DB schema flights"`

### Task 2: Scraper mit öffentlicher API + Retry
**Files:** Create `skybreak/flight_scraper.py`, `tests/test_story2_scraper.py`
**Interfaces:** `fetch_flights(airport_code) -> list[dict]`, `load_flights_for_airport(...)`
- [ ] Step 1: Failing test (`mock requests.get` mit 429, dann 200; prüft Retry + Daten)
- [ ] Step 2: `pytest` → FAIL
- [ ] Step 3: Implementiere `skybreak/flight_scraper.py` mit `requests`, `tenacity.retry` (wait=30min, stop=5), Filter `scheduled_departure >= today+365`
- [ ] Step 4: `pytest` → PASS
- [ ] Step 5: Commit

### Task 3: Background-Job APScheduler
**Files:** Create `skybreak/scraper_job.py`, `tests/test_story2_job.py`
**Interfaces:** `start_scheduler()`, `scrape_all_airports()`
- [ ] Step 1: Test (`scheduler.add_job(...)` läuft, ruft `fetch_flights` auf)
- [ ] Step 2: FAIL
- [ ] Step 3: `APScheduler` (`BackgroundScheduler`) in `scrape_all_airports()`; alle Codes aus `airports`-DB lesen
- [ ] Step 4: PASS
- [ ] Step 5: Commit

### Task 4: API-Endpoint `/api/flights`
**Files:** Modify `skybreak/app.py`, `tests/test_story2_api.py`
**Interfaces:** `GET /api/flights` (optional `?airport=XYZ`)
- [ ] Step 1: Failing test (`client.get('/api/flights')` → 200 + JSON)
- [ ] Step 2: FAIL
- [ ] Step 3: Endpoint in `app.py` hinzufügen; liest `flights`-DB; Filter +365d
- [ ] Step 4: PASS
- [ ] Step 5: Commit
