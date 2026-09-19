# SkyBreak - Architecture Overview

## High-Level Design

### Core Components

1. **Web Frontend** (React/Vue.js)
   - Responsive UI for airport codes, trip planning, and monitoring
   - Dashboard for monitored trips and price charts
   - Configuration panel for days off, turnaround windows, and alerts

2. **Backend Service** (Node.js/Python)
   - API layer for flight data management
   - Local database (SQLite/PostgreSQL) for storing airports, flights, and trips
   - Integration with Google Flight Scraper

3. **Docker Compose** (Hosted Infrastructure)
   - Container orchestration for backend, frontend, and scraper
   - Separate services: API, Web App, Scraper, Database
   - Configurable via environment variables

4. **Google Flight Scraper**
   - Open-source scraper for flight prices (e.g., `google-flight-scraper`)
   - Extracts departure/arrival times and prices from airline websites

5. **Price History & Charts**
   - Daily price tracking for monitored trips
   - Visualization using Chart.js or similar

6. **Telegram Bot**
   - Notification system for price drops below threshold
   - Integration with Telegram Bot API

## Data Flow

1. User enters airport codes in the web UI
2. Backend loads flight data from the scraper (or cached)
3. System calculates feasible turn-arounds (start→destination→return)
4. Turn-arounds are stored with start/end times (excluding weekends)
5. Monitored trips are selected for price tracking
6. Every 24 hours, prices are fetched and compared against thresholds
7. Price history charts are generated
8. Telegram bot sends notifications when prices drop

## Technology Stack

- **Frontend:** React + Tailwind CSS (nice web UI)
- **Backend:** Node.js + Express
- **Database:** SQLite (lightweight, local)
- **Containerization:** Docker + docker-compose
- **Scraping:** Open-source Google Flight Scraper
- **Notifications:** Telegram Bot API
- **Charts:** Chart.js

## Key Requirements Mapping

| Requirement | Component |
|--------------|------------|
| No paid APIs | Use open-source scraper + local caching |
| Nice web frontend | React + Tailwind |
| Docker/hosted | docker-compose.yml |
| International airport codes | Input validation + geocoding |
| Load departures/arrivals | Scraper + local DB |
| Calculate turn-arounds | Algorithm in backend |
| Configurable days off | Business logic in backend |
| Select monitored trips | Filtering in UI |
| Google Flight Engine | Open-source scraper |
| Price checking every 24h | Cron-like scheduler |
| Price chart | Chart.js |
| Telegram notifications | Bot integration |
| Remove monitoring | API endpoint to disable |
| Remove airport | Cleanup in backend |

## Implementation Order (Incremental)

1. **Architecture Setup** - Docker compose, basic structure
2. **Airport Management** - CRUD for airports
3. **Flight Scraper Integration** - Fetch flight data
4. **Turnaround Calculation** - Logic for round trips
5. **Monitoring System** - Track trips, store data
6. **Price Tracking** - Daily price checks
7. **Visualization** - Charts for price history
8. **Telegram Notifications** - Alert system
9. **Configuration** - Days off, thresholds, etc.
10. **Frontend** - UI for all features

Each component can be developed and tested independently.