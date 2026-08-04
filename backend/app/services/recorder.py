"""
Continuous segment recording (FR-2). Runs one thread per camera, writing
whatever the camera_manager's capture thread has most recently produced.
Recording must never stop even if the detection pipeline lags (NFR,
Section 14) — this thread only depends on camera_manager, never on the
detector, so a slow YOLO pass can't stall the recording.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path

import cv2

from app.core.config import RECORDINGS_DIR, SEGMENT_SECONDS
from app.core.db import db_session
from app.services.camera_manager import CameraState, camera_manager

RECORD_FPS_CAP = 15.0   # cap written fps to keep segment files small for the demo


@dataclass
class RecorderState:
    camera_id: int
    current_recording_id: int | None = None
    current_segment_path: str | None = None
    current_segment_start_ts: float = 0.0
    _stop: bool = False


class RecorderManager:
    def __init__(self):
        self.states: dict[int, RecorderState] = {}
        self._lock = threading.Lock()

    def start(self, camera_id: int):
        with self._lock:
            if camera_id in self.states:
                return
            state = RecorderState(camera_id=camera_id)
            self.states[camera_id] = state
            t = threading.Thread(target=self._record_loop, args=(camera_id, state), daemon=True)
            t.start()

    def get(self, camera_id: int) -> RecorderState | None:
        return self.states.get(camera_id)

    def _camera_dir(self, camera_id: int) -> Path:
        d = RECORDINGS_DIR / f"camera_{camera_id}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _open_new_segment(self, camera_id: int, state: RecorderState, frame_size, fps):
        ts = time.time()
        filename = f"{int(ts)}.mp4"
        path = self._camera_dir(camera_id) / filename
        # H.264 (avc1), not the default mp4v — browsers won't play mp4v in
        # <video> (see app/core/config.py's VENDOR_DIR comment for why this
        # needs the bundled OpenH264 DLL to actually encode, not just open).
        fourcc = cv2.VideoWriter_fourcc(*"avc1")
        writer = cv2.VideoWriter(str(path), fourcc, fps, frame_size)
        if not writer.isOpened():
            raise RuntimeError(
                f"VideoWriter failed to open for camera {camera_id} with H.264 (avc1). "
                "Is vendor/openh264-2.5.0-win64.dll present?"
            )

        with db_session() as conn:
            cur = conn.execute(
                "INSERT INTO recordings (camera_id, start_ts, file_path) VALUES (?, datetime(?, 'unixepoch'), ?)",
                (camera_id, ts, str(path)),
            )
            state.current_recording_id = cur.lastrowid

        state.current_segment_path = str(path)
        state.current_segment_start_ts = ts
        return writer

    def _close_segment(self, state: RecorderState, path: str):
        try:
            size = Path(path).stat().st_size
        except OSError:
            size = 0
        with db_session() as conn:
            conn.execute(
                "UPDATE recordings SET end_ts = CURRENT_TIMESTAMP, size_bytes = ? WHERE id = ?",
                (size, state.current_recording_id),
            )

    def _record_loop(self, camera_id: int, state: RecorderState):
        cam: CameraState | None = None
        while cam is None or cam.latest_frame is None:
            cam = camera_manager.get(camera_id)
            time.sleep(0.2)

        fps = min(cam.fps, RECORD_FPS_CAP)
        frame = cam.get_latest()
        h, w = frame.shape[:2]
        writer = self._open_new_segment(camera_id, state, (w, h), fps)

        frame_interval = 1.0 / fps
        last_written_index = -1

        while not state._stop:
            loop_start = time.time()

            if time.time() - state.current_segment_start_ts >= SEGMENT_SECONDS:
                writer.release()
                self._close_segment(state, state.current_segment_path)
                writer = self._open_new_segment(camera_id, state, (w, h), fps)

            if cam.frame_index != last_written_index and cam.latest_frame is not None:
                f = cam.get_latest()
                if f is not None and f.shape[1::-1] == (w, h):
                    writer.write(f)
                    last_written_index = cam.frame_index

            elapsed = time.time() - loop_start
            sleep_for = frame_interval - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

        writer.release()
        self._close_segment(state, state.current_segment_path)


recorder_manager = RecorderManager()
