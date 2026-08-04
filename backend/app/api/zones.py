"""Detection zone CRUD (FR-14, Section 11)."""
import json

from fastapi import APIRouter, HTTPException

from app.core.db import db_session
from app.models.schemas import ZoneCreate, ZoneOut, ZoneUpdate

router = APIRouter(prefix="/zones", tags=["zones"])


def _row_to_zone(row) -> ZoneOut:
    return ZoneOut(
        id=row["id"],
        camera_id=row["camera_id"],
        name=row["name"],
        polygon=json.loads(row["polygon"]),
        enabled=bool(row["enabled"]),
        sensitivity=row["sensitivity"],
        dwell_seconds=row["dwell_seconds"],
    )


@router.post("", response_model=ZoneOut, status_code=201)
def create_zone(zone: ZoneCreate):
    if len(zone.polygon) < 3:
        raise HTTPException(422, "A zone polygon needs at least 3 points")
    with db_session() as conn:
        cam = conn.execute("SELECT id FROM cameras WHERE id = ?", (zone.camera_id,)).fetchone()
        if not cam:
            raise HTTPException(404, "Camera not found")
        cur = conn.execute(
            "INSERT INTO zones (camera_id, name, polygon, enabled, sensitivity, dwell_seconds) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                zone.camera_id, zone.name, json.dumps(zone.polygon),
                int(zone.enabled), zone.sensitivity, zone.dwell_seconds,
            ),
        )
        row = conn.execute("SELECT * FROM zones WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _row_to_zone(row)


@router.put("/{zone_id}", response_model=ZoneOut)
def update_zone(zone_id: int, patch: ZoneUpdate):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM zones WHERE id = ?", (zone_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Zone not found")

        fields = patch.model_dump(exclude_unset=True)
        if "polygon" in fields:
            if len(fields["polygon"]) < 3:
                raise HTTPException(422, "A zone polygon needs at least 3 points")
            fields["polygon"] = json.dumps(fields["polygon"])
        if "enabled" in fields:
            fields["enabled"] = int(fields["enabled"])

        if fields:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            conn.execute(f"UPDATE zones SET {set_clause} WHERE id = ?", (*fields.values(), zone_id))

        row = conn.execute("SELECT * FROM zones WHERE id = ?", (zone_id,)).fetchone()
        return _row_to_zone(row)


@router.delete("/{zone_id}", status_code=204)
def delete_zone(zone_id: int):
    with db_session() as conn:
        row = conn.execute("SELECT id FROM zones WHERE id = ?", (zone_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Zone not found")
        conn.execute("DELETE FROM zones WHERE id = ?", (zone_id,))
