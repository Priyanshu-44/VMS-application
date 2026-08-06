"""Camera registry + live MJPEG streaming endpoints (FR-1, Section 11)."""
import json
import time

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse

from app.core.config import MJPEG_BOUNDARY
from app.core.db import db_session
from app.models.schemas import CameraCreate, CameraOut, ZoneOut
from app.services.camera_manager import camera_manager
from app.services.event_pipeline import pipeline_manager
from app.services.recorder import recorder_manager

router = APIRouter(prefix="/cameras", tags=["cameras"])


def _row_to_camera(row) -> CameraOut:
    return CameraOut(
        id=row["id"],
        name=row["name"],
        source=row["source"],
        location=row["location"],
        status=row["status"],
        created_at=str(row["created_at"]) if row["created_at"] else None,
    )


@router.get("", response_model=list[CameraOut])
def list_cameras():
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM cameras ORDER BY id").fetchall()
        return [_row_to_camera(r) for r in rows]


@router.post("", response_model=CameraOut, status_code=201)
def create_camera(cam: CameraCreate):
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO cameras (name, source, location, status) VALUES (?, ?, ?, 'online')",
            (cam.name, cam.source, cam.location),
        )
        row = conn.execute(
            "SELECT * FROM cameras WHERE id = ?", (cur.lastrowid,)
        ).fetchone()

    # A camera added after startup only gets its capture thread lazily, the
    # first time something requests its stream/snapshot (_ensure_capture_started
    # below). Recording and detection have no equivalent lazy path, so without
    # this a camera added through this endpoint would show up live but never
    # record or generate events. Wire it up the same way app.main's startup
    # event does for cameras that already existed at boot.
    camera_manager.register(row["id"], row["source"], row["name"])
    recorder_manager.start(row["id"])
    pipeline_manager.start(row["id"])

    return _row_to_camera(row)


@router.get("/{camera_id}", response_model=CameraOut)
def get_camera(camera_id: int):
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM cameras WHERE id = ?", (camera_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Camera not found")
        return _row_to_camera(row)


@router.get("/{camera_id}/zones", response_model=list[ZoneOut])
def list_zones_for_camera(camera_id: int):
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM zones WHERE camera_id = ? ORDER BY id", (camera_id,)).fetchall()
        return [
            ZoneOut(
                id=r["id"], camera_id=r["camera_id"], name=r["name"],
                polygon=json.loads(r["polygon"]), enabled=bool(r["enabled"]),
                sensitivity=r["sensitivity"], dwell_seconds=r["dwell_seconds"],
            )
            for r in rows
        ]


def _ensure_capture_started(camera_id: int):
    """Lazily start the capture thread for a camera the first time it's needed."""
    if camera_manager.get(camera_id) is not None:
        return
    with db_session() as conn:
        row = conn.execute("SELECT * FROM cameras WHERE id = ?", (camera_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Camera not found")
        camera_manager.register(camera_id, row["source"], row["name"])


def _mjpeg_generator(camera_id: int):
    state = camera_manager.get(camera_id)
    boundary = MJPEG_BOUNDARY
    last_index = -1
    while True:
        if state.frame_index != last_index:
            jpeg = state.get_latest_jpeg()
            if jpeg is not None:
                last_index = state.frame_index
                yield (
                    f"--{boundary}\r\n"
                    "Content-Type: image/jpeg\r\n"
                    f"Content-Length: {len(jpeg)}\r\n\r\n"
                ).encode() + jpeg + b"\r\n"
        time.sleep(1 / 30)


@router.get("/{camera_id}/stream")
def stream_camera(camera_id: int):
    """MJPEG live stream — consumed directly by an <img> tag on the frontend."""
    _ensure_capture_started(camera_id)
    return StreamingResponse(
        _mjpeg_generator(camera_id),
        media_type=f"multipart/x-mixed-replace; boundary={MJPEG_BOUNDARY}",
    )


@router.get("/{camera_id}/snapshot")
def camera_snapshot(camera_id: int):
    """A single still JPEG frame — used by the zone editor (FR-14: 'click on
    a paused frame to place polygon points'), which needs a stable frame to
    draw over rather than a live-updating stream."""
    _ensure_capture_started(camera_id)
    state = camera_manager.get(camera_id)
    jpeg = state.get_latest_jpeg() if state else None
    if jpeg is None:
        raise HTTPException(503, "No frame available yet")
    return Response(content=jpeg, media_type="image/jpeg")
