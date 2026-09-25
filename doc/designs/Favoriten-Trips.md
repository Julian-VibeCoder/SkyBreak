# Favoriten-Trips Design

## Ziel
Einzelne Trips aus der Trip-Ergebnisliste können als Favorit gespeichert werden. Auf Seite /prices werden sie schön dargestellt und können gelöscht werden.

## Datenbank
Tabelle `favorite_trips`:
- id (PK)
- trip_date (TEXT)
- start_time (TEXT)
- destination_airport (TEXT)
- outbound_flight_number (TEXT)
- return_flight_number (TEXT)
- created_at

Migration via db_migrate.py (version erhöhen).

## API
- GET /api/favorites -> Liste der Favoriten
- POST /api/favorites -> Speichern (Body: trip-Daten)
- DELETE /api/favorites/<id> -> Löschen
- GET /api/trips -> ergänzt `is_favorite` für jedes Ergebnis (Vergleich mit DB)

## Frontend
- In Trip-Ergebnisliste: Favoriten-Button (Stern/Herz) + Statusanzeige (favorisiert ja/nein)
- Auf /prices: Favoriten-Block mit Details (Datum, Uhrzeit, Zielflughafen, Flugnummern) + Löschen-Button

## Regel (kein Live-Patch)
Alle Änderungen im Quellcode, dann docker build + redeploy.
