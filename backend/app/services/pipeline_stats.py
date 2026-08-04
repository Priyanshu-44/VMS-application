"""
In-memory counters powering the analytics view's headline number: how much
noise the false-alarm pipeline actually removes (PRD Section 3's target
metric and Section 7's demo moment). Intentionally in-memory, not a DB
table — this is a live-session stat that resets on restart, which is the
right behavior for a demo (you want "since this run started", not a
lifetime total muddied by earlier tuning runs).

Two counters:
  - motion_ticks: frames where MOG2 saw motion at all — this is what a
    naive raw-motion detector would have alerted on.
  - confirmed_events: detections that survived all four filter layers and
    became a real event.
The gap between them *is* the false-alarm reduction number.
"""
import threading
from collections import defaultdict


class PipelineStats:
    def __init__(self):
        self._lock = threading.Lock()
        self.motion_ticks: dict[int, int] = defaultdict(int)
        self.confirmed_events: dict[int, int] = defaultdict(int)

    def record_motion(self, camera_id: int):
        with self._lock:
            self.motion_ticks[camera_id] += 1

    def record_confirmed(self, camera_id: int):
        with self._lock:
            self.confirmed_events[camera_id] += 1

    def totals(self):
        with self._lock:
            motion = sum(self.motion_ticks.values())
            confirmed = sum(self.confirmed_events.values())
        return motion, confirmed


pipeline_stats = PipelineStats()
