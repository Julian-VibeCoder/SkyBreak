# SkyBreak — Project Review Findings

**Review Date:** 2026-09-22  
**Scope:** Architecture, technologies, code quality, tests, GitHub Actions, Docker build/process, docs, user-stories alignment  
**Head:** `main` (40ec397)

---

## 1. Architecture & Design

### Finding: Architecture doc describes a technologies stack that does not match the codebase
- **File:** `doc/architecture.md`
- **Severity:** HIGH
- **Evidence:** Doc claims "Backend: Node.js + Express", "Frontend: React + Tailwind CSS", "Scraping: Open-source Google Flight Scraper", "Notifications: Telegram Bot API", "Charts: Chart.js". Actual stack: Python/Flask backend (`skybreak/app.py`), React frontend with inline-styles (not Tailwind), RapidAPI `aerodatabox` scraper (`skybreak/flight_scraper.py`), SQLite DB (`skybreak.db`), no Telegram integration, no Chart.js.
- **Solution:** Rewrite `doc/architecture.md` to match actual implementation; remove unimplemented components from architecture unless planned; add a "Current vs Planned" delta section.

### Finding: User stories contain copy-paste errors and missing acceptance criteria
- **File:** `doc/user-stories.md`
- **Severity:** MEDIUM
- **Evidence:** Stories 1–12 repeat identical acceptance criteria blocks ("Frontend input form validates and submits to backend API / Backend stores validated code / UI displays stored airport list"). Stories 3, 4, 5, 6, 7, 8, 9, 10, 11 all contain the same copied block instead of story-specific criteria. Story 13 (filter by date) and 14 (visible prices) are truncated/incomplete.
- **Solution:** Rewrite acceptance criteria per story; remove duplicated blocks; complete Stories 13–14.

### Finding: Design / Plan docs exist but are disconnected from code state
- **Files:** `doc/designs/`, `doc/plans/`
- **Severity:** LOW
- **Evidence:** Design docs (`agent-workflow.md`, `single-container-architecture.md`, `story-1-airport-entry.md`, `story2.md`) describe a planned architecture; code has diverged (e.g., multi-service compose described, but single-container architecture is used; frontend uses inline styles rather than Tailwind). Plans reference `DESIGN.md`/`PLAN.md` globally, but repo policy (`AGENTS.md`) requires feature-based names under `doc/designs/<Feature>.md`.
- **Solution:** Update design docs to reflect actual single-container + Flask + React architecture; align file naming with `AGENTS.md` policy.

---

## 2. Technologies Used

### Finding: Dependency versions unpinned; no lockfile for Python
- **File:** `requirements.txt`
- **Severity:** MEDIUM
- **Evidence:** Only package names listed (`flask`, `pytest`, `requests`, `tenacity`, `apscheduler`). No `==` versions, no `requirements-dev.txt`, no `poetry.lock`/`Pipfile.lock`. `frontend/package-lock.json` exists but `npm ci` in Dockerfile relies only on `package-lock.json`; `requirements.txt` has no equivalent.
- **Solution:** Pin versions (`flask==3.x`, `requests==2.x`, etc.); generate `requirements-lock.txt` or use `pip-compile`; document upgrade policy.

### Finding: Deprecated / risky APIs in use
- **Files:** `skybreak/airport.py`, `skybreak/app.py`
- **Severity:** MEDIUM
- **Evidence:** `datetime.utcnow()` (deprecated in Python 3.12+); `sqlite3.connect()` without `check_same_thread=False` when accessed from Flask threads; `urllib.request.urlopen` for airport lookup without caching timeout/TTL.
- **Solution:** Replace `utcnow()` with `datetime.now(timezone.utc)`; add `check_same_thread=False` or use connection pooling; add TTL/cache invalidation to `_airport_cache`.

---

## 3. Code Quality — Backend (`skybreak/`)

### Finding: DB path inconsistency and schema drift
- **Files:** `skybreak/airport.py` (`DB_PATH = "/data/skybreak.db"`), `init_db.py` (uses `DB_FILE` env), `docker-compose.yml` (mount `"/opt/skybreak/:/data/"` — wrong source path), `tests/test_single_container.py` (expects `/data/skybreak.db` in compose)
- **Severity:** HIGH
- **Evidence:** Compose mounts host `/opt/skybreak/` to container `/data/`, but `DB_PATH` expects container `/data/skybreak.db`. If host `/opt/skybreak/` doesn't exist, DB is created inside container, lost on restart. `test_single_container.py` asserts `/data/skybreak.db` is in compose, but it's not — the mount is `/opt/skybreak/`. `init_db.py` uses `DB_FILE` env (defaults to `skybreak.db`, relative to CWD); `app.py` hardcodes `/data/skybreak.db`; `airport.py` hardcodes `/data/skybreak.db`.
- **Solution:** Unify DB path via env (`DB_FILE=/data/skybreak.db`) everywhere; fix compose mount to `./data:/data` or similar; ensure `init_db.py`, `airport.py`, `app.py`, `scraper_job.py` all read from `os.environ.get("DB_FILE", "/data/skybreak.db")`.

### Finding: Migration logic present but fragile
- **Files:** `skybreak/airport.py` (`init_db()`), `AGENTS.md`
- **Severity:** MEDIUM
- **Evidence:** `init_db()` tries `ALTER TABLE` for missing columns (`airport_name`, `destination_name`, `flight_number`, `year_ahead`). Works for incremental updates, but if table was never created (empty DB) it creates with base schema, then tries to add columns — safe. However, `init_db()` does not create `flights` table with all columns in one `CREATE TABLE`; it creates with minimal columns then alters. `tests/test_story2_schema.py` asserts columns `airport_code` (should be `airport_icao`), `scheduled_departure` (should be `departure_time`) — schema assertions don't match actual DB.
- **Solution:** Use a single canonical `CREATE TABLE IF NOT EXISTS` with all columns; update tests to assert actual column names.

### Finding: Scraper fails to parse nested RapidAPI responses; test proves it
- **Files:** `skybreak/scraper_job.py`, `tests/test_fix_scrape_parse.py`
- **Severity:** HIGH
- **Evidence:** `save_flights()` reads `dep.get("scheduledTime")` as dict or string. If `scheduledTime` is `{"utc":"..."}`, it handles it; but test input uses `{"scheduledTime":{"utc":"2026-09-21 10:25Z"}}` with `airport.icao` — `save_flights` skips because `dep_time` extraction expects `scheduledTime` to be either string or dict with key `utc`; the test passes a nested dict, but code path may miss it due to `if isinstance(dep_time_raw, dict): dep_time = dep_time_raw.get("utc")` — this should work, yet `assert len(rows) == 1` fails with 0 rows, meaning either insertion was skipped (duplicate check, self-flight skip, or exception swallowed). The `except Exception: continue` swallows all errors silently.
- **Solution:** Add structured logging inside `save_flights()` for every `continue`; fix `scheduledTime` parsing to handle both `{"utc":"..."}` and `{"local":"..."}`; do not swallow exceptions silently — log at WARNING.

### Finding: Rate-limit backoff logic has logic errors and long sleeps
- **File:** `skybreak/airport.py` (`trigger_fetch_for_airport`)
- **Severity:** MEDIUM
- **Evidence:** First 429 sets `wait_time = 30*60` (30 min), then doubles (`wait_time *= 2`). Loop calls `time.sleep(wait_time)` inside `except` but continues loop with same `current_start`, so it retries same window after sleep — okay. But `wait_time = 0` at start; first success doesn't reset; if a later window fails, first backoff is 30 min (okay). However, `logger.info` on 429 uses `wait_time if wait_time > 0 else 30*60` which is redundant. More importantly: `trigger_fetch_for_airport` opens two connections (`conn`, `conn2`) but never closes `conn` until end (line 108); if exception occurs before line 108, `conn` leaks. `start_dt = datetime.utcnow()` is deprecated.
- **Solution:** Use `with sqlite3.connect(...)` or explicit `finally: conn.close()`; replace `utcnow()`; log exact exception message.

### Finding: `clean_old_flights()` deletes past flights — may delete data needed for price history
- **File:** `skybreak/scraper_job.py`
- **Severity:** MEDIUM
- **Evidence:** `DELETE FROM flights WHERE departure_time < datetime('now')` removes all past flights every interval. If price history references historical flights, they are deleted immediately. `AGENTS.md` requires DB migration for existing DB; deleting historical data conflicts with Story 8 (price history chart).
- **Solution:** Add `created_at` or archive table for history; only delete flights older than retention period; document retention policy.

---

## 4. Code Quality — Frontend (`frontend/`)

### Finding: No build errors, but inline styles and missing features
- **File:** `frontend/src/App.js`
- **Severity:** LOW
- **Evidence:** React 18, `react-scripts` build works (`frontend/build/` exists). UI has tabs (airports, flights, trips, costs, settings) but trips/costs are empty shells (lines 196–212). Settings page works; airport input validates IATA (`/^[A-Z0-9]{3}$/`). No Tailwind usage despite doc claim.
- **Solution:** Complete trips/costs tabs if required; document that inline CSS is intentional for self-contained build; if Tailwind is required, add it to `package.json` and rebuild.

### Finding: Date filter uses exact match, but SQL uses `date(departure_time)`
- **File:** `skybreak/app.py` (line 53)
- **Evidence:** `date_filter = request.args.get('date').strip()`; SQL `date(departure_time) = ?`. Works if `date_filter` is `YYYY-MM-DD`. No validation of format; empty string could cause mismatch.
- **Solution:** Validate `date_filter` with regex `^
\d{4}-\d{2}-\n\d{2}$`; reject malformed.

---

## 5. GitHub Actions

### Finding: CI workflow is a stub — does not run full test suite
- **File:** `.github/workflows/ci.yml`
- **Severity:** HIGH
- **Evidence:** Only runs `test_bugix_fixes.py` with `pytest`; fallback uses `unittest discover`. No install of `requirements.txt`; no `python -m pytest` on full suite; no build check for frontend; no Docker health check. `CI-CONFIG.md` describes a full TDD pipeline but workflow doesn't match.
- **Solution:** Update `ci.yml` to: install Python deps (`pip install -r requirements.txt`), install frontend deps (`npm ci`), build frontend (`npm run build`), run full pytest (`python -m pytest`), run Docker build (`docker build -t skybreak .`) and smoke test.

### Finding: Docker publish workflow pushes on PR
- **File:** `.github/workflows/docker-publish.yml`
- **Severity:** MEDIUM
- **Evidence:** `push: ${{ github.event_name != 'pull_request' }}` — pushes on PR? Actually expression is `!= 'pull_request'`, so for PR (`pull_request`) `push` = `false`, which is correct (no push on PR). But metadata tags include `type=ref,event=pr`, creating tags for PRs that are never pushed — harmless but noisy. Workflow uses `GITHUB_TOKEN` with `packages: write`; okay for GHCR.
- **Solution:** Remove PR tag type or keep; verify `docker/login-action` succeeds; add `docker build` step to CI so build is validated before publish.

### Finding: `CI-CONFIG.md` contradicts actual workflow
- **File:** `CI-CONFIG.md`
- **Severity:** LOW
- **Evidence:** `CI-CONFIG.md` shows a simple `echo "Tests executed..."`; actual `.github/workflows/ci.yml` is different (runs `test_bugix_fixes.py`). The doc is stale.
- **Solution:** Update `CI-CONFIG.md` to reflect actual workflow file names and commands.

---

## 6. Docker Build & Compose

### Finding: Multi-stage Dockerfile exists but compose uses wrong volume and separate frontend service
- **Files:** `Dockerfile`, `docker-compose.yml`
- **Severity:** HIGH
- **Evidence:** Dockerfile builds React app (`npm ci && npm run build`) and copies `frontend/build` to final image; exposes 80; runs `python -m skybreak.app`. Compose defines TWO services (`app` + `frontend` with nginx:alpine mounting `./frontend` directly, ignoring the built `frontend/build`). Compose mount for `app` is `"/opt/skybreak/:/data/"` — source path `/opt/skybreak/` likely doesn't exist on host; DB path broken.
- **Solution:** Align compose with Dockerfile: either (a) remove `frontend` service and let Flask serve `frontend/build` (as `app.py` does with `static_folder`), or (b) keep nginx frontend but build it separately and mount `frontend/build`. Fix volume to `./data:/data` or use named volume. Ensure `.dockerignore` excludes `node_modules` and `*.db` (it does).

### Finding: Dockerfile builder stage includes unnecessary build tools in final image
- **File:** `Dockerfile`
- **Severity:** LOW
- **Evidence:** Builder installs `gcc`, `libsqlite3-dev`, `nodejs`, `npm`; final stage only installs `libsqlite3-0`. This is correct multi-stage. But `COPY --from=builder /app/init_db.py .` copies after DB init; if `DB_FILE` env points to `/data/skybreak.db`, `init_db.py` at build time creates DB in `/app` (or relative), not in `/data`. Final image has no DB initialization at runtime unless `app.py` calls `init_db()` (it does at import time, line 11).
- **Solution:** Ensure `init_db.py` uses `DB_FILE` env; verify runtime DB creation works with empty `/data` mount.

### Finding: `.dockerignore` excludes `.git` and `*.db` but misses `__pycache__` build artifacts
- **File:** `.dockerignore`
- **Severity:** LOW
- **Evidence:** `.dockerignore`: `node_modules`, `frontend/src/.gitkeep`, `*.db`, `.git`, `.tmp`. Missing `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.env`, `skybreak.db` (covered by `*.db`).
- **Solution:** Add `__pycache__/`, `*.pyc`, `.env`, `.pytest_cache/`, `*.egg-info/`.

---

## 7. Tests

### Finding: Several tests are empty assertions or assert wrong schema
- **Files:** `tests/test_fetch_max_days_luecken.py` (`assert True` x2), `tests/test_story2_schema.py` (wrong column names), `tests/test_bugix_fixes.py` (tests file removal, not logic), `tests/test_workflow.py` (tests git branch/files existence — meta tests)
- **Severity:** MEDIUM
- **Evidence:** `test_fetch_max_days_luecken.py`: both functions just `assert True`; no test of gap logic. `test_story2_schema.py`: asserts `airport_code`, `scheduled_departure`, `scheduled_arrival` — actual columns are `airport_icao`, `departure_time`; test will fail if DB matches real schema. `test_workflow.py`: asserts `DESIGN.md` and `PLAN.md` exist — they don't (only `doc/designs/` and `doc/plans/` exist); test fails.
- **Solution:** Rewrite `test_fetch_max_days_luecken.py` to test window logic; fix `test_story2_schema.py` to match actual columns; remove meta-tests or update them to match repo policy (`AGENTS.md` requires feature-based docs, not global `DESIGN.md`).

### Finding: One real test fails: scraper save logic
- **File:** `tests/test_fix_scrape_parse.py`
- **Severity:** HIGH (verified failure)
- **Evidence:** `test_save_flights_parses_nested` fails — 0 rows inserted for valid input. Root cause likely silent exception swallowing in `save_flights()` or duplicate-check rejecting valid first insert.
- **Solution:** Add debug logging; fix parsing; re-run until passes.

---

## 8. Documentation & Process

### Finding: `AGENTS.md` requires feature-branch + design-review + TDD, but no feature branch for current state
- **File:** `AGENTS.md`
- **Severity:** MEDIUM (process)
- **Evidence:** `AGENTS.md` mandates `git checkout -b ...`, design doc under `doc/designs/<Feature>.md`, tests first, then implementation, PR only with approval. Current repo is on `main` with unmerged design/plans; no `feature/` branch for the current fixes. `tests/test_workflow.py` asserts branch `agent-workflow-instructions` exists; it doesn't.
- **Solution:** Create feature branch `feature/review-refactor`; complete design doc; fix tests; implement solutions; open PR when ready.

### Finding: Database migration requirement documented but not fully validated
- **File:** `AGENTS.md` (line 31–33), `docker-compose.yml`
- **Severity:** MEDIUM
- **Evidence:** `AGENTS.md` says container must handle empty/missing DB and migrate existing DB. `init_db()` does create + alter, but if DB file is missing at startup (`/data/skybreak.db` not mounted or missing), `sqlite3.connect` creates empty file; `app.py` calls `init_db()` at import, so it works. However, `docker-compose.yml` volume `"/opt/skybreak/:/data/"` means DB may not exist at expected path.
- **Solution:** Validate with `docker-compose up` from clean state; ensure `/data/skybreak.db` created; verify migration from old schema works.

---

## Summary Table

| Area | Finding | Severity | Status |
|---|---|---|---|
| Architecture doc | Technology stack mismatch | HIGH | Needs rewrite |
| User stories | Copy-paste acceptance criteria | MEDIUM | Needs edit |
| DB / Code | Path inconsistency (`DB_PATH` vs compose vs env) | HIGH | Fix unify |
| Scraper / DB | `save_flights()` silent failure; test fails | HIGH | Fix parsing + logging |
| CI / GitHub | CI stub; does not run full suite or build | HIGH | Update workflow |
| Docker / Compose | Wrong volume; separate frontend service ignores build | HIGH | Align compose with Dockerfile |
| Tests | Empty assertions; wrong schema assertions | MEDIUM | Rewrite |
| Process | Feature branch / PR rules not followed for current state | MEDIUM | Create branch + PR |

---

## Recommended Refactoring Plan (Minimal)

1. **Unify DB path** (1 file): `DB_PATH = os.environ.get("DB_FILE", "/data/skybreak.db")` in all modules; fix compose volume.
2. **Fix scraper parsing + logging** (2 files): `save_flights()`; add structured log; fix `test_fix_scrape_parse.py`.
3. **Update CI** (1 file): `.github/workflows/ci.yml` — install deps, build frontend, run full tests, build Docker.
4. **Align compose** (1 file): `docker-compose.yml` — fix volume, decide single-service vs nginx, match Dockerfile.
5. **Update docs** (2 files): `doc/architecture.md` (match reality); `doc/user-stories.md` (fix criteria); add `.dockerignore` entries.
6. **Process**: Create `feature/review-refactor` branch; complete `doc/designs/review-refactor.md`; write/update tests; implement; PR.

---

*This review was generated by inspection of the repository at `/projects/vacation` (main @ 40ec397). All file paths and line references are verified against current HEAD.*
--- FIXED (Post-Review Verification) ---
- Finding 3 (DB): init_db.py fixed (/data/skybreak.db default); init_db creates tables with created_at column; container creates DB at startup (Dockerfile removed build-time DB init)
- Finding 4 (Frontend): FRONTEND_BUILD_DIR defaults to /app/frontend/build; Dockerfile builds frontend via npm build; container serves static files correctly
- Finding 5 (Actions): CI-CONFIG.md updated; tests updated; workflow runs pytest
- Docker Build: Verified (skybreak-local:latest builds)
- Container Persistence: DB (/data mount) persisted through recreation
- Cleanup: All test containers and volumes removed
