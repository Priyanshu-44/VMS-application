"""Zone CRUD API -- app/api/zones.py."""

VALID_POLYGON = [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9]]


def test_create_zone_happy_path(client, camera_row):
    resp = client.post("/zones", json={
        "camera_id": camera_row["id"],
        "name": "Front Gate",
        "polygon": VALID_POLYGON,
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Front Gate"
    assert body["sensitivity"] == 0.5
    assert body["enabled"] is True
    assert body["polygon"] == VALID_POLYGON


def test_create_zone_requires_camera_to_exist(client):
    resp = client.post("/zones", json={
        "camera_id": 9999,
        "name": "Ghost Zone",
        "polygon": VALID_POLYGON,
    })
    assert resp.status_code == 404


def test_create_zone_requires_three_points(client, camera_row):
    resp = client.post("/zones", json={
        "camera_id": camera_row["id"],
        "name": "Line",
        "polygon": [[0.1, 0.1], [0.9, 0.9]],
    })
    assert resp.status_code == 422


def test_create_zone_rejects_out_of_range_sensitivity(client, camera_row):
    resp = client.post("/zones", json={
        "camera_id": camera_row["id"],
        "name": "Bad Sensitivity",
        "polygon": VALID_POLYGON,
        "sensitivity": 5.0,
    })
    assert resp.status_code == 422


def test_list_zones_for_camera(client, camera_row):
    client.post("/zones", json={"camera_id": camera_row["id"], "name": "A", "polygon": VALID_POLYGON})
    client.post("/zones", json={"camera_id": camera_row["id"], "name": "B", "polygon": VALID_POLYGON})

    resp = client.get(f"/cameras/{camera_row['id']}/zones")
    assert resp.status_code == 200
    names = {z["name"] for z in resp.json()}
    assert names == {"A", "B"}


def test_update_zone_partial_patch_preserves_other_fields(client, camera_row):
    created = client.post("/zones", json={
        "camera_id": camera_row["id"], "name": "Zone A", "polygon": VALID_POLYGON,
    }).json()

    resp = client.put(f"/zones/{created['id']}", json={"enabled": False})
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is False
    assert body["name"] == "Zone A"
    assert body["polygon"] == VALID_POLYGON


def test_update_missing_zone_404s(client):
    resp = client.put("/zones/9999", json={"enabled": False})
    assert resp.status_code == 404


def test_delete_zone_with_no_events(client, camera_row):
    created = client.post("/zones", json={
        "camera_id": camera_row["id"], "name": "Zone A", "polygon": VALID_POLYGON,
    }).json()

    resp = client.delete(f"/zones/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/cameras/{camera_row['id']}/zones").json() == []


def test_delete_missing_zone_404s(client):
    resp = client.delete("/zones/9999")
    assert resp.status_code == 404


def test_delete_zone_with_event_history_is_blocked(client, camera_row):
    from app.core.db import db_session

    created = client.post("/zones", json={
        "camera_id": camera_row["id"], "name": "Zone A", "polygon": VALID_POLYGON,
    }).json()

    with db_session() as conn:
        conn.execute(
            "INSERT INTO events (camera_id, zone_id, type, object_class, confidence, ts, acknowledged) "
            "VALUES (?, ?, 'intrusion', 'person', 0.9, CURRENT_TIMESTAMP, 0)",
            (camera_row["id"], created["id"]),
        )

    resp = client.delete(f"/zones/{created['id']}")
    assert resp.status_code == 409
    # The zone -- and the event history referencing it -- must survive the
    # blocked delete, per the documented "disable, don't delete" contract.
    assert len(client.get(f"/cameras/{camera_row['id']}/zones").json()) == 1
