"""
Analytics view (FR-19, Section 11): detections per hour/zone, and the
false-alarm-reduction headline number that's the whole pitch (Section 3/7).
"""
from fastapi import APIRouter

from app.core.db import db_session
from app.models.schemas import AnalyticsResponse
from app.services.pipeline_stats import pipeline_stats

router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics():
    with db_session() as conn:
        hour_rows = conn.execute(
            "SELECT strftime('%Y-%m-%d %H:00', ts) AS hour, COUNT(*) AS count "
            "FROM events GROUP BY hour ORDER BY hour"
        ).fetchall()
        detections_per_hour = [{"hour": r["hour"], "count": r["count"]} for r in hour_rows]

        zone_rows = conn.execute(
            "SELECT z.id AS zone_id, z.name AS zone_name, c.name AS camera_name, COUNT(e.id) AS count "
            "FROM zones z "
            "JOIN cameras c ON c.id = z.camera_id "
            "LEFT JOIN events e ON e.zone_id = z.id "
            "GROUP BY z.id ORDER BY count DESC"
        ).fetchall()
        detections_per_zone = [
            {"zone_id": r["zone_id"], "zone_name": r["zone_name"], "camera_name": r["camera_name"], "count": r["count"]}
            for r in zone_rows
        ]

    motion_ticks, confirmed_events = pipeline_stats.totals()
    suppressed = max(motion_ticks - confirmed_events, 0)
    reduction_pct = round((suppressed / motion_ticks) * 100, 1) if motion_ticks else 0.0

    return AnalyticsResponse(
        detections_per_hour=detections_per_hour,
        detections_per_zone=detections_per_zone,
        confirmed_vs_false={
            "motion_triggers": motion_ticks,
            "confirmed_events": confirmed_events,
            "suppressed": suppressed,
            "reduction_pct": reduction_pct,
        },
    )
