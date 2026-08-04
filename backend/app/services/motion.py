"""
Layer 1 of the false-alarm pipeline (PRD Section 7): a cheap MOG2 background
subtraction gate. YOLO only runs on a frame when something is actually
moving, saving CPU and — just as importantly for the pitch — proving the
"we don't even look unless something moved" story.
"""
import cv2
import numpy as np

from app.core.config import MOTION_MIN_AREA


class MotionGate:
    """One instance per camera — MOG2 keeps a running background model that
    must not be shared across sources."""

    def __init__(self):
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=300, varThreshold=25, detectShadows=True
        )
        self._warmup_frames = 0

    def detect(self, frame: np.ndarray) -> bool:
        """Returns True if meaningful motion is present in this frame."""
        fg_mask = self.bg_subtractor.apply(frame)
        # Shadows are labeled 127 by MOG2 — drop them, keep only strong FG (255)
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

        self._warmup_frames += 1
        if self._warmup_frames < 15:
            # MOG2 needs a few frames to build an initial background model;
            # treat the warmup window as "no motion" to avoid a false
            # motion spike on the very first frames of a clip/loop.
            return False

        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return any(cv2.contourArea(c) >= MOTION_MIN_AREA for c in contours)
