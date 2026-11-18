"""Synthetic, isolated recovery drill. Never connects to production."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

def run(*args):
    subprocess.run(args, check=True, cwd=ROOT)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:18080")
    parser.add_argument("--max-bytes", type=int, default=10 * 1024**3)
    args = parser.parse_args()
    REPORTS.mkdir(exist_ok=True)
    started = time.monotonic()
    results = {"scope": "synthetic demo: one app, one SQLite database, one snapshot",
               "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "checks": [], "production_touched": False}
    with tempfile.TemporaryDirectory(prefix="backup-proof-") as tmp:
        tmp = Path(tmp)
        source = tmp / "source.db"
        with sqlite3.connect(source) as db:
            db.execute("CREATE TABLE checks (id INTEGER PRIMARY KEY, label TEXT NOT NULL)")
            db.execute("INSERT INTO checks VALUES (1, 'synthetic-customer-record')")
        # SQLite online backup API creates a transactionally consistent snapshot.
        snapshot = tmp / "snapshot.db"
        with sqlite3.connect(source) as src, sqlite3.connect(snapshot) as dst:
            src.backup(dst)
        if snapshot.stat().st_size > args.max_bytes:
            raise ValueError("Snapshot exceeds approved size cap")
        results["snapshot_bytes"] = snapshot.stat().st_size
        results["snapshot_sha256"] = sha256(snapshot)
        results["backup_age_seconds"] = 0
        restored = tmp / "restored.db"
        shutil.copy2(snapshot, restored)
        results["restored_sha256"] = sha256(restored)
        results["checks"].append({"name": "snapshot_integrity", "passed": sha256(snapshot) == sha256(restored)})
        with sqlite3.connect(restored) as db:
            row = db.execute("SELECT label FROM checks WHERE id=1").fetchone()
            count = db.execute("SELECT COUNT(*) FROM checks").fetchone()[0]
            integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        results["checks"] += [
            {"name": "database_integrity", "passed": integrity == "ok"},
            {"name": "record_retrieval", "passed": row == ("synthetic-customer-record",)},
            {"name": "record_count", "passed": count == 1},
        ]
        # Launch restored app only, with isolated DB and loopback binding.
        env = dict(os.environ, APP_DB=str(restored))
        proc = subprocess.Popen(["python3", "app/server.py"], cwd=ROOT, env=dict(env, PYTHONUNBUFFERED="1"),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            # Server uses 8080 inside this synthetic demo; no production address.
            for attempt in range(30):
                try:
                    with urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=1) as resp:
                        results["checks"].append({"name": "application_starts", "passed": json.load(resp)["status"] == "ok"})
                    break
                except Exception:
                    time.sleep(.2)
            else:
                results["checks"].append({"name": "application_starts", "passed": False})
        finally:
            proc.terminate()
            proc.wait(timeout=5)
    results["recovery_elapsed_seconds"] = round(time.monotonic() - started, 2)
    results["passed"] = all(x["passed"] for x in results["checks"])
    (REPORTS / "latest.json").write_text(json.dumps(results, indent=2) + "\n")
    lines = ["# Synthetic recovery evidence", "", f"Result: **{'PASS' if results['passed'] else 'FAIL'}**",
             "", f"Recovery elapsed: {results['recovery_elapsed_seconds']} seconds",
             f"Snapshot bytes: {results['snapshot_bytes']}", f"SHA-256: `{results['snapshot_sha256']}`",
             "", "## Checks"]
    lines += [f"- {'PASS' if c['passed'] else 'FAIL'}: {c['name']}" for c in results["checks"]]
    lines += ["", "## Recovery runbook", "1. Obtain authorized, consistent snapshot.",
              "2. Verify checksum and size; restore only into an isolated environment.",
              "3. Start restored application and run agreed acceptance checks.",
              "4. Record evidence, dependencies, elapsed time and limitations.",
              "", "Synthetic evidence only; not a customer recovery certification."]
    (REPORTS / "latest.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(results, indent=2))
    if not results["passed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
