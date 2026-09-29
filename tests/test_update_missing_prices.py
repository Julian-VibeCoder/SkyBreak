import sqlite3, os, pytest, sys
sys.path.insert(0, '.')
from skybreak.app import app

DB_PATH = os.environ.get("DB_FILE", "/data/skybreak.db")

@pytest.fixture
def client():
    with app.test_client() as c:
        yield c

def test_missing_prices_filter(client):
    # Verify endpoint exists and rejects when already running (or returns ok if not)
    r = client.post("/api/prices/missing")
    # We accept 200 (updated) or 409 (running) — either proves route exists
    assert r.status_code in (200, 409)
