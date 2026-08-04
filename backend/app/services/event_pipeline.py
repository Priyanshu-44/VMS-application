"""
The orchestrator: wires together the four-layer false-alarm pipeline
described in PRD Section 7 / pseudocode in Section 12.

  MOG2 motion gate -> YOLOv8 classify -> per-zone confidence + containment
  -> centroid tracker (dwell) -> cooldown -> create_event -> push over WS

One thread per camera, throttled to ANALYSIS_FPS so the UI and recording
stay responsive even on CPU-only inference (NFR, Section 14).
"""
from __future__ import annotations

import json
import threading
import time
import uuid

import cv2

from app.core.config import ANALYSIS_FPS, THUMBNAILS_DIR
from app.core.db import db_session
from app.core.geometry import point_in_polygon
from app.services.camera_manager import camera_manager
from app.services.detector import Detection, Detector
from app.services.motion import MotionGate
from app.services.pipeline_stats import pipeline_stats
from app.services.recorder import recorder_manager
from app.services.tracker import CameraTracker
from app.services.ws_manager import ws_manager

ZONE_CACHE_REFRESH_SECONDS = 2.0
LOITER_MULTIPLIER = 2.5   # dwell beyond zone.dwell_seconds * this => "loitering" instead of "intrusion"
THUMB_PADDING = 0.15      # extra context around the bbox, as a fraction of bbox size


class DetectionPipeline:
    def __init__(self, camera_id: int):
        self.camera_id = camera_id
        self.motion_gate = MotionGate()
        self.tracker = CameraTracker()
        self._stop = False
        self._zones_cache: list[dict] = []
        self._zones_cache_ts = 0.0

    def _load_zones(self, now: float) -> list[dict]:
        if now - self._zones_cache_ts < ZONE_CACHE_REFRESH_SECONDS:
            return self._zones_cache
        with db_session() as conn:
            rows = conn.execute(
                "SELECT * FROM zones WHERE camera_id = ? AND enabled = 1", (self.camera_id,)
            ).fetchall()
            self._zones_cache = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "polygon": json.loads(r["polygon"]),
                    "sensitivity": r["sensitivity"],
                    "dwell_seconds": r["dwell_seconds"],
                }
                for r in rows
            ]
        self._zones_cache_ts = now
        return self._zones_cache

    def _save_thumbnail(self, frame, det: Detection) -> str:
        x1, y1, x2, y2 = det.bbox
        bw, bh = x2 - x1, y2 - y1
        h, w = frame.shape[:2]
        x1 = max(0, int(x1 - bw * THUMB_PADDING))
        y1 = max(0, int(y1 - bh * THUMB_PADDING))
        x2 = min(w, int(x2 + bw * THUMB_PADDING))
        y2 = min(h, int(y2 + bh * THUMB_PADDING))
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            crop = frame

        filename = f"{uuid.uuid4().hex}.jpg"
        path = THUMBNAILS_DIR / filename
        cv2.imwrite(str(path), crop, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        return str(path)

    def _create_event(self, zone: dict, det: Detection, dwell_seconds: float, frame, now: float):
        event_type = "loitering" if dwell_seconds >= zone["dwell_seconds"] * LOITER_MULTIPLIER else "intrusion"
        thumbnail_path = self._save_thumbnail(frame, det)

        rec_state = recorder_manager.get(self.camera_id)
        clip_path = rec_state.current_segment_path if rec_state else None
        clip_offset = (now - rec_state.current_segment_start_ts) if rec_state else None

        with db_session() as conn:
            cur = conn.execute(
                "INSERT INTO events "
                "(camera_id, zone_id, type, object_class, confidence, ts, clip_path, clip_offset, thumbnail_path, acknowledged) "
                "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, 0)",
                (
                    self.camera_id, zone["id"], event_type, det.cls_name, det.confidence,
                    clip_path, clip_offset, thumbnail_path,
                ),
            )
            row = conn.execute("SELECT * FROM events WHERE id = ?", (cur.lastrowid,)).fetchone()

        event_dict = dict(row)
        ws_manager.broadcast_threadsafe({"kind": "event", "data": event_dict})
        return event_dict

    def _tick(self):
        state = camera_manager.get(self.camera_id)
        if state is None or state.latest_frame is None:
            return

        frame = state.get_latest()
        if frame is None:
            return

        if not self.motion_gate.detect(frame):
            return
        pipeline_stats.record_motion(self.camera_id)

        now = time.time()
        zones = self._load_zones(now)
        if not zones:
            return

        detections = Detector.instance().detect(frame)

        for det in detections:
            for zone in zones:
                if det.confidence < zone["sensitivity"]:
                    continue
                x, y = det.centroid_norm
                if not point_in_polygon(x, y, zone["polygon"]):
                    continue

                track = self.tracker.update(zone["id"], det.cls_name, det.centroid_norm, now)
                dwell = track.dwell_seconds()
                if dwell >= zone["dwell_seconds"] and not track.in_cooldown(now):
                    self._create_event(zone, det, dwell, frame, now)
                    pipeline_stats.record_confirmed(self.camera_id)
                    track.start_cooldown(now)

        self.tracker.prune(now)

    def run(self):
        interval = 1.0 / ANALYSIS_FPS
        while not self._stop:
            loop_start = time.time()
            try:
                self._tick()
            except Exception as e:
                # Detection must never take the process down — recording and
                # streaming keep running even if a single tick errors.
                print(f"[detection] camera {self.camera_id} tick error: {e}")
            elapsed = time.time() - loop_start
            sleep_for = interval - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)


class PipelineManager:
    def __init__(self):
        self.pipelines: dict[int, DetectionPipeline] = {}

    def start(self, camera_id: int):
        if camera_id in self.pipelines:
            return
        pipeline = DetectionPipeline(camera_id)
        self.pipelines[camera_id] = pipeline
        t = threading.Thread(target=pipeline.run, daemon=True)
        t.start()


pipeline_manager = PipelineManager()
