"""Shared pytest fixtures.

Every test gets its own throwaway SQLite file (via `test_db`) so tests never
touch `data/db/vms.sqlite3` -- the file the actual running demo uses -- and
never leak state between tests.
"""
import pytest


@pytest.fixture()
def test_db(tmp_path, monkeypatch):
    """Point app.core.db at a fresh SQLite file and create its schema."""
    from app.core import db as db_module

    db_path = tmp_path / "test_vms.sqlite3"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    db_module.init_db()
    return db_path


@pytest.fixture()
def client(test_db):
    """A FastAPI TestClient wired to the isolated test_db.

    Deliberately NOT used as a context manager (`with TestClient(app) as c`)
    -- that would run app.main's on_startup, which spins up a capture/
    recorder/detection thread per camera row already in the DB. The zone and
    event routes under test never touch those pipeline singletons, so
    skipping lifespan keeps these tests fast and side-effect free. The
    test_db fixture above already created the schema these routes need.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


@pytest.fixture()
def camera_row(test_db):
    """Insert a camera row directly via SQL, deliberately bypassing
    POST /cameras -- that endpoint's job (correctly, for the real app) is to
    also start real capture/recorder/detection background threads, which
    zone/event API tests have no need for. They just need a camera id to
    hang zones and events off of.
    """
    from app.core.db import db_session

    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO cameras (name, source, location, status) VALUES (?, ?, ?, 'online')",
            ("Test Cam", "0", "Test Location"),
        )
        row = conn.execute("SELECT * FROM cameras WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)
