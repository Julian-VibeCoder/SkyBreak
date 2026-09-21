import logging
import time
import requests
from datetime import datetime, timedelta
from skybreak.airport import get_setting

logger = logging.getLogger(__name__)
BASE_URL = "https://aerodatabox.p.rapidapi.com/flights/airports/iata"

def fetch_flights(airport_code, year_ahead=None):
    if year_ahead is None:
        try:
            year_ahead = int(get_setting("fetch_days_ahead"))
        except Exception:
            year_ahead = 2
        year_ahead = min(year_ahead, 7)  # first-week batch for initial load
    api_key = get_setting("api_key") or ""
    if not api_key:
        return []
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
    }

    # Fetch until 365-day data available; back off exponentially on rate limits
    wait_time = 30 * 60  # 30 minutes in seconds
    max_attempts = 10
    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        start_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
        end_str = (datetime.utcnow() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M")
        url = f"{BASE_URL}/{airport_code}/{start_str}/{end_str}"
        params = {"withLeg":"true","direction":"Both","withCodeshared":"true","withLocation":"false","withCancelled":"false","withCargo":"false","withPrivate":"false"}
        try:
            logger.info("RapidAPI aerodatabox access: airport=%s url=%s", airport_code, url)
            res = requests.get(url, headers=headers, params=params, timeout=10)
            if res.status_code == 429:
                logger.info("RapidAPI rate limit (429) for %s; waiting %d seconds before retry", airport_code, wait_time)
                time.sleep(wait_time)
                wait_time *= 2
                continue
            if res.status_code in (503,):
                res.raise_for_status()
            logger.info("RapidAPI aerodatabox response: status=%s airport=%s", res.status_code, airport_code)
            data = res.json()
            flights = []
            departures = data.get("departures", []) or []
            arrivals = data.get("arrivals", []) or []
            if isinstance(departures, list):
                flights.extend(departures)
            if isinstance(arrivals, list):
                flights.extend(arrivals)
            if not flights and isinstance(data, dict) and "data" in data:
                inner = data.get("data", [])
                flights = inner if isinstance(inner, list) else []
            if not flights and isinstance(data, list):
                flights = data
            return flights
        except Exception as e:
            logger.info("RapidAPI aerodatabox access failed: airport=%s error=%s", airport_code, e)
            logger.info("Waiting %d seconds before retry for %s", wait_time, airport_code)
            time.sleep(wait_time)
            wait_time *= 2
    logger.info("Exhausted fetch attempts for %s; returning empty", airport_code)
    return []
