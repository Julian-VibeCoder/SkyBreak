import os, sys
os.environ.setdefault("FRONTEND_BUILD_DIR", "frontend/build")
os.environ.setdefault("DB_FILE", "/data/skybreak.db")
sys.path.insert(0, '.')
os.environ["FRONTEND_BUILD_DIR"] = "/projects/vacation/frontend/build"
os.environ["DB_FILE"] = "/data/skybreak.db"
from skybreak.app import app

def test_index_returns_200():
    # Set the build directory for test environment
    os.environ["FRONTEND_BUILD_DIR"] = os.environ.get("FRONTEND_BUILD_DIR", "frontend/build")
    with app.test_client() as c:
        r = c.get('/')
        assert r.status_code == 200
