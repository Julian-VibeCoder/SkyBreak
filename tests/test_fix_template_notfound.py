import os, sys
sys.path.insert(0, '.')
from skybreak.app import app

def test_index_returns_200():
    with app.test_client() as c:
        r = c.get('/')
        assert r.status_code == 200
