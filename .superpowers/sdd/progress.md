# SDD Ledger — plan: doc/plans/story2.md
Feature-Branch: feature/story2-flight-api

## Pre-flight rulings
- Ruling: Schema muss destination_icao + flight_direction enthalten (Hin-/Rückflug-Mapping).
- Ruling: Öffentliche API (kein Key) + tenacity Retry (nicht Job-Loop).
- Ruling: Filter +365d — bestätigt in Commit 457f739.

## Tasks
Task 1 (Schema): Subagent startete, kein Report — manuell: init_db.py hat flights mit destination_icao, flight_direction. Teilweise.
Task 2 (Scraper): Subagent gestartet, kein Commit — nicht abgeschlossen.
Task 3 (Job): Subagent gestartet, kein Commit — nicht abgeschlossen.
Task 4 (API): Subagent bereit — Commit 457f739 (tests/test_story2_api.py, skybreak/app.py, init_db.py) — abgeschlossen, gemerged.

## Final verification (manuell)
- Schema korrekt: destination_icao + flight_direction ✅
- Filter +365d ✅
- Subagent-Reports T1-T3 fehlen → nicht abgeschlossen.
Task 2 (Scraper): manuell nachgezogen (skybreak/flight_scraper.py, tenacity)
Task 3 (Job): manuell nachgezogen (skybreak/scraper_job.py, APScheduler)
