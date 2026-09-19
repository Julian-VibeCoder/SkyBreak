# SkyBreak - Architecture Overview (Updated)

## Key Changes
- **Destinations Filterable** — UI filters turn-around list by destination
- **Next Year Only** — Scraper fetches only upcoming 12 months of flight data
- **Test-Driven** — All new features start with failing test specs
- **Data Sources** — Arrivals/departures from real free REST API (batch mode); prices from Google Flight Scraper only

## API Strategy
- **Free REST API** (e.g., AviationStack, FlightAware free tier, or OpenFlights) — batched requests to handle rate limits
- **Google Flight Scraper** — price extraction only (not schedules)

## Implementation (TDD)
1. Write failing test for filter
2. Implement filter logic
3. Write failing test for 1-year fetch
4. Implement time window restriction
5. Write integration test for API batch
6. Implement batch fetching