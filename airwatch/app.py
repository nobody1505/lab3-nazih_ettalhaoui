"""AirWatch: air-quality readings (PM2.5) stored in PostgreSQL.

Environment variables:
  DATABASE_URL     postgresql://USER:PASSWORD@HOST:PORT/DBNAME
  CONNECT_RETRIES  attempts to reach the database at startup (default 10)
  RETRY_DELAY      seconds between two attempts (default 2)
"""
import os
import sys
import time

import psycopg
from flask import Flask, jsonify, request

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://airwatch:airwatch@localhost:5432/airwatch")
CONNECT_RETRIES = int(os.environ.get("CONNECT_RETRIES", "10"))
RETRY_DELAY = float(os.environ.get("RETRY_DELAY", "2"))

app = Flask(__name__)


def connect():
    return psycopg.connect(DATABASE_URL, connect_timeout=3)


def init_db():
    """Create the table. Retry while the database is not reachable yet."""
    for attempt in range(1, CONNECT_RETRIES + 1):
        try:
            with connect() as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS readings ("
                    " id SERIAL PRIMARY KEY,"
                    " sensor TEXT NOT NULL,"
                    " pm25 REAL NOT NULL,"
                    " created_at TIMESTAMPTZ NOT NULL DEFAULT now())")
            print("AirWatch: database ready", flush=True)
            return
        except psycopg.OperationalError as exc:
            print(f"AirWatch: database not reachable "
                  f"(attempt {attempt}/{CONNECT_RETRIES}): {exc}", flush=True)
            time.sleep(RETRY_DELAY)
    print("AirWatch: giving up, cannot reach the database", flush=True)
    sys.exit(1)


@app.post("/readings")
def add_reading():
    data = request.get_json(silent=True) or {}
    sensor, pm25 = data.get("sensor"), data.get("pm25")
    if not isinstance(sensor, str) or not isinstance(pm25, (int, float)):
        return {"error": 'expected JSON like {"sensor": "amphi-a", "pm25": 12.5}'}, 400
    with connect() as conn:
        row = conn.execute(
            "INSERT INTO readings (sensor, pm25) VALUES (%s, %s) RETURNING id",
            (sensor, pm25)).fetchone()
    return {"id": row[0], "sensor": sensor, "pm25": pm25}, 201


@app.get("/readings")
def list_readings():
    limit = min(int(request.args.get("limit", 20)), 200)
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, sensor, pm25, created_at FROM readings "
            "ORDER BY id DESC LIMIT %s", (limit,)).fetchall()
    return jsonify([{"id": r[0], "sensor": r[1], "pm25": r[2],
                     "created_at": r[3].isoformat()} for r in rows])


@app.get("/stats")
def stats():
    with connect() as conn:
        rows = conn.execute(
            "SELECT sensor, count(*), round(avg(pm25)::numeric, 1) "
            "FROM readings GROUP BY sensor ORDER BY sensor").fetchall()
    return jsonify([{"sensor": r[0], "readings": r[1], "avg_pm25": float(r[2])}
                    for r in rows])


@app.get("/health")
def health():
    try:
        with connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "database": "reachable"}
    except psycopg.OperationalError:
        return {"status": "error", "database": "unreachable"}, 503


init_db()
