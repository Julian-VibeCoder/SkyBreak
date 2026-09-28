# Design: Aktualisierung Preis-Logik auf fast-flights 3.1.0

Ziel: Auf `fast-flights` v3 aktualisieren, alte v2-Abhängigkeiten entfernen, Consent-Cookie initialisieren.

## Änderungen
- `requirements.txt`: `fast-flights` ohne konkrete Version, ohne `[local]`
- `flight_prices.py`: DirectFetch / PlaywrightFetch / parse_offers / CONSENT_COOKIES
- Settings: Google-Consent-Cookie-Feld mit vorgegebenem Wert
- Dokumentation: Design und Plan aktualisiert
