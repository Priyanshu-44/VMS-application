"""
Stage-1 sanity check: confirms YOLOv8n loads and detects objects on each
sample clip. Prints per-clip detection counts and classes found on a
handful of sampled frames. Not part of the runtime app — just a manual
verification step for the PRD Day-1 milestone.

Run from backend/:  .venv\\Scripts\\python.exe scripts\\verify_yolo.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2  # noqa: E402
from ultralytics import YOLO  # noqa: E402

from app.core.config import SAMPLE_CLIPS_DIR, YOLO_MODEL  # noqa: E402


def sample_frames(path: Path, n: int = 5):
    cap = cv2.VideoCapture(str(path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    step = max(total // n, 1)
    frames = []
    for i in range(n):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i * step)
        ok, frame = cap.read()
        if ok:
            frames.append(frame)
    cap.release()
    return frames


def main():
    print(f"Loading {YOLO_MODEL} ...")
    t0 = time.time()
    model = YOLO(YOLO_MODEL)
    print(f"Model loaded in {time.time() - t0:.1f}s\n")

    clips = sorted(SAMPLE_CLIPS_DIR.glob("*.mp4"))
    if not clips:
        print(f"No clips found in {SAMPLE_CLIPS_DIR}")
        return

    for clip in clips:
        frames = sample_frames(clip)
        if not frames:
            print(f"{clip.name}: could not read frames (codec issue?)")
            continue

        t0 = time.time()
        classes_seen = {}
        for frame in frames:
            results = model(frame, verbose=False)[0]
            for box in results.boxes:
                cls_name = model.names[int(box.cls[0])]
                conf = float(box.conf[0])
                classes_seen.setdefault(cls_name, []).append(round(conf, 2))
        elapsed = time.time() - t0

        print(f"=== {clip.name} ===")
        print(f"  frames sampled: {len(frames)}   inference time: {elapsed:.2f}s "
              f"({elapsed / len(frames):.3f}s/frame)")
        if classes_seen:
            for cls_name, confs in classes_seen.items():
                print(f"  {cls_name}: {len(confs)} detections, confidences {confs}")
        else:
            print("  no objects detected on sampled frames")
        print()


if __name__ == "__main__":
    main()
