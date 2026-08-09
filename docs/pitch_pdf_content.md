# 3-Page PDF Content — ready to paste into Canva/PowerPoint/Google Slides

Screenshots are already captured at `docs/screenshots/` — use those files
directly, no need to retake them. File names are noted at each screenshot
slot below.

**File name on submission:** `ByteBreakers_NationalInstituteOfTechnologyDelhi_A-1Launchpad_2026.pdf`

---

## Page 1 — Problem & Solution

**Headline:** Smart VMS — AI Intrusion Detection & False-Alarm Suppression
**Team Byte Breakers · National Institute of Technology Delhi**

**The pain:**
Traditional surveillance systems force operators to switch between live
monitoring and recorded playback during an investigation — costing
precious seconds during a real incident. Worse, naïve motion detection
floods operators with false alarms (wind, animals, foliage), causing alert
fatigue: the one real intrusion looks identical to the hundred false ones
before it.

**Our one-line solution:**
A unified VMS where live feeds, recorded playback, and AI-flagged events
live on one interactive timeline — with a four-layer filtering pipeline
smart enough to know a swaying tree isn't an intruder.

**Architecture:**
```
Sample clips (looped, 4 cameras)
        │
        ▼
FastAPI backend — MJPEG stream, H.264 segment recording
        │
        ▼
Detection pipeline — MOG2 motion gate → YOLOv8 classify → zone test → dwell/cooldown
        │
        ▼
SQLite + clips/thumbnails on disk
        │
        ▼
React frontend — live grid · timeline · dashboard · zone editor · analytics
        ▲
        └── WebSocket real-time push
```

**Tech stack:** Python 3.13 + FastAPI · OpenCV + MOG2 · Ultralytics YOLOv8n
· SQLite · React + Vite + Tailwind CSS · Recharts · WebSocket

**Screenshot:** `docs/screenshots/live_grid.png` — all 4 camera tiles live

---

## Page 2 — Features & AI Approach

**The four-layer false-alarm pipeline:**

| Layer | What it does | Why it matters |
|---|---|---|
| 1. Motion pre-filter (MOG2) | Cheap background subtraction gates the expensive model | YOLO only runs when something actually moves |
| 2. Object-class filter (YOLOv8) | Must classify as person/car/truck/bus/bicycle/motorcycle | Leaves, shadows, birds discarded before zone check |
| 3. Zone containment | Detection centroid must fall inside an enabled operator-drawn polygon | A person on a public path outside the fence doesn't alert; crossing the perimeter does |
| 4. Dwell + cooldown | Escalation requires N seconds of continued presence; a 30s cooldown blocks duplicate re-alerts | One intruder generates one alert, not fifty |

**Verified result, this build:** 878 raw motion triggers → 78 confirmed
events = **91% false-alarm reduction**, with the wind/foliage test camera
sitting at **zero** detections throughout. (Recompute this from your own
Analytics page right before recording — it's a live figure, not fixed, and
will differ slightly session to session; use whatever you actually see.)

**Core features:**
- Live multi-camera grid with real-time alert flashing
- Interactive canvas timeline — colored event markers, hover-to-preview
  thumbnail, **one-click seek** to any event's exact footage
- Severity-coded bounding boxes on event thumbnails — red for intrusion,
  orange for loitering
- Zone editor — draw a polygon on a live paused frame, tune sensitivity
  and dwell time per zone, no restart required
- Dashboard — camera status, active alerts, storage usage, recent
  detections, all live via WebSocket
- Analytics — false-alarm reduction stat, detections/hour, detections/zone

**Screenshots:**
- `docs/screenshots/playback_timeline.png` — timeline with a marker clicked, seeking to that event
- `docs/screenshots/zone_editor.png` — polygon drawn on a paused frame
- `docs/screenshots/dashboard.png` — 4 tiles with live data

---

## Page 3 — Impact & Links

**Metrics (from this build's own verification, not projected):**
- **91%** false-alarm reduction vs. raw motion detection
- **< 3 seconds**, zero tool-switching, to go from a live alert to
  reviewing that exact moment's footage
- **1 click** from any timeline marker to seeked playback
- Detection loop runs on CPU alone — no GPU required for the demo
- Tested end-to-end on both the sample clips and a real live webcam feed

**What's built (all of it, verified live — not mocked):**
Live grid, continuous H.264 recording, full 4-layer detection pipeline,
event generation with real thumbnails (severity-colored bounding boxes)
and clip references, interactive timeline with click-to-seek, zone editor,
dashboard, analytics — every P0 requirement and both win-booster
differentiators from the spec.

**What's roadmap, deliberately not built for this prototype:**
Real RTSP/ONVIF camera integration, cloud storage & retention, user
authentication/roles/audit trails, face/license-plate recognition, native
mobile apps, direct integration with A-1's Vigil PIDS sensor network for
sensor-fused alerts, edge deployment.

**Relevance to A-1:** this directly mirrors the false-alarm problem A-1's
PIDS product line already faces in the field — the same zone + class +
dwell filtering logic applies whether the sensor is a camera or a fence
vibration sensor.

**Links:**
- GitHub: `https://github.com/Priyanshu-44/VMS-application`
- Demo video: `https://drive.google.com/file/d/1P0PAuc7I6PgwUa2UF9chmtmrAyLpWdFZ/view?usp=sharing`

**Screenshot:** `docs/screenshots/analytics.png` — false-alarm-reduction stat block

---

## Cover page (if your template needs one separately)

- Title: **Smart VMS — AI Intrusion Detection & False-Alarm Suppression**
- Case Study: Smart Video Management System (VMS)
- Team: Byte Breakers
- College: National Institute of Technology Delhi
- Event: A-1 Launchpad 2026 — Round 2, Software Development / AI-ML track
