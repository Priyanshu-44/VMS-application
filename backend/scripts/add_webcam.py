"""
Registers your physical webcam as a live camera on an already-running backend,
so you can test the pipeline on real, non-repeating footage instead of the
looped sample clips.

The backend must already be running (uvicorn app.main:app) before you run
this -- it calls the running server's POST /cameras endpoint over HTTP so the
new camera gets its capture, recording, and detection threads started
immediately, the same way a camera present at boot does.

Usage (from backend/, with the backend already running on port 8000):
    .venv\\Scripts\\python.exe scripts\\add_webcam.py
    .venv\\Scripts\\python.exe scripts\\add_webcam.py --index 1 --name "My Laptop Cam"
"""
import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "http://localhost:8000"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=int, default=0, help="webcam device index (default 0, the first camera Windows finds)")
    parser.add_argument("--name", default="Webcam", help="display name for the camera")
    parser.add_argument("--location", default="Live webcam test", help="location label")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="backend base URL")
    args = parser.parse_args()

    payload = json.dumps({
        "name": args.name,
        "source": str(args.index),
        "location": args.location,
    }).encode()

    req = urllib.request.Request(
        f"{args.base_url}/cameras",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            camera = json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"Could not reach the backend at {args.base_url} -- is uvicorn running? ({e})")
        sys.exit(1)

    print(f"Registered camera {camera['id']}: {camera['name']} (source={camera['source']!r})")
    print()
    print("Next steps:")
    print(f"  - Live Grid should show it within a few seconds: http://localhost:5173/")
    print(f"  - Draw a detection zone for it at: http://localhost:5173/zones")
    print("    (without a zone, no events will fire for this camera -- the pipeline")
    print("     only evaluates enabled zones, same as every other camera.)")
    print(f"  - Watch it live: http://localhost:5173/playback/{camera['id']}")


if __name__ == "__main__":
    main()
