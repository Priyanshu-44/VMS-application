"""Camera registry + live MJPEG streaming endpoints (FR-1, Section 11)."""
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.config import MJPEG_BOUNDARY
from app.core.db import db_session
from app.models.schemas import CameraCreate, CameraOut
from app.services.camera_manager import camera_manager

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
