"""
Owns one background capture thread per registered camera. Sources can be:
  - an integer webcam device index (as a string, e.g. "0")
  - a file path to a looped sample clip (looped so the demo runs forever)

Each camera thread continuously grabs frames and stores the latest one
(as a numpy array + as pre-encoded JPEG bytes) so multiple consumers
(MJPEG stream endpoint, detection pipeline, recorder) can all read the
current frame without re-decoding or fighting over the VideoCapture object.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

from app.core.config import STREAM_JPEG_QUALITY


@dataclass
class CameraState:
    camera_id: int
    source: str
    name: str = ""
    is_file: bool = False
    online: bool = False
    latest_frame: Optional[np.ndarray] = None
    latest_jpeg: Optional[bytes] = None
    frame_ts: float = 0.0
    frame_index: int = 0          # increments per frame, used by recorder/detector
    fps: float = 25.0
    lock: threading.Lock = field(default_factory=threading.Lock)
    _stop: bool = False
    _thread: Optional[threading.Thread] = None

    def get_latest(self):
        with self.lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None

    def get_latest_jpeg(self):
        with self.lock:
            return self.latest_jpeg


class CameraManager:
    def __init__(self):
        self.cameras: dict[int, CameraState] = {}
        self._global_lock = threading.Lock()

    def register(self, camera_id: int, source: str, name: str = "") -> CameraState:
        with self._global_lock:
            if camera_id in self.cameras:
                return self.cameras[camera_id]

            is_file = not source.strip().lstrip("-").isdigit()
            state = CameraState(camera_id=camera_id, source=source, name=name, is_file=is_file)
            self.cameras[camera_id] = state

            t = threading.Thread(target=self._capture_loop, args=(state,), daemon=True)
            state._thread = t
            t.start()
            return state

    def unregister(self, camera_id: int):
        with self._global_lock:
            state = self.cameras.pop(camera_id, None)
            if state:
                state._stop = True

    def get(self, camera_id: int) -> Optional[CameraState]:
        return self.cameras.get(camera_id)

    def all_states(self):
        return list(self.cameras.values())

    def _capture_loop(self, state: CameraState):
        cap_source = state.source if state.is_file else int(state.source)
        cap = cv2.VideoCapture(cap_source)

        if not cap.isOpened():
            state.online = False
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        state.fps = fps if fps and fps > 1 else 25.0
        frame_interval = 1.0 / state.fps
        state.online = True

        while not state._stop:
            loop_start = time.time()
            ok, frame = cap.read()

            if not ok or frame is None:
                if state.is_file:
                    # loop sample clips forever for the demo
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    state.online = False
                    time.sleep(0.5)
                    cap.open(cap_source)
                    continue

            state.online = True
            ok_jpeg, jpeg = cv2.imencode(
                ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), STREAM_JPEG_QUALITY]
            )
            with state.lock:
                state.latest_frame = frame
                if ok_jpeg:
                    state.latest_jpeg = jpeg.tobytes()
                state.frame_ts = time.time()
                state.frame_index += 1

            elapsed = time.time() - loop_start
            sleep_for = frame_interval - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

        cap.release()


# Module-level singleton shared across the FastAPI app
camera_manager = CameraManager()
