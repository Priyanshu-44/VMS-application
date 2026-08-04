"""One-off DB init helper: `python scripts/init_db.py` (run from backend/)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.db import init_db, DB_PATH  # noqa: E402

if __name__ == "__main__":
    init_db()
    print(f"SQLite schema ready at {DB_PATH}")
