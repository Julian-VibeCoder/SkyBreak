# Story 1: Basic Airport Entry — Design

## User Story Coverage
Story 1 from doc/user-stories.md: enter international airport codes (LHR, JFK, CDG), validate IATA, store, error handling.

## Architecture Compatibility
- Backend: Python / SQLite (local DB per architecture.md)
- Docker: app + db services in docker-compose.yml
- Extension points: Stories 2-14 (flights, turnarounds, monitoring) build on airport table

## Design Decisions
- SQLite table `airports` (id, code, created_at)
- Validation: 3 uppercase alphanumeric chars (IATA standard)
- Module: `skybreak/airport.py`
- Tests: `tests/test_story1_airport.py`
