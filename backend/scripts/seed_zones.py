"""
Seeds one pre-drawn detection zone per demo camera (Section 16 deliverable:
"pre-drawn zones so judges can reproduce the demo"). Idempotent per camera —
skips a camera that already has a zone.

Run from backend/:  .venv\\Scripts\\python.exe scripts\\seed_zones.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.db import db_session, init_db  # noqa: E402

# Polygons in normalized [0,1] coordinates, resolution-independent.
ZONES_BY_CAMERA_NAME = {
    "Perimeter Cam 1 - Rear Gate": {
        "name": "Rear gate perimeter",
        "polygon": [[0.05, 0.05], [0.95, 0.05], [0.95, 0.95], [0.05, 0.95]],
        # Low-light CCTV footage -> YOLO confidence runs low (~0.3-0.45), see Stage 1 verification.
        "sensitivity": 0.3,
        "dwell_seconds": 1,
    },
    "Perimeter Cam 2 - Tree Line": {
        "name": "Tree line (false-positive control)",
        "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
        "sensitivity": 0.5,
        "dwell_seconds": 2,
    },
    "Perimeter Cam 3 - Walkway": {
        # Right two-thirds of frame = "restricted area"; the walkway itself
        # (left third) stays outside the zone -> demonstrates containment.
        "name": "Restricted area beyond walkway",
        "polygon": [[0.35, 0.0], [1.0, 0.0], [1.0, 1.0], [0.35, 1.0]],
        "sensitivity": 0.5,
        "dwell_seconds": 1,
    },
    "Perimeter Cam 4 - Access Road": {
        "name": "Access road",
        "polygon": [[0.0, 0.35], [1.0, 0.35], [1.0, 1.0], [0.0, 1.0]],
        "sensitivity": 0.35,
        "dwell_seconds": 1,
    },
}


def main():
    init_db()
    with db_session() as conn:
        for cam_name, zone in ZONES_BY_CAMERA_NAME.items():
            cam = conn.execute("SELECT id FROM cameras WHERE name = ?", (cam_name,)).fetchone()
            if not cam:
                print(f"WARNING: camera '{cam_name}' not found (run seed_cameras.py first)")
                continue

            existing = conn.execute(
                "SELECT COUNT(*) AS c FROM zones WHERE camera_id = ?", (cam["id"],)
            ).fetchone()["c"]
            if existing:
                print(f"{cam_name}: zone already present, skipping")
                continue

            conn.execute(
                "INSERT INTO zones (camera_id, name, polygon, enabled, sensitivity, dwell_seconds) "
                "VALUES (?, ?, ?, 1, ?, ?)",
                (cam["id"], zone["name"], json.dumps(zone["polygon"]), zone["sensitivity"], zone["dwell_seconds"]),
            )
            print(f"Seeded zone for {cam_name}: {zone['name']}")


if __name__ == "__main__":
    main()
