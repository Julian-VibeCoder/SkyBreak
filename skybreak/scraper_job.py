from apscheduler.schedulers.background import BackgroundScheduler
from skybreak.flight_scraper import fetch_flights
import sqlite3

def scrape_all_airports():
    conn = sqlite3.connect("test.db")
    rows = conn.execute("SELECT code FROM airports").fetchall()
    conn.close()
    for (code,) in rows:
        try:
            data = fetch_flights(code)
            # Speichern in flights mit destination_icao + direction
        except Exception:
            pass

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_all_airports, 'interval', minutes=30)
    scheduler.start()
