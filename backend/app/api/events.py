"""Event query + acknowledge endpoints (FR-9, FR-20, Section 11)."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.db import db_session
from app.models.schemas import EventOut

router = APIRouter(prefix="/events", tags=["events"])


def _row_to_event(row) -> EventOut:
    return EventOut(
        id=row["id"],
        camera_id=row["camera_id"],
        zone_id=row["zone_id"],
        type=row["type"],
        object_class=row["object_class"],
        confidence=row["confidence"],
        ts=str(row["ts"]),
        clip_path=row["clip_path"],
        clip_offset=row["clip_offset"],
        thumbnail_path=row["thumbnail_path"],
        acknowledged=bool(row["acknowledged"]),
    )


@router.get("", response_model=list[EventOut])
def list_events(
    camera_id: Optional[int] = None,
    type: Optional[str] = None,
    start: Optional[str] = Query(None, description="ISO timestamp, inclusive"),
    end: Optional[str] = Query(None, description="ISO timestamp, inclusive"),
    limit: int = Query(200, le=1000),
):
    clauses, params = [], []
    if camera_id is not None:
        clauses.append("camera_id = ?")
        params.append(camera_id)
    if type is not None:
        clauses.append("type = ?")
        params.append(type)
    if start is not None:
        clauses.append("ts >= ?")
        params.append(start)
    if end is not None:
        clauses.append("ts <= ?")
        params.append(end)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT * FROM events {where} ORDER BY ts DESC LIMIT ?"
    params.append(limit)

    with db_session() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [_row_to_event(r) for r in rows]


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Event not found")
        return _row_to_event(row)


@router.post("/{event_id}/acknowledge", response_model=EventOut)
def acknowledge_event(event_id: int):
    with db_session() as conn:
        row = conn.execute("SELECT id FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Event not found")
        conn.execute("UPDATE events SET acknowledged = 1 WHERE id = ?", (event_id,))
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        return _row_to_event(row)
