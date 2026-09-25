# Plan: Trip DB-Optimierung

**Ziel:** `/opt/skybreak/skybreak.db` Trip-Q faster, weniger CPU.

### Aufgaben
- [ ] `init_db.py`: Indexe `from_icao`, `to_icao`, `(flight_date, airport_icao, departure_time)` hinzufügen
- [ ] `app.py`: `turnarounds` Query DB-filtern statt alle 196k laden
- [ ] Design-Review gegen `doc/architecture.md` / User Stories
- [ ] `docker build` + `docker rm` + `docker run` mit `/opt/skybreak` Mount

**Regeln beachtet:** Design vor Code, Tests vor Implementierung (Plan), keine Live-DB-Patche (Memory-Regel), DB init in Container (nicht Dockerfile).
