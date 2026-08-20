"""
SQLite access layer. Schema matches PRD Section 10 verbatim (cameras, zones,
events, recordings). Uses the stdlib sqlite3 module — no ORM, kept simple
and transparent for a prototype/judged demo.
"""
import sqlite3
from contextlib import contextmanager

from app.core.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS cameras (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    source        TEXT NOT NULL,          -- device index, file path, or URL
    location      TEXT,
    status        TEXT DEFAULT 'online',  -- online | offline
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS zones (
    id            INTEGER PRIMARY KEY,
    camera_id     INTEGER REFERENCES cameras(id),
    name          TEXT NOT NULL,
    polygon       TEXT NOT NULL,          -- JSON: [[x,y],[x,y],...] normalized 0-1
    enabled       INTEGER DEFAULT 1,
    sensitivity   REAL DEFAULT 0.5,       -- confidence threshold override
    dwell_seconds INTEGER DEFAULT 2
);

CREATE TABLE IF NOT EXISTS events (
    id             INTEGER PRIMARY KEY,
    camera_id      INTEGER REFERENCES cameras(id),
    zone_id        INTEGER REFERENCES zones(id),
    type           TEXT NOT NULL,         -- intrusion | motion | loitering
    object_class   TEXT,                  -- person | car | truck ...
    confidence     REAL,
    ts             TIMESTAMP NOT NULL,
    clip_path      TEXT,                  -- recorded segment
    clip_offset    REAL,                  -- seconds into segment
    thumbnail_path TEXT,
    acknowledged   INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS recordings (
    id          INTEGER PRIMARY KEY,
    camera_id   INTEGER REFERENCES cameras(id),
    start_ts    TIMESTAMP NOT NULL,
    end_ts      TIMESTAMP,
    file_path   TEXT NOT NULL,
    size_bytes  INTEGER
);

CREATE INDEX IF NOT EXISTS idx_events_camera_ts ON events(camera_id, ts);
CREATE INDEX IF NOT EXISTS idx_recordings_camera_start ON recordings(camera_id, start_ts);
CREATE INDEX IF NOT EXISTS idx_zones_camera ON zones(camera_id);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    # This app genuinely has concurrent writers -- the recorder thread and
    # detection thread per camera, plus API request handlers, each open
    # their own connection via db_session(). SQLite's default rollback-
    # journal mode serializes writers and can raise "database is locked"
    # under that contention. WAL lets readers and a writer proceed
    # concurrently; busy_timeout makes a writer that does contend retry for
    # up to 5s instead of failing immediately.
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn


@contextmanager
def db_session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist. Safe to call on every startup."""
    with db_session() as conn:
        conn.executescript(SCHEMA)
