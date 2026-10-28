# Plan: Build / CI / Docker Pipeline Fixes

Order: tests first, then implementation. Each item maps to a finding in the design
doc. Validate with the Python 3.12 venv (fast-flights 3.1 needs ≥3.10); final check
runs the full portable suite and a Docker build if a daemon is available.

## Phase 0 — Test portability harness (must exist before other tests)
- [ ] NEW `tests/conftest.py`:
  - at import time set `DB_FILE` to a writable temp path (unless already set) and
    `FRONTEND_BUILD_DIR` to the repo `frontend/build` (create a placeholder
    `index.html` if missing);
  - session autouse fixture runs `apply_migrations()` so the schema exists for any
    test that opens the DB;
  - a function-scoped helper to reset the flights/favorites tables when needed.

## Phase 1 — Tests for the changes (RED first, then GREEN)
- [ ] NEW `tests/test_db_migration.py`:
  - fresh DB → `apply_migrations()` → version == 11;
  - `start_time/return_time/trip_date` absent from `favorite_trips`;
  - unique index recreation does not raise; idempotent (run twice, still 11);
  - subprocess `python -m skybreak.db_migrate` exits 0 and yields version 11
    (validates the `__main__` guard fix).
- [ ] NEW `tests/test_settings_persistence.py`:
  - set a non-whitelisted key + `price_fetch_interval_hours`; after
    `apply_migrations()` the interval survives, the junk is gone,
    `google_consent_cookie` is seeded.
- [ ] NEW `tests/test_ci_config.py` (parse YAML/text, no Docker/runner needed):
  - `ci.yml`: no `|| true` anywhere; runs `pytest` on `tests/`; installs deps +
    builds frontend;
  - `docker-publish.yml`: no `pull_request` trigger; `cache-to` is a `registry`
    type (persists); no dead `CACHEBUST` build-arg;
  - `ghcr-cleanup.yml`: decides per version (any protected tag → keep); fixed
    non-empty login username; checks delete HTTP status.

## Phase 2 — Fix `db_migrate.py` (GREEN for the migration tests)
- [ ] Single clean `apply_migrations()` + a single `__main__` guard at the end.
- [ ] `migration_v11`: drop `idx_favorite_unique`, drop the 3 columns, recreate the
  unique index on the surviving columns (robust to missing columns); guard the whole
  body so a partial state never leaves a half-dropped table.
- [ ] Add `price_fetch_interval_hours` to the settings whitelist.
- [ ] `python -m skybreak.db_migrate` no longer raises `NameError`.

## Phase 3 — Fix price-scraping runtime dependency
- [ ] `requirements.txt`: pin `fast-flights==3.1.0`; add explicit runtime deps
  `primp`, `protobuf>=5.27.0`, `selectolax`, `typing_extensions`; remove duplicate
  `requests`; drop `pytest` (move to dev).
- [ ] NEW `requirements-dev.txt` = `-r requirements.txt` + `pytest`.
- [ ] Delete unused `requirements_clean.txt`.
- [ ] Confirm `from fast_flights import FlightQuery, Passengers, create_query` works.

## Phase 4 — Slim the Dockerfile
- [ ] Final stage: keep only `libsqlite3-0` (drop the 20+ GTK/browser libs).
- [ ] `npm install` → `npm ci` (reproducible).
- [ ] Remove redundant `COPY` lines (db_migrate.py, App.js).
- [ ] Remove unused `ENV FLASK_APP`; keep `PYTHONUNBUFFERED`, `DB_FILE`,
  `FRONTEND_BUILD_DIR`.
- [ ] `.dockerignore`: add `__pycache__`, `*.pyc`, `tests`, `doc`, `memory.md`,
  `.git` keep.

## Phase 5 — Port valid tests, delete stale ones
- [ ] Port to env DB_FILE / real build dir: `test_story2_api`, `test_price_chart`,
  `test_airport_persistence`, `stories/test_story2_schema::test_flights_table_exists`,
  `test_single_container` (8088:80), `test_app_integration` (current imports).
- [ ] Delete: `test_story1_airport.py`, `test_story2_scraper.py`,
  `test_fix_scrape_parse.py`, `test_fix_template_notfound.py`,
  `test_story2_schema::test_flights_columns` (with per-file justification in PR).

## Phase 6 — Fix workflows
- [ ] `ci.yml`: no `|| true`; setup-python 3.11 + setup-node (npm cache);
  install `requirements-dev.txt`; `cd frontend && npm ci && npm run build`;
  run `pytest tests/` excluding infra-only tests (`test_docker_build.py`,
  `test_price_chart_playwright.py`, `tests/frontend`). Broaden push branches to
  feature patterns.
- [ ] `docker-publish.yml`: drop `pull_request` trigger; `cache-to: type=registry`
  branch-scoped `mode=max` with matching `cache-from`; remove dead `CACHEBUST`.
- [ ] `ghcr-cleanup.yml`: per-version keep logic; fixed login username
  (`x-access-token` + GITHUB_TOKEN); `set -euo pipefail`; fail on unexpected
  delete status.

## Phase 7 — Validate
- [ ] `python -m pytest tests/ --ignore=tests/frontend --ignore=tests/test_price_chart_playwright.py --ignore=tests/test_docker_build.py` → all green.
- [ ] `python -m skybreak.db_migrate` exits 0 (clean DB).
- [ ] `docker build` if a daemon is available; else note it and rely on the
  Dind-capable publish workflow.

## Plan-review checklist
- [x] Order correct (tests before code where feasible; conftest before ported tests).
- [x] No missing dependencies (fast-flights pinned; dev file chains runtime).
- [x] Review log updated — this plan + design doc; PR description to summarize.
