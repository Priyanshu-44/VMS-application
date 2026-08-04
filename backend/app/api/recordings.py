"""Recording segment listing + playback (FR-3/FR-4, Section 11).

Playback strategy: each event/timeline click resolves to a specific segment
file; that file is served with HTTP Range support so the browser's native
<video> element handles seek/play/pause. `clip_offset` (seconds into the
segment) is used by the frontend to set `video.currentTime` after load —
simpler and more reliable for a prototype than server-side frame seeking.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.db import db_session
from app.models.schemas import RecordingOut

router = APIRouter(tags=["recordings"])


def _row_to_recording(row) -> RecordingOut:
    return RecordingOut(
        id=row["id"], camera_id=row["camera_id"], start_ts=str(row["start_ts"]),
        end_ts=str(row["end_ts"]) if row["end_ts"] else None,
        file_path=row["file_path"], size_bytes=row["size_bytes"],
    )


@router.get("/recordings/{camera_id}", response_model=list[RecordingOut])
def list_recordings(
    camera_id: int,
    start: Optional[str] = Query(None, description="ISO timestamp, inclusive"),
    end: Optional[str] = Query(None, description="ISO timestamp, inclusive"),
):
    clauses, params = ["camera_id = ?"], [camera_id]
    if start is not None:
        clauses.append("(end_ts IS NULL OR end_ts >= ?)")
        params.append(start)
    if end is not None:
        clauses.append("start_ts <= ?")
        params.append(end)
    where = " AND ".join(clauses)

    with db_session() as conn:
        rows = conn.execute(
            f"SELECT * FROM recordings WHERE {where} ORDER BY start_ts", params
        ).fetchall()
        return [_row_to_recording(r) for r in rows]


@router.get("/playback")
def playback(
    camera_id: Optional[int] = Query(None),
    ts: Optional[str] = Query(None, description="ISO timestamp to locate the containing segment"),
    event_id: Optional[int] = Query(None, description="Resolve directly from an event id instead of ts"),
):
    """Returns the video segment file containing the requested moment.
    Pass either `event_id` (uses that event's clip_path directly) or
    `camera_id` + `ts` (finds the segment whose [start_ts, end_ts] window
    contains ts)."""
    with db_session() as conn:
        if event_id is not None:
            row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
            if not row or not row["clip_path"]:
                raise HTTPException(404, "Event or its clip not found")
            return FileResponse(row["clip_path"], media_type="video/mp4")

        if ts is None or camera_id is None:
            raise HTTPException(422, "Provide either event_id, or both camera_id and ts")

        row = conn.execute(
            "SELECT * FROM recordings WHERE camera_id = ? AND start_ts <= ? "
            "AND (end_ts IS NULL OR end_ts >= ?) ORDER BY start_ts DESC LIMIT 1",
            (camera_id, ts, ts),
        ).fetchone()
        if not row:
            raise HTTPException(404, "No recording covers that timestamp")
        return FileResponse(row["file_path"], media_type="video/mp4")
