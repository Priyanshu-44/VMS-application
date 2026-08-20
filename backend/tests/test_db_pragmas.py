"""Connection-level PRAGMAs -- app/core/db.py's get_connection(). This app
has genuinely concurrent SQLite writers (recorder + detection thread per
camera, plus API handlers), so WAL mode and a busy_timeout matter for real,
not just as a style preference.
"""
from app.core.db import get_connection


def test_wal_mode_enabled(test_db):
    conn = get_connection()
    try:
        mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        assert mode.lower() == "wal"
    finally:
        conn.close()


def test_busy_timeout_set(test_db):
    conn = get_connection()
    try:
        timeout_ms = conn.execute("PRAGMA busy_timeout;").fetchone()[0]
        assert timeout_ms == 5000
    finally:
        conn.close()


def test_foreign_keys_enforced(test_db):
    conn = get_connection()
    try:
        fk = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        assert fk == 1
    finally:
        conn.close()
