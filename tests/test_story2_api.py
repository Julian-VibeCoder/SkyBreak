import pytest
import sqlite3
import os
from skybreak.app import app

DB_PATH = "/data/skybreak.db"

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def init_flights_table():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.execute("CREATE TABLE IF NOT EXISTS flights (id INTEGER PRIMARY KEY AUTOINCREMENT, airport_icao TEXT, destination_icao TEXT, flight_direction TEXT, departure_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("DELETE FROM flights")
    conn.execute("INSERT INTO flights (airport_icao, destination_icao, flight_direction, departure_time) VALUES (?, ?, ?, datetime('now', '+10 days'))", ("LHR", "JFK", "departure"))
    conn.execute("INSERT INTO flights (airport_icao, destination_icao, flight_direction, departure_time) VALUES (?, ?, ?, datetime('now', '+60 days'))", ("LHR", "CDG", "arrival"))
    conn.commit()
    conn.close()

def test_get_flights_200_and_json(client):
    resp = client.get("/api/flights")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["destination_icao"] == "JFK"
    assert data[0]["direction"] == "departure"

def test_get_flights_filter_airport(client):
    resp = client.get("/api/flights?airport=LHR")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert all(r["airport_icao"] == "LHR" for r in data)
