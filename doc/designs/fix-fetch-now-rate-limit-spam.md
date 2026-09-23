# Fix: fetch-now button spams API on 429 rate limit

Goal: Prevent unbounded retries / spam when external API returns 429.
Approach: Cap retries in scraper loop + add coalesce guard on endpoint.
