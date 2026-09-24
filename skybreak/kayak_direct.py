#!/usr/bin/env python3
"""Kayak-Direktflug-Scraper: Abflüge und Ankünfte eines Flughafens als JSON.

Liest von kayak.com/direct alle Nonstop-Flüge ab und zu einem Flughafen
(IATA-Code) aus und speichert sie als flache JSON-Liste mit einem Eintrag
pro konkretem Flugtag.


INSTALLATION
============

Benötigt Python 3.9+ sowie die Pakete `requests` und `airportsdata`
(Zeitzonen der Flughäfen, für die Flugdauer). Da das System-Python unter
Ubuntu/Debian keine pip-Installation erlaubt (PEP 668), nutzt man eine
virtuelle Umgebung. `--system-site-packages` sorgt dafür, dass das
System-`requests` mit den System-Zertifikaten verwendet wird (nötig hinter
einem Firmen-Proxy mit eigenem Zertifikat):

    python3 -m venv --system-site-packages .venv
    .venv/bin/pip install airportsdata requests


BENUTZUNG
=========

    .venv/bin/python kayak_direct.py IATA [Optionen]

Argumente und Optionen:

    IATA                      IATA-Code des Flughafens, z. B. FRA, FKB, STR
                              (Groß-/Kleinschreibung egal).
    -m, --months YYYY-MM ...  Nur diese Monate abfragen. Ohne Angabe werden
                              alle Monate geholt, die Kayak anbietet
                              (in der Regel aktueller Monat + 11).
    -d, --direction RICHTUNG  both (Standard), departures oder arrivals.
    -o, --output DATEI        Zieldatei. Standard: <IATA>_direct.json
    --delay SEKUNDEN          Pause zwischen zwei Anfragen (Standard 0.5).
                              Erhöhen, falls Kayak Anfragen blockiert.

Beispiele:

    # Kompletter Flugplan (alle Monate, beide Richtungen) -> FKB_direct.json
    .venv/bin/python kayak_direct.py FKB

    # Nur Oktober und November 2026
    .venv/bin/python kayak_direct.py FRA -m 2026-10 2026-11

    # Nur Abflüge, eigene Zieldatei, langsamer
    .venv/bin/python kayak_direct.py FRA -d departures -o fra_dep.json --delay 1

Fortschritt und Fehler werden auf stderr ausgegeben, die Daten landen
ausschließlich in der JSON-Datei.

Laufzeit: Pro Monat eine Anfrage für die Zielliste plus pro Ziel eine
Anfrage je Richtung. Beispiele mit Standard-Delay:
    FKB (~40 Ziele),  1 Monat, beide Richtungen:  ca. 1 Minute
    FRA (~260 Ziele), 1 Monat, beide Richtungen:  ca. 5 Minuten
    FRA, alle 12 Monate:                          ca. 1 Stunde


JSON-FORMAT
===========

Die Datei enthält eine flache Liste von Flügen, ohne weitere Metadaten,
sortiert nach Datum, Abflugzeit und Flugnummer. Jeder Eintrag ist genau
ein Flug an genau einem Tag. Ein Flug, der jeden Dienstag stattfindet,
erscheint also für einen Monat mit vier Dienstagen als vier Einträge.

    [
      {
        "date": "2026-10-01",
        "flight_number": "SQ25",
        "from": "FRA",
        "to": "SIN",
        "departure": "12:15",
        "arrival": "06:50",
        "arrival_date": "2026-10-02",
        "duration_min": 755
      },
      ...
    ]

Felder:

    date           Abflugdatum (YYYY-MM-DD), Ortszeit am Abflughafen.
    flight_number  Airline-Code + Flugnummer, z. B. "LH400", "FR8786".
    from           IATA-Code des Abflughafens.
    to             IATA-Code des Zielflughafens.
    departure      Abflugzeit (HH:MM, 24h), Ortszeit am Abflughafen.
    arrival        Ankunftszeit (HH:MM, 24h), Ortszeit am Zielflughafen.
    arrival_date   Ankunftsdatum (YYYY-MM-DD), Ortszeit am Zielflughafen.
                   Weicht bei Nachtflügen und über die Datumsgrenze von
                   `date` ab (+1, +2 oder auch -1 Tag).
    duration_min   Flugdauer in Minuten, berechnet aus Abflug/Ankunft und
                   den Zeitzonen beider Flughäfen (inkl. Sommerzeit).

Abflug oder Ankunft:
    Es gibt kein eigenes Richtungsfeld. Ein Abflug hat den abgefragten
    IATA-Code in `from`, eine Ankunft hat ihn in `to`:

        abfluege  = [f for f in flights if f["from"] == "FRA"]
        ankuenfte = [f for f in flights if f["to"]   == "FRA"]

Eindeutigkeit:
    (date, flight_number, from, departure) ist pro Eintrag eindeutig.
    Codeshare-Flüge sind ausgeschlossen, jeder physische Flug erscheint
    nur einmal unter der Nummer der durchführenden Airline.


WIE DIE DATEN ENTSTEHEN / EINSCHRÄNKUNGEN
=========================================

- Kayak liefert pro Flug einen Wochentag, das erste Datum im Monat und einen
  Gültigkeitszeitraum. Das Script nimmt an, dass der Flug innerhalb dieses
  Zeitraums jede Woche an diesem Wochentag geht, und erzeugt daraus die
  einzelnen Tage. Unregelmäßige Flugpläne bildet Kayak über viele kurze
  Zeiträume ab (teils nur eine Woche). Ob innerhalb eines Zeitraums einzelne
  Wochen ausfallen, ist aus den Daten nicht erkennbar.
- Ankünfte werden über die Gegenrichtung der angeflogenen Ziele ermittelt.
  Ein Flughafen, von dem es nur Flüge zum abgefragten Flughafen gibt, aber
  keine zurück, fehlt daher.
- Ist ein Flughafen nicht in `airportsdata` enthalten, fällt `duration_min`
  auf Kayaks typische Routendauer zurück; `arrival_date` wird dann ohne
  Zeitzone geschätzt (Folgetag, wenn Ankunft < Abflug).
- Kayak fasst manche Flughäfen zu Gruppen zusammen (z. B. FRA + HHN). Die
  Flugdaten kommen trotzdem exakt pro Flughafen; unter FRA erscheinen also
  keine Hahn-Flüge.
- Züge sind ausgeschlossen.
- Genutzt werden die internen Kayak-APIs /i/api/directflights/v1/routes und
  /route/data. Ändert Kayak diese, muss das Script angepasst werden.
"""

import argparse
import calendar
import json
import re
import sys
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import airportsdata
import requests

BASE = "https://www.kayak.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0"
AIRPORTS = airportsdata.load("IATA")


def log(msg):
    print(msg, file=sys.stderr)


class KayakDirect:
    def __init__(self, delay=0.5):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.5"})
        self.token = None

    def _bootstrap(self):
        # /direct is served from an SEO cache without a session; /flights sets
        # the session cookies and embeds a matching formtoken (X-CSRF).
        r = self.session.get(f"{BASE}/flights", timeout=30)
        r.raise_for_status()
        m = re.search(r'"formtoken":"([^"]+)"', r.text)
        if not m:
            raise RuntimeError("formtoken not found on kayak.com/flights")
        self.token = m.group(1)

    def _post(self, path, params):
        if self.token is None:
            self._bootstrap()
        for attempt in range(2):
            time.sleep(self.delay)
            r = self.session.post(
                f"{BASE}{path}",
                params=params,
                data="{}",
                headers={
                    "X-CSRF": self.token,
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": f"{BASE}/direct",
                    "Origin": BASE,
                },
                timeout=30,
            )
            if r.status_code == 401 and attempt == 0:
                self._bootstrap()  # session or token expired
                continue
            r.raise_for_status()
            return r.json()

    def routes(self, origin, month=None):
        params = {"from": origin, "excludeTrains": "true", "excludeCodeShares": "true"}
        if month:
            params["tm"] = month
        return self._post("/i/api/directflights/v1/routes", params)

    def route_data(self, origin, dest, month):
        params = {"from": origin, "to": dest, "tm": month, "excludeCodeShares": "true"}
        return self._post("/i/api/directflights/v1/route/data", params)


def to_time(s):
    return datetime.strptime(s.strip().upper(), "%I:%M %p").time()


def resolve_year(month_day, anchor, before):
    """Attach a year to 'Oct 21' so it lies on the given side of anchor (closest match)."""
    d = datetime.strptime(f"{month_day} {anchor.year}", "%b %d %Y").date()
    if before and d > anchor:
        d = d.replace(year=d.year - 1)
    elif not before and d < anchor:
        d = d.replace(year=d.year + 1)
    return d


def tz(code):
    a = AIRPORTS.get(code)
    return ZoneInfo(a["tz"]) if a and a.get("tz") else None


def arrival_and_duration(dep_date, dep_t, arr_t, from_code, to_code, typical_min):
    """Return (arrival_date, duration_min) using the airports' time zones.

    The arrival day offset (-1..+2, e.g. overnight or across the date line) is
    the one whose duration is closest to Kayak's typical route duration.
    """
    tz_from, tz_to = tz(from_code), tz(to_code)
    if not (tz_from and tz_to):
        arr_date = dep_date + timedelta(days=1) if arr_t < dep_t else dep_date
        return arr_date, typical_min
    dep = datetime.combine(dep_date, dep_t, tz_from)
    best = None
    for offset in (-1, 0, 1, 2):
        arr_date = dep_date + timedelta(days=offset)
        minutes = round((datetime.combine(arr_date, arr_t, tz_to) - dep).total_seconds() / 60)
        if minutes <= 0:
            continue
        score = abs(minutes - typical_min) if typical_min else minutes
        if best is None or score < best[0]:
            best = (score, arr_date, minutes)
    return (best[1], best[2]) if best else (dep_date, typical_min)


def expand(raw, month, from_code, to_code, typical_min):
    """Turn one Kayak schedule entry into one record per flight date in `month`.

    Kayak returns {weekday: first date in month} plus a validity period; the
    flight operates weekly on that weekday within the period.
    """
    year, mon = map(int, month.split("-"))
    month_end = date(year, mon, calendar.monthrange(year, mon)[1])
    dep_t = to_time(raw["localizedDepartureTime"])
    arr_t = to_time(raw["localizedArrivalTime"])
    for first in raw["flights"].values():
        d = date.fromisoformat(first)
        valid_to = resolve_year(raw["localizedValidTo"], d, before=False)
        while d <= min(valid_to, month_end):
            arr_date, duration = arrival_and_duration(d, dep_t, arr_t, from_code, to_code, typical_min)
            yield {
                "date": d.isoformat(),
                "flight_number": f'{raw["airlineCode"]}{raw["flightNumber"]}',
                "from": from_code,
                "to": to_code,
                "departure": dep_t.strftime("%H:%M"),
                "arrival": arr_t.strftime("%H:%M"),
                "arrival_date": arr_date.isoformat(),
                "duration_min": duration,
            }
            d += timedelta(days=7)


def scrape(airport, months=None, direction="both", delay=0.5):
    k = KayakDirect(delay=delay)
    airport = airport.upper()
    first = k.routes(airport)
    if not first.get("fromAirport"):
        raise SystemExit(f"Unknown airport or no direct flights: {airport}")
    months = months or [m["urlMonth"] for m in first.get("travelMonths", [])]

    flights = {}
    for month in months:
        routes = k.routes(airport, month).get("routes", [])
        log(f"{month}: {len(routes)} routes")
        for r in routes:
            legs = []
            if direction in ("both", "departures"):
                legs.append((airport, r["code"]))
            if direction in ("both", "arrivals"):
                legs.append((r["code"], airport))
            for from_code, to_code in legs:
                try:
                    data = k.route_data(from_code, to_code, month)
                except requests.RequestException as e:
                    log(f"  {from_code}->{to_code}: failed ({e})")
                    continue
                for raw in data.get("flights", []):
                    for f in expand(raw, month, from_code, to_code, r.get("duration")):
                        flights[(f["date"], f["flight_number"], f["from"], f["departure"])] = f

    return sorted(flights.values(), key=lambda f: (f["date"], f["departure"], f["flight_number"]))


def main():
    p = argparse.ArgumentParser(description="Scrape kayak.com/direct departures and arrivals for an airport.")
    p.add_argument("airport", help="IATA airport code, e.g. FKB")
    p.add_argument("-m", "--months", nargs="+", metavar="YYYY-MM", help="months to scrape (default: all available)")
    p.add_argument("-d", "--direction", choices=["both", "departures", "arrivals"], default="both",
                   help="which flights to scrape (default: both)")
    p.add_argument("-o", "--output", help="output file (default: <IATA>_direct.json)")
    p.add_argument("--delay", type=float, default=0.5, help="seconds between requests (default: 0.5)")
    args = p.parse_args()

    flights = scrape(args.airport, args.months, args.direction, args.delay)
    out = args.output or f"{args.airport.upper()}_direct.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(flights, f, ensure_ascii=False, indent=2)
    log(f"Saved {len(flights)} flights -> {out}")


if __name__ == "__main__":
    main()
