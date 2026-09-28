# Plan: fast-flights v3 Update

1. Design-Review gegen user-stories.md + architecture.md
2. `requirements.txt` aktualisieren (nur `fast-flights`, alte Abhängigkeiten raus)
3. `flight_prices.py` auf v3-API umstellen (DirectFetch, PlaywrightFetch, parse_offers, CONSENT_COOKIES)
4. Settings-Route `/api/settings` + Frontend erweitern für `google_consent_cookie`
5. Initialisierung mit `CAESHAgBEhJnd3NfMjAyMzA4MTAtMF9SQzIaAmRlIAEaBgiAo_CmBg`
6. Tests ausführen, Bild bauen, Container neu starten
