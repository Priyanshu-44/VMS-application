"""Event query + acknowledge API -- app/api/events.py."""


def _insert_event(camera_id, event_type="intrusion", object_class="person", acknowledged=0, ts=None):
    from app.core.db import db_session

    with db_session() as conn:
        if ts is None:
            cur = conn.execute(
                "INSERT INTO events (camera_id, zone_id, type, object_class, confidence, ts, acknowledged) "
                "VALUES (?, NULL, ?, ?, 0.85, CURRENT_TIMESTAMP, ?)",
                (camera_id, event_type, object_class, acknowledged),
            )
        else:
            # CURRENT_TIMESTAMP only has 1-second resolution, so tests that
            # need a deterministic ordering across several inserts pass an
            # explicit ts instead of relying on real-time gaps.
            cur = conn.execute(
                "INSERT INTO events (camera_id, zone_id, type, object_class, confidence, ts, acknowledged) "
                "VALUES (?, NULL, ?, ?, 0.85, ?, ?)",
                (camera_id, event_type, object_class, ts, acknowledged),
            )
        return cur.lastrowid


def test_list_events_empty(client, camera_row):
    resp = client.get("/events")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_events_filters_by_camera_and_type(client, camera_row):
    _insert_event(camera_row["id"], event_type="intrusion")
    _insert_event(camera_row["id"], event_type="loitering")

    resp = client.get("/events", params={"camera_id": camera_row["id"], "type": "intrusion"})
    body = resp.json()
    assert len(body) == 1
    assert body[0]["type"] == "intrusion"


def test_list_events_most_recent_first(client, camera_row):
    first_id = _insert_event(camera_row["id"], ts="2026-01-01 10:00:00")
    second_id = _insert_event(camera_row["id"], ts="2026-01-01 10:00:05")

    body = client.get("/events").json()
    assert [e["id"] for e in body] == [second_id, first_id]


def test_list_events_respects_limit(client, camera_row):
    for _ in range(5):
        _insert_event(camera_row["id"])

    body = client.get("/events", params={"limit": 2}).json()
    assert len(body) == 2


def test_get_event_404_when_missing(client):
    resp = client.get("/events/9999")
    assert resp.status_code == 404


def test_acknowledge_event_persists(client, camera_row):
    event_id = _insert_event(camera_row["id"])

    resp = client.post(f"/events/{event_id}/acknowledge")
    assert resp.status_code == 200
    assert resp.json()["acknowledged"] is True

    refetched = client.get(f"/events/{event_id}").json()
    assert refetched["acknowledged"] is True


def test_acknowledge_missing_event_404s(client):
    resp = client.post("/events/9999/acknowledge")
    assert resp.status_code == 404


def test_thumbnail_404_when_not_set(client, camera_row):
    event_id = _insert_event(camera_row["id"])
    resp = client.get(f"/events/{event_id}/thumbnail")
    assert resp.status_code == 404
