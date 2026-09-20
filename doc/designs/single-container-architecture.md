# Design: Single-Container Architecture — SkyBreak

## Intent
Redesign from 2 containers (app + nginx) → 1 container serving frontend on port 80, SQLite file mount only external data.
No static HTML files; frontend is built React served by Flask.

## Constraints from User
- One Docker container
- Port 80 exposed
- SQLite DB file (`skybreak.db`) as external volume mount (only external data)
- Business logic + frontend inside container
- User Stories 1–14 must be supported (Airports, Flights, Turnarounds, Monitoring, Price Charts, Telegram)

## Proposed Architecture (Approach A — Monolith)

```
+----------------------------------------+
|  Single Container (port 80)            |
|  +------------------+ +--------------+ |
|  | React Frontend   | | Flask API    | |
|  | (built to /app/  | | (python 3.11)| |
|  |  frontend/dist)  | | skybreak/    | |
|  +--------+---------+ +------+-------+ |
|           |                  |         |
|           +--------+---------+         |
|                    |                   |
|            +------+-------+            |
|            | SQLite DB     |            |
|            | /data/skybreak.db (mount)|
|            +---------------+            |
+----------------------------------------+
```

### Components
1. **Frontend (React)** — `frontend/src/`. Built via `npm run build` → static bundle served by Flask at `/`. No static HTML files in repo; only source + build output in container.
2. **Backend (Flask)** — `skybreak/app.py` + modules. Routes: `/` (serve React index.html), `/api/airports`, `/api/flights`, `/api/turnarounds`, `/api/monitoring`, `/api/prices`, `/api/telegram`. SQLite via `sqlite3` (stdlib) to mounted file.
3. **Data (SQLite)** — file `skybreak.db` mounted at `/data/skybreak.db`. Only persistent external state.
4. **Build step** — `Dockerfile` installs Node + Python, runs `npm install && npm run build`, then copies everything.

### Data Flow
- User → Port 80 → Flask
- React SPA loads → calls `/api/*`
- Flask reads/writes `/data/skybreak.db` (mount)
- Price charts via frontend Chart.js + backend price data
- Telegram bot triggered by backend scheduler / endpoint (optional per Story 9)

### Compatibility Check — User Stories
- Story 1 (Airports): `/api/airports` + React form ✓
- Story 2 (Load flights): scraper integration or import endpoint ✓
- Story 3 (Turnarounds): backend algorithm, stored in DB ✓
- Story 4 (Days off): config endpoint + DB field ✓
- Story 5 (Monitor trips): DB table + UI list ✓
- Story 6 (Scraper): backend service / cron inside container ✓
- Story 7 (24h check): scheduled task or endpoint invoked externally ✓
- Story 8 (Price chart): `/api/prices` + frontend chart ✓
- Story 9 (Telegram): backend bot call ✓
- Story 10/11 (Remove): DELETE endpoints ✓
- Story 13/14 (Filter/Prices): query params + response fields ✓

### Technology Stack (updated from doc/architecture.md)
- Container: `python:3.11-s` + `nodejs`/`npm`
- Frontend: React (source only, built in image)
- Backend: Flask (Python 3.11)
- DB: SQLite (file mount, single file)
- Port: 80

## Design Review
- [x] User Stories abgedeckt (1–14)
- [x] Architektur konsistent (1 Container, 1 Port, 1 DB-Mount)
- [x] Keine statischen HTML-Dateien (nur React-Source + Build)
- [x] Docker Compose reduziert auf 1 Service
