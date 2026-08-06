# Smart VMS — AI Intrusion Detection & False-Alarm Suppression

**Team Byte Breakers** · National Institute of Technology Delhi
Built for **A-1 Launchpad 2026 — Round 2** (Software Development / AI-ML track), Case Study: Smart Video Management System.

> A-1's perimeter security operators drown in false alerts triggered by wind, animals, and moving foliage. This VMS unifies live monitoring and recorded playback in one interface, and is **smart enough to know a swaying tree is not an intruder** — verified in this repo's own test runs at an **85.9% reduction in false triggers** vs. raw motion detection (85 motion triggers → 12 confirmed events, `85` counted live during Stage 4 verification of this build; your own run will produce its own numbers as the demo clips loop).

**Demo video:** _[link — add before submission]_
**Live docs (when running locally):** http://localhost:8000/docs

---

## Contents

- [What this is](#what-this-is)
- [The differentiator — four-layer false-alarm pipeline](#the-differentiator--four-layer-false-alarm-pipeline)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Getting started](#getting-started)
- [Project structure](#project-structure)
- [Database schema](#database-schema)
- [API reference](#api-reference)
- [What's built vs. roadmap](#whats-built-vs-roadmap)
- [Acknowledgements](#acknowledgements)

## What this is

A functional prototype — not a slide-deck concept. Four camera feeds (webcam-optional; the demo runs entirely on looped sample clips for a reliable, repeatable demo) are ingested, recorded to disk in 30-second segments, and analyzed frame-by-frame by an AI pipeline. Detected intrusions land on an interactive timeline in real time via WebSocket, and one click on a marker seeks straight to that moment's footage.

| Screen | What it does |
|---|---|
| **Live Grid** (`/`) | Multi-camera MJPEG grid, online/offline status, real-time alert flash |
| **Playback + Timeline** (`/playback/:cameraId`) | The demo centerpiece — canvas timeline with colored event markers, hover-to-preview, click-to-seek, native video seek/play/pause, live↔playback toggle |
| **Events** (`/events`) | Filterable event table, acknowledge, click-through to the exact playback moment |
| **Dashboard** (`/dashboard`) | 4 tiles: camera status, active alerts, storage usage, recent detections feed |
| **Analytics** (`/analytics`) | The false-alarm-reduction number, detections/hour, detections/zone |
| **Zone Editor** (`/zones`) | Draw a polygon on a paused frame; tune sensitivity/dwell time per zone |

## The differentiator — four-layer false-alarm pipeline

A raw motion detector fires on everything that moves. This pipeline layers four filters so only a real intrusion reaches the operator:

1. **Motion pre-filter (OpenCV MOG2)** — cheap background subtraction gates the expensive model; YOLO only runs on frames where something actually moved.
2. **Object-class filter (YOLOv8)** — the moving thing must classify as `person`, `car`, `truck`, `bus`, `bicycle`, or `motorcycle`. Leaves, shadows, and camera noise are discarded before a zone is ever checked.
3. **Zone containment** — the detection's centroid must fall inside an operator-drawn, enabled polygon (point-in-polygon test, normalized coordinates).
4. **Dwell + cooldown** — a momentary detection doesn't escalate instantly (configurable dwell seconds); once an event fires, a cooldown window (default 30s) suppresses duplicate alerts for the same zone+class.

The included sample cameras are chosen to demonstrate this directly: **Perimeter Cam 2 (Tree Line)** runs a wind/foliage clip and — verified, not assumed — produces **zero events** across the whole pipeline, while the other three cameras (intrusion, pedestrian, vehicle clips) fire real, correctly-classified events.

## Architecture

```
Sample clips (looped, 4 "cameras")
        │
        ▼
FastAPI backend — ingest, MJPEG stream out, H.264 segment recording
        │
        ▼
AI detection engine — MOG2 motion gate → YOLOv8 classify → zone test → dwell/cooldown
        │
        ▼
SQLite (cameras, zones, events, recordings) + clips & thumbnails on disk
        │
        ▼
React frontend — live grid · timeline (markers + seek) · dashboard · zone editor · analytics
        ▲
        └── WebSocket for real-time event push
```

One background thread per camera per concern (capture, recording, detection) — recording never stalls even if detection lags, per the prototype's non-functional requirements.

## Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Backend | Python 3.13 + FastAPI | Async, auto OpenAPI docs at `/docs` |
| Video I/O | OpenCV (`opencv-python`) | Frame capture, MJPEG streaming, segment recording |
| Object detection | Ultralytics YOLOv8n | CPU-friendly; ~0.13–0.8s/frame on a laptop CPU depending on scene |
| Motion pre-filter | OpenCV MOG2 | Cheap gate before the model runs |
| Video codec | H.264 via Cisco's OpenH264 | See [Acknowledgements](#acknowledgements) — required because OpenCV's default `mp4v` fallback isn't playable in browsers |
| Database | SQLite | Zero-config, ships as sample data |
| Real-time | FastAPI WebSocket (`/ws/events`) | Push new events to the UI instantly |
| Frontend | React 19 + Vite + Tailwind CSS v4 | Dark theme, canvas-rendered timeline |
| Charts | Recharts | Analytics view |

## Getting started

Tested on Windows with Python 3.13 and Node 22. No GPU, no external services, no system `ffmpeg` binary required — everything needed ships in this repo or installs via `pip`/`npm`.

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts\init_db.py
.venv\Scripts\python.exe scripts\seed_cameras.py
.venv\Scripts\python.exe scripts\seed_zones.py
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

The first run also auto-downloads YOLOv8n weights (~6MB, from Ultralytics' official GitHub releases) via the `ultralytics` package.

API docs: **http://localhost:8000/docs**

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. `frontend/.env` already points at `http://localhost:8000` — no edits needed for local use.

### 3. (Optional) Verify the pipeline directly

```bash
cd backend
.venv\Scripts\python.exe scripts\verify_yolo.py   # confirms YOLOv8 detects the right classes on each sample clip
.venv\Scripts\python.exe scripts\test_ws.py       # confirms /ws/events pushes live events
```

### macOS/Linux note

`backend/vendor/openh264-2.5.0-win64.dll` is Windows-only. On macOS/Linux, either install a system `ffmpeg` with libx264 (OpenCV will use it automatically) or grab the matching OpenH264 binary for your platform from [Cisco's releases](https://github.com/cisco/openh264/releases) and point `os.add_dll_directory`-equivalent loading at it (macOS uses `.dylib`/`DYLD_LIBRARY_PATH`, Linux uses `.so`/`LD_LIBRARY_PATH` — `app/core/config.py` only wires the Windows path today).

## Project structure

```
backend/
  app/
    api/        # cameras, zones, events, recordings, dashboard, analytics, ws
    core/       # config, db (SQLite schema + connections), geometry (point-in-polygon)
    services/   # camera_manager, recorder, motion, detector, tracker,
                # event_pipeline (the orchestrator), ws_manager, pipeline_stats
    models/     # Pydantic schemas
  scripts/      # init_db, seed_cameras, seed_zones, verify_yolo, test_ws
  vendor/       # openh264 DLL (see Acknowledgements)
frontend/
  src/
    pages/      # LiveGrid, PlaybackPage, EventsPage, DashboardPage, AnalyticsPage, ZonesPage
    components/ # Sidebar, Layout, CameraTile, Timeline (the centerpiece)
    lib/        # api.js (REST client), time.js
    hooks/      # useEventsSocket (WS with auto-reconnect)
data/
  sample_clips/ # 4 demo clips (see Acknowledgements)
  recordings/   # generated at runtime, per-camera segments
  thumbnails/   # generated at runtime, event crops
  db/           # vms.sqlite3
prd.md          # the source-of-truth requirements doc this build follows
```

## Database schema

SQLite, matching the design locked on Day 1 (see [`backend/app/core/db.py`](backend/app/core/db.py) for the authoritative version):

```sql
CREATE TABLE cameras (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, source TEXT NOT NULL,
    location TEXT, status TEXT DEFAULT 'online', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE zones (
    id INTEGER PRIMARY KEY, camera_id INTEGER REFERENCES cameras(id), name TEXT NOT NULL,
    polygon TEXT NOT NULL,        -- JSON [[x,y],...] normalized 0-1
    enabled INTEGER DEFAULT 1, sensitivity REAL DEFAULT 0.5, dwell_seconds INTEGER DEFAULT 2
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY, camera_id INTEGER REFERENCES cameras(id), zone_id INTEGER REFERENCES zones(id),
    type TEXT NOT NULL,           -- intrusion | motion | loitering
    object_class TEXT, confidence REAL, ts TIMESTAMP NOT NULL,
    clip_path TEXT, clip_offset REAL, thumbnail_path TEXT, acknowledged INTEGER DEFAULT 0
);

CREATE TABLE recordings (
    id INTEGER PRIMARY KEY, camera_id INTEGER REFERENCES cameras(id),
    start_ts TIMESTAMP NOT NULL, end_ts TIMESTAMP, file_path TEXT NOT NULL, size_bytes INTEGER
);
```

## API reference

Full interactive docs at `/docs`. Summary:

| Method | Endpoint | Purpose |
|---|---|---|
| GET/POST | `/cameras` | List / register cameras |
| GET | `/cameras/{id}/stream` | MJPEG live stream |
| GET | `/cameras/{id}/snapshot` | Single still JPEG (zone editor) |
| GET | `/cameras/{id}/zones` | Zones for a camera |
| POST/PUT/DELETE | `/zones`, `/zones/{id}` | Create / update / remove a zone |
| GET | `/events` | List events (filter by camera, type, time range) |
| GET | `/events/{id}`, `/events/{id}/thumbnail` | Event detail / thumbnail image |
| POST | `/events/{id}/acknowledge` | Dismiss an alert |
| GET | `/recordings/{camera_id}` | Segments in a time window |
| GET | `/playback` | Stream a recording by `event_id` or `camera_id`+`ts` |
| GET | `/dashboard/stats`, `/analytics` | Dashboard tiles / analytics view data |
| WS | `/ws/events` | Real-time event push |

## What's built vs. roadmap

**Built:** everything in the table above, plus the full 4-layer detection pipeline, zone editor, and dashboard/analytics — see `prd.md` Section 5 for the original scope split (MVP vs. win-boosters), all of which is implemented.

**Explicitly out of scope for this prototype** (see `prd.md` Section 20): real RTSP/ONVIF camera integration, cloud storage/retention, authentication/roles/audit trails, face/license-plate recognition, native mobile apps, direct integration with A-1's Vigil PIDS sensor network, edge deployment.

**Worth knowing for anyone extending this:** Ultralytics YOLOv8 is AGPL-3.0 licensed for non-commercial/open use (a commercial license is available separately from Ultralytics) — fine for this prototype and demo, but a real product decision for A-1 if this pipeline goes further.

## Acknowledgements

Third-party libraries, models, and sample assets used in this project:

- **[Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)** (AGPL-3.0) — object detection model (`yolov8n.pt`, downloaded from Ultralytics' official GitHub releases)
- **[OpenCV](https://opencv.org/)** (Apache 2.0) — video capture, MOG2 background subtraction, video I/O
- **[Cisco OpenH264](https://github.com/cisco/openh264)** ([binary license](http://www.openh264.org/BINARY_LICENSE.txt)) — H.264 video encoder, required so recorded segments play in `<video>` (OpenCV's bundled FFmpeg has no H.264 encoder without it); binary vendored at `backend/vendor/openh264-2.5.0-win64.dll`
- **[FastAPI](https://fastapi.tiangolo.com/)** (MIT) — backend framework, auto-generated OpenAPI docs
- **[React](https://react.dev/)** (MIT), **[Vite](https://vitejs.dev/)** (MIT), **[Tailwind CSS](https://tailwindcss.com/)** (MIT), **[Recharts](https://recharts.org/)** (MIT), **[react-router-dom](https://reactrouter.com/)** (MIT) — frontend
- **Sample surveillance clips** — [Mixkit](https://mixkit.co/) (Mixkit Stock Video Free License, no attribution required, free for commercial/personal use):
  - ["Two thieves recorded on a security camera"](https://mixkit.co/free-stock-video/two-thieves-recorded-on-a-security-camera-31372/) — intrusion demo clip
  - ["Tree, wind and clouds in the blue sky"](https://mixkit.co/free-stock-video/tree-wind-and-clouds-in-the-blue-sky-30260/) — false-positive control clip
  - ["Footsteps of a young man walking down the street"](https://mixkit.co/free-stock-video/footsteps-of-a-young-man-walking-down-the-street-4893/) — pedestrian/zone-containment demo clip
  - ["Cars passing on a street in a town"](https://mixkit.co/free-stock-video/cars-passing-on-a-street-in-a-town-2872/) — vehicle-class detection demo clip

---

_See [`prd.md`](prd.md) for the full requirements document this build follows, including the 5-day milestone plan, functional requirements table, and demo video script._
