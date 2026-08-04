"""
Layer 2 of the false-alarm pipeline: YOLOv8 object classification, run only
on frames that already passed the motion gate. Returns detections with
normalized centroids so they can be tested against zone polygons directly.
"""
from dataclasses import dataclass

import numpy as np
from ultralytics import YOLO

from app.core.config import DETECTION_INFERENCE_FLOOR, RELEVANT_CLASSES, YOLO_MODEL


@dataclass
class Detection:
    cls_name: str
    confidence: float
    bbox: tuple[float, float, float, float]   # x1,y1,x2,y2 in pixels
    centroid_norm: tuple[float, float]         # (x,y) normalized 0-1


class Detector:
    """Loaded once and shared across all camera detection threads — the
    ultralytics model object is safe to call concurrently for inference
    (each call is stateless), avoiding N separate model loads."""

    _instance: "Detector | None" = None

    def __init__(self):
        self.model = YOLO(YOLO_MODEL)
        # Warm the model once so the first real inference isn't the slow one.
        self.model(np.zeros((320, 320, 3), dtype=np.uint8), verbose=False)

    @classmethod
    def instance(cls) -> "Detector":
        if cls._instance is None:
            cls._instance = Detector()
        return cls._instance

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """Runs inference at a low confidence floor so every zone (which may
        each define its own, higher `sensitivity` threshold) has candidates
        to filter from. The per-zone confidence gate is applied by the
        caller (layer 2b of the pipeline), not here."""
        h, w = frame.shape[:2]
        results = self.model(frame, verbose=False, conf=DETECTION_INFERENCE_FLOOR)[0]

        out = []
        for box in results.boxes:
            cls_name = self.model.names[int(box.cls[0])]
            if cls_name not in RELEVANT_CLASSES:
                continue
            conf = float(box.conf[0])
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            out.append(
                Detection(
                    cls_name=cls_name,
                    confidence=conf,
                    bbox=(x1, y1, x2, y2),
                    centroid_norm=(cx / w, cy / h),
                )
            )
        return out
