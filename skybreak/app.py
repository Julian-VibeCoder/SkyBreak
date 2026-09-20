import sqlite3, os
from flask import Flask, send_from_directory
app = Flask(__name__, static_folder="frontend/dist", static_url_path="")
DB_PATH = "/data/skybreak.db"

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/airports", methods=["GET"])
def list_airports():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT code FROM airports").fetchall()
    conn.close()
    from flask import jsonify
    return jsonify([r[0] for r in rows])
