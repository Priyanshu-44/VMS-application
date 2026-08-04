"""Dashboard stats: the 4-tile overview (FR-10..13, Section 11)."""
from pathlib import Path

from fastapi import APIRouter

from app.core.config import THUMBNAILS_DIR
from app.core.db import db_session
from app.models.schemas import DashboardStats
from app.services.camera_manager import camera_manager

router = APIRouter(tags=["dashboard"])


def _human_bytes(n: int) -> str:
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


@router.get("/dashboard/stats", response_model=DashboardStats)
def dashboard_stats():
    states = camera_manager.all_states()
    cameras_online = sum(1 for s in states if s.online)

    with db_session() as conn:
        cameras_total = conn.execute("SELECT COUNT(*) AS c FROM cameras").fetchone()["c"]

        recent_rows = conn.execute(
            "SELECT * FROM events ORDER BY ts DESC LIMIT 8"
        ).fetchall()
        recent_detections = [
            {
                "id": r["id"], "camera_id": r["camera_id"], "zone_id": r["zone_id"],
                "type": r["type"], "object_class": r["object_class"], "confidence": r["confidence"],
                "ts": str(r["ts"]), "clip_path": r["clip_path"], "clip_offset": r["clip_offset"],
                "thumbnail_path": r["thumbnail_path"], "acknowledged": bool(r["acknowledged"]),
            }
            for r in recent_rows
        ]

        recordings_bytes = conn.execute(
            "SELECT COALESCE(SUM(size_bytes), 0) AS s FROM recordings WHERE size_bytes IS NOT NULL"
        ).fetchone()["s"]

        active_alerts = conn.execute(
            "SELECT COUNT(*) AS c FROM events WHERE acknowledged = 0"
        ).fetchone()["c"]

    # Include currently-open (not-yet-closed) segments' on-disk size too, so
    # the storage tile doesn't undercount while the demo is actively recording.
    open_segments_bytes = 0
    from app.services.recorder import recorder_manager
    for state in recorder_manager.states.values():
        if state.current_segment_path:
            p = Path(state.current_segment_path)
            if p.exists():
                open_segments_bytes += p.stat().st_size

    thumbnails_bytes = sum(f.stat().st_size for f in THUMBNAILS_DIR.glob("*.jpg"))
    storage_used = recordings_bytes + open_segments_bytes + thumbnails_bytes

    return DashboardStats(
        cameras_online=cameras_online,
        cameras_total=cameras_total,
        recent_detections=recent_detections,
        storage_used_bytes=storage_used,
        storage_used_readable=_human_bytes(storage_used),
        active_alerts=active_alerts,
    )
