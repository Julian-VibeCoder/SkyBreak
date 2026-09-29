# Feature: Datum-Filter und Gruppen-Aktionen für Favoriten

## Beschreibung
Implementiert drei wesentliche Verbesserungen auf der Preis-Seite:
1. Datumsfilterung (Start-/Enddatum) für Favoriten-Preise
2. "Delete All" Button für jede Favoriten-Gruppe
3. "Favorite All" Button für jede Gruppe in der Trips-Ansicht

## User Stories
- **Als Benutzer möchte ich Favoriten nach Datum filtern können**, um bestimmte Zeiträume anzuzeigen und leere Gruppen auszublenden.
- **Als Benutzer möchte ich alle gefilterten Favoriten einer Gruppe mit einem Klick löschen können**, um Massenoperationen durchzuführen.
- **Als Benutzer möchte ich alle Trips einer Zielflughafen-Gruppe als Favorit markieren können**, um den Workflow zu beschleunigen.

## Akzeptanzkriterien
1. Auf der Preis-Seite gibt es zwei Datum-Eingabefelder (von/bis) oberhalb der Favoriten-Gruppen
2. Wenn ein Datumsfilter gesetzt ist, werden nur Favoriten innerhalb dieses Bereichs angezeigt
3. Gruppen, die durch den Filter leer werden, werden komplett ausgeblendet
4. Jede erweiterbare Gruppe hat einen "Delete all in group" Button, der alle angezeigten Favoriten der Gruppe löscht
5. Beim Löschen wird eine Bestätigung angezeigt
6. In der Trips-Ansicht hat jede erweiterbare Gruppe einen "Favorite all" Button
7. Beim Klicken auf "Favorite all" werden alle Trips der Gruppe als Favorit markiert
8. Bei allen Aktionen wird die UI nach Erfolg aktualisiert

## Technische Details
### Preis-Seite Änderungen:
- Hinzufügen von `filterStart` und `filterEnd` State-Variablen
- Eingabe-Felder für Datumsfilter oberhalb der Gruppen-Liste
- Filter-Logik in der Gruppen-Rendering-Schleife
- "Delete all in group" Button mit Bestätigungs-Dialog
- Gruppen werden ausgeblendet, wenn sie nach Filter leer sind

### Trips-Seite Änderungen:
- Hinzufügen von "Favorite all" Button zu jeder Gruppe
- Beim Klicken werden alle Trips der Gruppe als Favorit gespeichert
- Optimistische UI-Updates nach erfolgreichem Speichern

## Abhängigkeiten
- Keine neuen Backend-Endpoints erforderlich (verwendet bestehende `/api/favorites` Endpunkte)
- Nur Frontend-Änderungen in `frontend/src/App.js`

## Tests
- Manuelle Prüfung der Datumsfilter-Funktion
- Prüfung der "Delete all" Funktionalität mit Bestätigung
- Prüfung der "Favorite all" Funktionalität in Trips-Ansicht
- Sicherstellen, dass leere Gruppen ausgeblendet werden
- Überprüfen, dass die UI korrekt nach Aktionen aktualisiert wird