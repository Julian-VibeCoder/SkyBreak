# Design: Build / CI / Docker Pipeline Fixes

Goal: Make the GitHub Actions and Docker build actually work and gate meaningfully,
slim the image, and fix a broken DB migration + broken price-scraping runtime dependency.

Context (from code review of `Dockerfile`, `.github/workflows/*`, `skybreak/db_migrate.py`):
The build *succeeds*, but the pipeline is not doing its job and there are real bugs.

## Findings & fixes (priority order)

### 1. CI can never fail + runs only 1 trivial test  → `.github/workflows/ci.yml`
- The run line ends in `|| (… || true)`, so the step **always exits 0** → branch
  protection is meaningless.
- It runs only `tests/test_bugix_fixes.py` (3 file-existence asserts), installs no
  runtime deps and never builds the frontend.
- **Fix:** install runtime + test deps, build the frontend, run the real portable
  suite. Remove `|| true`. No fall-back that swallows failures. Exclude
  infra-only tests (Docker daemon, Playwright browser, JS dir) explicitly.
- Test-suite drift: 11 tests fail on `main` (hardcoded `/data` paths, removed
  `flight_scraper` module, stale `year_ahead` column, `8088:80` vs `80:80`,
  order-dependent `save_flights`). → add `tests/conftest.py` (temp DB + migration +
  build dir), port valid tests to the env, delete stale/redundant/unused tests,
  and add new tests for the areas that changed (see "New tests").

### 2. `docker-publish.yml` fails on every PR + cache not persisted + dead arg
- Triggers on `pull_request` **and** does `push: true` → GITHUB_TOKEN is read-only
  on PR events → every PR build fails.
- `cache-to: type=inline` returns the cache to stdout but **stores it nowhere** →
  no cross-run caching. The "invalidate when frontend/src changes" comment is not
  implemented.
- Passes `build-args: CACHEBUST=${{ github.sha }}` but the Dockerfile has **no**
  `ARG CACHEBUST` → silently ignored.
- **Fix:** drop the `pull_request` trigger; persist cache to a registry ref
  (`type=registry`, branch-scoped, `mode=max`); remove the dead `CACHEBUST` arg.

### 3. `ghcr-cleanup.yml` deletes the `main` image + can't login on schedule
- Decides KEEP/DELETE **per tag** but `DELETE`s **per version** → a version carrying
  both `main` and a branch tag gets deleted when the branch tag is processed,
  wiping `:main`.
- `username: ${{ github.actor }}` is **empty** on `schedule` events → the nightly
  login fails and cleanup never runs.
- **Fix:** per-**version** keep logic (keep if *any* tag is `main`/`v*`); fixed
  non-empty login username (`x-access-token` + GITHUB_TOKEN); fail on unexpected
  API status.

### 4. Dockerfile: ~200 MB unused browser/GTK libs + non-reproducible build
- Final stage installs `libgtk-3-0 libnss3 libasound2 libxss1 libgbm1 …` —
  Chromium/Playwright runtime deps. Nothing at runtime uses a browser (Playwright is
  test-only; the price scraper uses `primp`+`selectolax`, pure HTTP).
- `npm install` (Dockerfile) vs `npm ci` (old CI) → non-reproducible.
- Redundant `COPY` lines for `db_migrate.py`/`App.js` (already in the dir COPY).
- `ENV FLASK_APP=skybreak.app` unused (CMD runs `python -m skybreak.app`).
- **Fix:** keep only `libsqlite3-0`; use `npm ci`; drop redundant COPYs and
  `FLASK_APP`; extend `.dockerignore` (`__pycache__`, `tests/`, `doc/`, `*.pyc`).

### 5. Migration v11 broken + duplicated `apply_migrations` + settings wiped → `db_migrate.py`
- `migration_v11` drops `start_time/return_time/trip_date` from `favorite_trips`
  but those columns are in the `idx_favorite_unique` index (created v7) → SQLite
  refuses the drop → version stuck at 10, re-fails every startup.
- `apply_migrations` is defined twice and there are two `__main__` guards; the first
  guard fires **before** `migration_v11` is defined → `python -m skybreak.db_migrate`
  crashes with `NameError`.
- `apply_migrations` deletes every setting not in a 5-key whitelist, so
  `price_fetch_interval_hours` (read by the price scheduler) is wiped on every
  restart even if the user set it.
- **Fix:** single clean `apply_migrations` + one `__main__` guard; v11 drops the
  unique index, then the columns, then recreates the index on surviving columns;
  add `price_fetch_interval_hours` to the settings whitelist.

### Runtime dependency bug (found while making CI green)
- `get_flight_price.py` imports `FlightQuery, create_query` from `fast_flights`, but
  the pinned package (latest `fast-flights` 2.2 at review time) has no such API →
  the price endpoints 500. **`fast-flights 3.1.0` does exist on PyPI**
  (requires Python ≥3.10; deps `primp`, `protobuf>=5.27.0`, `selectolax`).
- **Fix:** pin `fast-flights==3.1.0` and list the runtime deps explicitly
  (`primp`, `protobuf>=5.27.0`, `selectolax`, `typing_extensions`); remove the
  duplicate `requests` and move `pytest` to a dev requirements file.

## Design-review checklist
- [x] User Stories covered — tests deleted are redundant/stale; coverage preserved
      (portable conftest) and new tests added for CI/Docker/migration/config.
- [x] Architecture consistent — only test config, workflows, image deps, and the
      migration module change; no runtime endpoint behavior changes beyond the
      dependency fix that makes the existing price endpoints work again.
- [x] CI/Workflow compatible — CI now runs Python 3.11 (app target, ≥3.10 needed by
      fast-flights 3.1), builds frontend, runs the portable suite (no `|| true`).
- [x] Documentation updated — this design + plan + PR description.

## New / changed tests
- NEW `tests/conftest.py` — portable temp DB + migration + frontend build dir.
- NEW `tests/test_db_migration.py` — v11 reaches 11, drops the 3 columns + recreates
  index, idempotent, and `python -m skybreak.db_migrate` exits 0.
- NEW `tests/test_settings_persistence.py` — `price_fetch_interval_hours` survives
  migration; non-whitelisted settings are removed; google_consent seed present.
- NEW `tests/test_ci_config.py` — guards the workflow/Docker fixes from regression:
  no `|| true` in ci.yml, `docker-publish` does not push on `pull_request` and uses
  a persisted (registry) cache, no dead `CACHEBUST` arg, `ghcr-cleanup` uses
  per-version keep + fixed login username.
- Ported (env, kept): `test_story2_api`, `test_price_chart`,
  `test_airport_persistence`, `test_story2_schema::test_flights_table_exists`,
  `test_single_container`, `test_app_integration`.
- Deleted (stale/redundant/unused, with justifications):
  `test_story1_airport.py`, `test_story2_scraper.py`, `test_fix_scrape_parse.py`,
  `test_fix_template_notfound.py`, `test_story2_schema::test_flights_columns`.
- Excluded from CI (infra-only, kept in repo): `test_docker_build.py`,
  `test_price_chart_playwright.py`, `tests/frontend/*`.
- Removed dead/unused files: `requirements_clean.txt`.
