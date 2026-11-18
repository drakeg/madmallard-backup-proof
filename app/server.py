import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB = os.environ.get("APP_DB", "/data/app.db")

def initialize():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    with sqlite3.connect(DB) as db:
        db.execute("CREATE TABLE IF NOT EXISTS checks (id INTEGER PRIMARY KEY, label TEXT NOT NULL)")
        db.execute("INSERT OR IGNORE INTO checks VALUES (1, 'synthetic-customer-record')")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        with sqlite3.connect(DB) as db:
            count = db.execute("SELECT COUNT(*) FROM checks").fetchone()[0]
            record = db.execute("SELECT label FROM checks WHERE id=1").fetchone()
        if self.path == "/health":
            result = {"status": "ok"}
        elif self.path == "/api/count":
            result = {"count": count}
        elif self.path == "/api/record/1" and record:
            result = {"label": record[0]}
        else:
            self.send_error(404)
            return
        body = json.dumps(result).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    initialize()
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
