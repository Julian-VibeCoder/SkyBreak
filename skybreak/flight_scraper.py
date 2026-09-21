import logging
import requests
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from skybreak.airport import get_setting

logger = logging.getLogger(__name__)
BASE_URL = "https://aerodatabox.p.rapidapi.com/flights/airports/iata"

@retry(
    stop=stop_after_attempt(5),
    wait=wait_fixed(30*60),
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    reraise=True
)
def fetch_flights(airport_code, year_ahead=None, start_time_str=None, end_time_str=None):
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
    if start_time_str is None:
        start_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
    else:
        start_str = start_time_str
    if end_time_str is None:
        end_str = (datetime.utcnow() + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M")
    else:
        end_str = end_time_str
    url = f"{BASE_URL}/{airport_code}/{start_str}/{end_str}"
    params = {"withLeg":"true","direction":"Both","withCodeshared":"true","withLocation":"false","withCancelled":"false","withCargo":"false","withPrivate":"false"}
    try:
        logger.info("RapidAPI aerodatabox access: airport=%s url=%s", airport_code, url)
        res = requests.get(url, headers=headers, params=params, timeout=10)
        if res.status_code in (400, 401, 403, 404, 429, 503):
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
        # Include all flights returned by endpoint within window
        return flights
    except Exception as e:
        logger.info("RapidAPI aerodatabox access failed: airport=%s error=%s", airport_code, e)
        return []
