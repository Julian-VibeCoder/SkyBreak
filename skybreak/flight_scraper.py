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
    params = {"withLeg":"true","direction":"Both","withCodeshared":"true","withLocation":"false"}
    try:
        logger.info("RapidAPI aerodatabox access: airport=%s url=%s", airport_code, BASE_URL)
        res = requests.get(BASE_URL, headers=headers, params=params, timeout=10)
        if res.status_code in (429, 503):
            res.raise_for_status()
        logger.info("RapidAPI aerodatabox response: status=%s airport=%s", res.status_code, airport_code)
        data = res.json()
        flights = data.get("data", []) if isinstance(data, dict) else data
        cutoff = datetime.utcnow() + timedelta(days=year_ahead)
        filtered = []
        for f in flights:
            dep = f.get("departure") or f.get("scheduled_departure")
            if dep:
                try:
                    dep_dt = datetime.fromisoformat(str(dep).replace("Z", "+00:00"))
                    if dep_dt <= cutoff:
                        filtered.append(f)
                except Exception:
                    filtered.append(f)
        return filtered
    except Exception as e:
        logger.info("RapidAPI aerodatabox access failed: airport=%s error=%s", airport_code, e)
        return []
