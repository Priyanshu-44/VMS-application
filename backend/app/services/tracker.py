"""
Layer 4 of the false-alarm pipeline: dwell tracking so a momentary
detection doesn't escalate instantly (FR-18) and a cooldown so a lingering
intruder doesn't spam duplicate events (FR-17).

Tracks are keyed by (zone_id, class) rather than matched frame-to-frame by
centroid proximity. That's a deliberate simplification: CPU-only YOLO
inference runs far slower than the source video's fps, so consecutive
*analyzed* frames can be a second or more apart — an object can move well
outside any sane centroid-distance threshold between two analyzed frames,
which fragmented identity into a new "track" almost every tick and defeated
the cooldown entirely (verified during Stage 2: it produced ~50 events in
45s across 3 cameras — the exact spam problem this layer exists to
prevent). Keying by (zone, class) trades multi-object precision — two
people of the same class in the same zone are treated as one dwelling
subject — for reliably suppressing duplicate alerts, which is what the
prototype's demo and metrics (Section 3) actually need.
"""
import uuid
from dataclasses import dataclass

from app.core.config import EVENT_COOLDOWN_SECONDS

STALE_AFTER_SECONDS = 6.0    # drop a track if unseen for this long (resets dwell); generous
                              # margin above observed CPU-inference tick latency (~0.1-0.8s)


@dataclass
class Track:
    track_id: str
    zone_id: int
    cls_name: str
    centroid: tuple[float, float]
    first_seen: float
    last_seen: float
    last_event_ts: float | None = None
    escalated: bool = False   # has fired at least one event already

    def dwell_seconds(self) -> float:
        return self.last_seen - self.first_seen

    def in_cooldown(self, now: float) -> bool:
        if self.last_event_ts is None:
            return False
        return (now - self.last_event_ts) < EVENT_COOLDOWN_SECONDS

    def start_cooldown(self, now: float):
        self.last_event_ts = now
        self.escalated = True


class CameraTracker:
    """One instance per camera in the detection pipeline."""

    def __init__(self):
        self.tracks: dict[tuple[int, str], Track] = {}

    def update(self, zone_id: int, cls_name: str, centroid: tuple[float, float], now: float) -> Track:
        key = (zone_id, cls_name)
        t = self.tracks.get(key)

        if t is not None and (now - t.last_seen) <= STALE_AFTER_SECONDS:
            t.centroid = centroid
            t.last_seen = now
            return t

        t = Track(
            track_id=str(uuid.uuid4()),
            zone_id=zone_id,
            cls_name=cls_name,
            centroid=centroid,
            first_seen=now,
            last_seen=now,
        )
        self.tracks[key] = t
        return t

    def prune(self, now: float):
        stale = [k for k, t in self.tracks.items() if now - t.last_seen > STALE_AFTER_SECONDS]
        for k in stale:
            del self.tracks[k]
