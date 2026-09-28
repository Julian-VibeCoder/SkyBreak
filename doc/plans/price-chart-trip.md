# Plan: Price-Chart auf Favorisiertem Trip (Preisseite)

> **Iteration-Review:** Plan geschrieben → gegen User-Story 8 + Architektur geprüft → gegen Design-Regeln (feature-basiert, kein globales DESIGN.md) geprüft → iterativ verfeinert (Button-Position, 3 Kurven, Zeitraum, Playwright-Test mit Mounts). Zufrieden.

**Ziel:** Auf der Preis-Seite für einen favorisierten Trip einen Button neben Löschen hinzufügen, der einen Chart mit 3 Kurven öffnet (Hin, Rück, Gesamtpreis) für den Zeitraum, zu dem Preisinformationen vorliegen.

**Architektur:** React-Frontend (Button + Modal/Overlay + SVG/Chart) + Flask-API (`/api/prices/history?trip_id=...`) + SQLite (`flight_prices` / `trip_prices`). Container mit `/data`-Mount (DB) + `/opt/skybreak` (kompatibel compose-example).

**Technik:** React, Flask, SQLite, Playwright (In-Container-Testing), SVG-Chart (kein externer Chart-Lib-Zwang, da bereits SVG-Pattern im Repo vorhanden).

---

## Spezifikation / User-Story
- User-Story 8 (Price History Chart): Chart zeigt Preisverlauf pro monitored trip.
- Zusatz-Req: Button auf Favoriten in Preisseite; 3 Kurven (Hin, Rück, Gesamt); Zeitraum = vorhandene Preisdaten.

---

### Task 1: Design & API-Plan
- [x] Design-Dok unter `doc/designs/price-chart-trip.md` (feature-basiert, nicht global)
- [x] API-Plan: `GET /api/prices/history?trip_id=<id>` → `[{date, outbound_price, return_price, total_price}, ...]`
- [x] DB-Abfrage gegen `flight_prices` / `trip_prices` (Schema prüfen)

### Task 2: Backend-Endpoint + DB
**Files:** `skybreak/app.py`, `tests/test_price_chart.py`
- [ ] Test schreiben: `test_price_chart_history_returns_3_series`
- [ ] Endpoint implementieren: Query nach `trip_id` + Datum, 3 Preisfelder zurückgeben
- [ ] DB-Migration falls nötig (Schema-Version in `db_version`)

### Task 3: Frontend-Button + Chart-Modal
**Files:** `frontend/src/App.js` (oder Preisseite-Komponente)
- [ ] Button neben Löschen-Button auf Favorit in Preisseite
- [ ] Click öffnet Modal/Overlay mit Chart
- [ ] 3 SVG-Linien: Hin (z.B. blau), Rück (orange), Gesamt (grün)
- [ ] Zeitraum = Min/Max Datum der zurückgegebenen Daten

### Task 4: Container-Deploy + Mount
**Files:** `docker-compose.yml` (example-Referenz), `.env`
- [ ] Use Mount points wie compose-example: `/data:/data` (DB), ggf. `/opt/skybreak` für App
- [ ] `DB_FILE=/data/skybreak.db`
- [ ] Build: `docker build -t skybreak-local .`
- [ ] Run: `docker rm -f flightbreak && docker run -d --name flightbreak -p 8088:80 -v /data:/data -v /opt/skybreak:/opt/skybreak skybreak-local`

### Task 5: Playwright-Test im Container
**Files:** `tests/test_price_chart_playwright.py`
- [ ] Test: Button klicken → Modal sichtbar → 3 Kurven-Elemente im DOM
- [ ] Ausführen mit `docker exec flightbreak python -m pytest ...` oder von Host mit Port 8088
- [ ] Mit compose-Mounts (`/data` persistent)

---
**Review-Checkliste (selbst geprüft):**
- [x] User-Story 8 abgedeckt
- [x] Architektur konsistent (Flask + React + SQLite + Docker)
- [x] Keine Live-Patches (DB/Container-Edits nur via Code + Rebuild)
- [x] Design-Doku feature-basiert (`doc/designs/price-chart-trip.md`)
- [x] Plan-Review durchgeführt (iterativ verfeinert)
- [x] Tests zuerst gefordert (Task 2 + 5)

**Hinweis zu Mounts:** Compose-Beispiel zeigt `/data` für DB + `/opt/skybreak` für App-Data. Container startet mit `DB_FILE=/data/skybreak.db`; Migration/Bildung passiert im Code (`init_db` / `db_migrate`), nicht live.
