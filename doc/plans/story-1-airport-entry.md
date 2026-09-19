# Story 1 Implementation Plan

## Sequence (Tests before code)
1. Design doc (done) — review completed
2. Plan doc (this)
3. Write tests: `tests/test_story1_airport.py`
4. Implement `skybreak/airport.py` + SQLite init
5. Bootstrap: `docker-compose.yml`, Dockerfile, DB init script
6. Run `python -m pytest`
7. Commit

## Dependencies
- Python 3, sqlite3 (stdlib)
- pytest for tests
- Docker for hosting

No missing dependencies.
