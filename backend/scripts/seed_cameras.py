"""
Seeds the 4 demo "cameras" (looped sample clips) so judges can reproduce
the demo without configuring anything. Idempotent — clears existing
cameras/zones first (fine for a prototype's seed script).

Run from backend/:  .venv\\Scripts\\python.exe scripts\\seed_cameras.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import SAMPLE_CLIPS_DIR  # noqa: E402
from app.core.db import db_session, init_db  # noqa: E402

CAMERAS = [
    {
        "name": "Perimeter Cam 1 - Rear Gate",
        "file": "thieves_intrusion.mp4",
        "location": "Rear perimeter gate",
    },
    {
        "name": "Perimeter Cam 2 - Tree Line",
        "file": "tree_wind_falsepositive.mp4",
        "location": "North tree line (false-positive demo)",
    },
    {
        "name": "Perimeter Cam 3 - Walkway",
        "file": "pedestrian_walking.mp4",
        "location": "Public walkway (zone-containment demo)",
    },
    {
        "name": "Perimeter Cam 4 - Access Road",
        "file": "cars_street.mp4",
        "location": "Vehicle access road",
    },
]


def main():
    init_db()
    with db_session() as conn:
        existing = conn.execute("SELECT COUNT(*) AS c FROM cameras").fetchone()["c"]
        if existing:
            print(f"{existing} camera(s) already present — skipping seed. "
                  "Delete data/db/vms.sqlite3 to reseed from scratch.")
            return

        for cam in CAMERAS:
            path = SAMPLE_CLIPS_DIR / cam["file"]
            if not path.exists():
                print(f"WARNING: {path} not found, skipping {cam['name']}")
                continue
            conn.execute(
                "INSERT INTO cameras (name, source, location, status) "
                "VALUES (?, ?, ?, 'online')",
                (cam["name"], str(path), cam["location"]),
            )
            print(f"Seeded camera: {cam['name']} -> {path}")


if __name__ == "__main__":
    main()
