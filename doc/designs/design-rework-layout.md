# Design Rework — Layout-Optimierung (mobile + desktop)

## Ziel
- Platzverschwendung reduzieren (Padding 36px → 24px, Sidebar 260→220)
- Mobile-Ansicht (iPhone 15) funktional sicherstellen
- Layout-Struktur korrigieren: Flex-Row statt kaputter Header/Main-Sibling

## Analyse (Playwright iPhone 15 / Desktop 1280)
- Layout.jsx: `<header>` als Direct-Child ohne Flex-Row; Main-Overflow nicht kontrolliert
- App.js: Tabelle breiter als 320px, Buttons zu klein für Touch
- Whitespace durch große Sektionen und übergroße Padding-Werte

## Änderungen
- Layout.jsx: flexDirection row; aside (Sidebar) fixed 220px; main padding 24px/20px
- App.js: Table font 12, button padding 6px 10px, Sections padding 24px, maxWidth 100%

## Design-Review-Checkliste
- [x] User Stories abgedeckt (Übersicht, Preise, Settings sichtbar)
- [x] Architektur konsistent (React/Flask/SQLite unverändert)
- [x] CI/Workflow: npm build ok, kein Dockerfile-Change nötig
- [x] Dokumentation: dieses Design + Plan + Screenshot-Analyse
