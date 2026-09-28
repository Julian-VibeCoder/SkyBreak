# Plan: Favoriten-Preise gruppieren wie Possible Turnarounds

## Ziel
Die Tabelle unter `prices` (komponente `FavoriteTripPrices`) soll wie die `trips`-Seite (Possible Turnarounds) gruppiert werden — pro Reiseziel (`destination_airport` / `dest_city_country`). Zusätzlich günstigster Preis pro Gruppe und Aufteilung in mehrere Tabellen.

## Bezug
- `frontend/src/App.js`: `FavoriteTripPrices` (Zeile 13) = eine große Tabelle
- `frontend/src/App.js`: `turnarounds`-Gruppierung (Zeile 511–560) = Muster für Gruppierung nach Ziel
- Datenquelle: `/api/favorites` liefert `price_total`, `destination_airport`, `dest_city_country`, etc.

## Änderungen
1. **Gruppierung**: In `FavoriteTripPrices` Preise nach `destination_airport` (oder `dest_city_country`) gruppieren — analog zu `turnarounds.forEach(t => { const key = t.hinflug_ziel || t.destination || '-'; ... })`.
2. **Gruppen-Header**: Für jede Gruppe einen aufklappbaren Header mit Zielname + Code (wie `trip_`-Buttons bei Turnarounds).
3. **Günstigster Preis pro Gruppe**: Pro Gruppe `min(price_total)` berechnen und als Info-Zeile unter dem Header anzeigen (z.B. "Günstigster Trip: 234 €").
4. **Tabellen-Aufteilung**: Statt einer großen `<table>` für alle Zeilen: für jede Gruppe eigene `<table>` (innerhalb des aufklappbaren Bereichs) — analog zu Turnarounds.
5. **Sortierung**: Innerhalb jeder Gruppe nach `price_total` aufsteigend sortieren (oder nach Datum, je nach Bedarf); global oder pro Gruppe.

## Dateien
- `frontend/src/App.js` (nur Frontend, keine DB-Änderung nötig)

## Tests / Validierung
- `npm run build` bzw. `npm start` prüfen, ob Gruppierung korrekt rendert
- Visuell prüfen: mehrere Gruppen sichtbar, günstigster Preis pro Gruppe angezeigt, einzelne Tabellen pro Ziel

## Reihenfolge
1. Design-Review gegen `turnarounds`-Gruppierung (fertig)
2. Implementierung `FavoriteTripPrices` umbauen
3. Test/Build
4. Keine DB-Migration nötig (nur Frontend)
