import requests
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(5), wait=wait_fixed(30*60))
def fetch_flights(airport_code):
    url = f"https://api.example.com/flights/{airport_code}"
    res = requests.get(url, timeout=10)
    res.raise_for_status()
    return res.json()
