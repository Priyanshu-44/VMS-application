"""
Central configuration for the Envision backend.
Paths are resolved relative to the repo root so the app can be run from
anywhere (uvicorn app.main:app run from backend/, or packaged).
"""
import os
import sys
from pathlib import Path

# backend/app/core/config.py -> backend/app/core -> backend/app -> backend -> repo root
BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent

DATA_DIR = REPO_ROOT / "data"
DB_PATH = DATA_DIR / "db" / "vms.sqlite3"
SAMPLE_CLIPS_DIR = DATA_DIR / "sample_clips"
RECORDINGS_DIR = DATA_DIR / "recordings"
THUMBNAILS_DIR = DATA_DIR / "thumbnails"

for d in (DATA_DIR / "db", RECORDINGS_DIR, THUMBNAILS_DIR, SAMPLE_CLIPS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# OpenCV's bundled FFmpeg loads the OpenH264 codec DLL dynamically at runtime
# (not statically linked, for licensing reasons) — it must be discoverable on
# the DLL search path regardless of the process's cwd. Without it, VideoWriter
# silently falls back to 'mp4v', which browsers refuse to play in <video>
# (verified during Stage 3: MEDIA_ERR_SRC_NOT_SUPPORTED despite the HTTP layer
# serving 206 Partial Content fine).
VENDOR_DIR = BACKEND_DIR / "vendor"
if sys.platform == "win32" and VENDOR_DIR.exists():
    os.add_dll_directory(str(VENDOR_DIR))
    os.environ["PATH"] = str(VENDOR_DIR) + os.pathsep + os.environ.get("PATH", "")

# --- Detection pipeline defaults (overridable per-zone via DB) ---
YOLO_MODEL = "yolov8n.pt"          # nano model, CPU-friendly
RELEVANT_CLASSES = {"person", "car", "truck", "bus", "bicycle", "motorcycle"}
DEFAULT_CONFIDENCE_THRESHOLD = 0.5
DETECTION_INFERENCE_FLOOR = 0.2      # run YOLO at this floor; per-zone sensitivity filters on top
DEFAULT_DWELL_SECONDS = 2
# 8s was too short for looping demo clips: Track.dwell_seconds() is
# last_seen - first_seen, and a continuously-visible object's track never
# resets (STALE_AFTER_SECONDS=6s never elapses), so dwell grows unbounded
# for the whole session and the track stays permanently classified
# "loitering," re-firing every cooldown window indefinitely. Verified live:
# 8s cooldown produced 110 events on one camera in 17 minutes (96 of them
# duplicate "loitering" re-fires) -- exactly the spam PRD Section 7.4 says
# this layer must prevent. 30s keeps re-escalation for genuine loitering
# while keeping the demo's event stream to roughly one event per clip loop.
EVENT_COOLDOWN_SECONDS = 30          # suppress duplicate events per track
ANALYSIS_FPS = 12                    # throttle detection loop (NFR: keep UI responsive)
MOTION_MIN_AREA = 800                # px^2, ignore tiny MOG2 blobs (noise)

# --- Recording ---
SEGMENT_SECONDS = 30                 # length of each recorded segment

# --- Streaming ---
MJPEG_BOUNDARY = "frame"
STREAM_JPEG_QUALITY = 75

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
