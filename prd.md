# Product Requirements Document — Smart Video Management System (VMS)

**Project:** Smart VMS with AI Intrusion Detection & False-Alarm Suppression
**Event:** A-1 Launchpad 2026 — Round 2 (Software Development / AI-ML track)
**Case Study:** Smart Video Management System (VMS)
**Deadline:** 9 August 2026 (Sunday), 11:59 PM — submit on Unstop
**Document owner:** _[Your name]_ · **Team:** _[Team name]_ · **College:** _[College name]_
**Status:** Draft v1.0 · **Last updated:** _[date]_

---

## 1. Executive summary

We are building a modern **Video Management System (VMS)** that unifies live camera monitoring and recorded-footage playback in a single interface, with **AI-detected intrusion/motion events** surfaced directly on an interactive timeline.

The product's differentiator — and the reason it fits A-1 specifically — is **false-alarm suppression through configurable detection zones and object-class filtering**. A-1 manufactures perimeter security systems (fences, gates, PIDS). Their operators drown in false alerts triggered by wind, animals, and moving foliage. Our VMS is "smart enough to know a swaying tree is not an intruder." That framing is our winning thesis and should lead every deliverable.

This is a **functional prototype**, not a paper concept. The demo shows real detection running on live video, events landing on the timeline, one-click seek-to-event playback, and a live operations dashboard.

---

## 2. Problem statement

Traditional surveillance systems separate live monitoring from recorded playback, forcing operators to switch tools during an incident investigation. This slows response and increases the chance of missing a real threat. Simultaneously, naïve motion detection floods operators with false alarms, causing alert fatigue — the real intrusion gets ignored because it looks like the hundred false ones before it.

Operators need a single interface where they can:
- Watch multiple live feeds at once.
- Scroll back through recordings on a timeline without leaving the view.
- Instantly jump to AI-flagged events instead of scrubbing manually.
- Trust the alerts, because the system filters out obvious non-threats.

## 3. Goals & success metrics

| Goal | Metric | Target (demo) |
|---|---|---|
| Unify live + playback | Time to review a past event from live view | < 3 seconds, no tool switch |
| Detect intrusions with AI | Person-detection accuracy on demo clips | Reliable on clear frames |
| Cut false alarms | Reduction vs raw motion detection | Show measurable drop (e.g. zone + class filter removes ~70% of noise triggers) |
| Fast event navigation | Clicks to reach any event's footage | 1 click on timeline marker |
| Operator situational awareness | Dashboard load with live status | Real-time tiles updating |

**Non-goals for the prototype:** production-grade RTSP CCTV integration, cloud storage, multi-tenant auth, mobile app. These are roadmap items, acknowledged but not built.

## 4. Target users / personas

- **Control-room operator (primary):** monitors feeds, responds to alerts, investigates incidents. Needs speed, clarity, low false-alarm noise.
- **Security supervisor:** reviews analytics and trends, tunes detection zones, audits incidents.
- **System admin (secondary):** configures cameras, storage, and detection settings.

## 5. Scope

### 5.1 In scope — MVP (the demo spine, must be flawless)
- Live multi-camera grid (webcam + looped sample surveillance clips as "cameras").
- Continuous recording of feeds to disk as short segments.
- AI person/vehicle detection on the live stream.
- Event creation on detection: timestamp, camera, class, confidence, thumbnail, clip reference.
- Interactive timeline with event markers and **click-to-seek** playback.
- Event list with timestamps and camera details.
- Dashboard with four tiles: camera status, recent detections, storage usage, active alerts.

### 5.2 In scope — Win-boosters (our differentiators)
- **Detection zones:** operator draws a polygon on a camera feed; events fire only when a detected object's centroid falls inside an enabled zone.
- **False-alarm suppression:** object-class filter (ignore anything not person/vehicle), confidence threshold, and a **dwell/loitering rule** (person must remain in a zone > N seconds to escalate).
- A small **analytics view:** detections per hour and per zone; false-alarm vs confirmed ratio.

### 5.3 Out of scope (mention as roadmap only)
- Real RTSP/ONVIF CCTV camera integration.
- Cloud video storage and retention policies.
- User authentication, roles, and audit logging.
- Face recognition / license-plate recognition.
- Native mobile applications.

## 6. Functional requirements

Each requirement maps to the case-study task list. Priority: **P0** = MVP, **P1** = win-booster, **P2** = nice-to-have.

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Display live feeds from multiple cameras in a grid layout | P0 |
| FR-2 | Continuously record each feed to disk in retrievable segments | P0 |
| FR-3 | Scroll back and play previous recordings via a timeline | P0 |
| FR-4 | Provide smooth playback (seek, play, pause) | P0 |
| FR-5 | Detect motion/intrusion events using AI (YOLOv8 + motion pre-filter) | P0 |
| FR-6 | Mark detected events as markers on the playback timeline | P0 |
| FR-7 | Display event timestamps for quick navigation | P0 |
| FR-8 | One-click seek from a timeline marker to that event's footage | P0 |
| FR-9 | Show an event list with timestamp, camera, type, confidence | P0 |
| FR-10 | Dashboard: camera status overview (online/offline) | P0 |
| FR-11 | Dashboard: recent AI detections feed | P0 |
| FR-12 | Dashboard: storage usage indicator | P0 |
| FR-13 | Dashboard: active alerts count | P0 |
| FR-14 | Create/edit polygon detection zones on a camera feed | P1 |
| FR-15 | Trigger events only for objects inside enabled zones | P1 |
| FR-16 | Filter detections by object class (person, car, truck) | P1 |
| FR-17 | Apply confidence threshold and event debounce/cooldown | P1 |
| FR-18 | Loitering/dwell rule: escalate only after N seconds in zone | P1 |
| FR-19 | Analytics: detections per hour and per zone | P1 |
| FR-20 | Acknowledge / dismiss an alert | P2 |
| FR-21 | Adjustable sensitivity per zone | P2 |

## 7. The differentiator in detail — false-alarm suppression

This section is the heart of the pitch. A raw motion detector fires on everything. Our pipeline layers four filters so only meaningful events reach the operator:

1. **Motion pre-filter (OpenCV MOG2):** cheap background subtraction gates the expensive model — YOLO only runs when something actually moves. Saves compute and framing.
2. **Object-class filter (YOLOv8):** the moving thing must be classified as a relevant class — `person`, `car`, `truck`, `bicycle`, `motorcycle`. Leaves, shadows, and birds are discarded.
3. **Zone containment:** the object's centroid must fall inside an operator-drawn polygon. A person walking on a public path outside the fence line does not alert; the same person crossing the perimeter does.
4. **Dwell / debounce:** a momentary detection is suppressed; escalation requires the object to persist in-zone for N seconds (configurable), and a cooldown prevents one intruder from generating fifty duplicate events.

**Demo framing:** show the same clip with (a) raw motion detection lighting up constantly, then (b) our filtered pipeline firing exactly once, on the real intrusion. Quantify the reduction. That contrast is the moment that wins the round.

## 8. System architecture

```
Camera feeds (webcam + looped sample clips)
        │
        ▼
FastAPI backend  ── ingest, MJPEG stream out, segment recording
        │
        ▼
AI detection engine  ── MOG2 motion gate → YOLOv8 classify → zone test → dwell/debounce
        │
        ▼
Event store  ── SQLite (events, zones, cameras) + clips & thumbnails on disk
        │
        ▼
React frontend  ── live grid · timeline (markers + seek) · dashboard · zone editor · analytics
        ▲
        └── WebSocket for real-time event push
```

**Flow summary:** the backend pulls frames from each source, streams them to the browser as MJPEG, and records segments to disk. In parallel, the detection engine analyzes frames; when all filters pass, it writes an event (with thumbnail + clip offset) to SQLite and pushes it to the frontend over WebSocket. The frontend renders live feeds, plots events on the timeline, and lets the operator click any marker to seek the corresponding recording.

## 9. Technology stack

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3.11 + FastAPI | Async, pairs naturally with the ML code, auto OpenAPI docs |
| Video I/O | OpenCV, FFmpeg | Frame capture, MJPEG streaming, segment recording |
| Object detection | Ultralytics YOLOv8 (nano/small) | Fast, accurate, easy zone integration, runs on CPU for demo |
| Motion pre-filter | OpenCV MOG2 | Cheap gate before running the model |
| Database | SQLite | Zero-config, perfect for a prototype, easy to ship as sample data |
| Real-time | WebSocket (FastAPI) | Push new events to the UI instantly |
| Frontend | React + Vite + Tailwind CSS | Fast to build, clean modern dark UI |
| Timeline/zones | HTML5 `<canvas>` | Custom marker rendering and polygon drawing |
| Charts | Recharts or Chart.js | Analytics view |

All third-party libraries, models, and sample datasets used **must be acknowledged** in the README and PDF (case-study requirement).

## 10. Data model (SQLite schema)

```sql
CREATE TABLE cameras (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    source        TEXT NOT NULL,          -- device index, file path, or URL
    location      TEXT,
    status        TEXT DEFAULT 'online',  -- online | offline
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE zones (
    id            INTEGER PRIMARY KEY,
    camera_id     INTEGER REFERENCES cameras(id),
    name          TEXT NOT NULL,
    polygon       TEXT NOT NULL,          -- JSON: [[x,y],[x,y],...] normalized 0-1
    enabled       INTEGER DEFAULT 1,
    sensitivity   REAL DEFAULT 0.5,       -- confidence threshold override
    dwell_seconds INTEGER DEFAULT 2
);

CREATE TABLE events (
    id             INTEGER PRIMARY KEY,
    camera_id      INTEGER REFERENCES cameras(id),
    zone_id        INTEGER REFERENCES zones(id),
    type           TEXT NOT NULL,         -- intrusion | motion | loitering
    object_class   TEXT,                  -- person | car | truck ...
    confidence     REAL,
    ts             TIMESTAMP NOT NULL,
    clip_path      TEXT,                  -- recorded segment
    clip_offset    REAL,                  -- seconds into segment
    thumbnail_path TEXT,
    acknowledged   INTEGER DEFAULT 0
);

CREATE TABLE recordings (
    id          INTEGER PRIMARY KEY,
    camera_id   INTEGER REFERENCES cameras(id),
    start_ts    TIMESTAMP NOT NULL,
    end_ts      TIMESTAMP,
    file_path   TEXT NOT NULL,
    size_bytes  INTEGER
);
```

## 11. API design (REST + WebSocket)

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/cameras` | List cameras with status |
| POST | `/cameras` | Register a camera source |
| GET | `/cameras/{id}/stream` | MJPEG live stream |
| GET | `/cameras/{id}/zones` | List zones for a camera |
| POST | `/zones` | Create a detection zone (polygon) |
| PUT | `/zones/{id}` | Update / enable / disable a zone |
| DELETE | `/zones/{id}` | Remove a zone |
| GET | `/events` | List events (filters: camera, time range, type) |
| GET | `/events/{id}` | Event detail |
| POST | `/events/{id}/acknowledge` | Dismiss an alert |
| GET | `/recordings/{camera_id}` | Segments in a time window (for the timeline) |
| GET | `/playback` | Stream a recording seeked to `?ts=` |
| GET | `/dashboard/stats` | Camera status, recent detections, storage, active alerts |
| GET | `/analytics` | Detections per hour / per zone |
| WS | `/ws/events` | Real-time push of new events |

FastAPI auto-generates interactive API docs at `/docs` — use this as your **API documentation deliverable**.

## 12. AI / ML detection pipeline (pseudocode)

```python
for frame in camera.frames():
    record_segment(frame)                      # always record

    if not motion_detected(frame, mog2):       # cheap gate
        continue

    detections = yolo(frame)                    # run model only on motion
    for det in detections:
        if det.cls not in RELEVANT_CLASSES:     # ignore non-threats
            continue
        if det.confidence < zone.sensitivity:   # confidence gate
            continue
        if not point_in_polygon(det.centroid, zone.polygon):
            continue                            # outside the zone

        track = update_tracker(det)             # dwell / loitering
        if track.dwell_seconds >= zone.dwell_seconds \
           and not in_cooldown(track):
            create_event(camera, zone, det, type_for(track))
            push_ws(event)
            start_cooldown(track)
```

Key techniques to name in the PDF: background subtraction (MOG2), single-stage object detection (YOLOv8), point-in-polygon zone testing, centroid tracking with dwell-time thresholding, and event debouncing.

## 13. UI / UX — screens & components

**Design language:** modern dark theme, sidebar navigation, minimal and operator-friendly, consistent colors/icons/typography.

- **Live grid:** 2×2 (or N-up) camera grid; each tile shows feed, camera name, online/offline dot, and flashes when it has an active alert.
- **Timeline (centerpiece):** horizontal track spanning the recording window; colored markers at event timestamps; hover shows thumbnail; click seeks the player. This component is the make-or-break of the demo — invest the most polish here.
- **Playback view:** video player synced to the timeline; play/pause/seek; jump-to-next-event control.
- **Zone editor:** click on a paused frame to place polygon points; save/enable per camera.
- **Dashboard:** four tiles — camera status, recent detections feed, storage usage bar, active alerts count.
- **Analytics:** detections-per-hour bar chart, per-zone breakdown, confirmed-vs-false ratio.
- **Event list:** filterable table (camera, time, class, confidence, acknowledge button).

## 14. Non-functional requirements

- **Performance:** detection loop keeps up with demo feeds (throttle to ~10–15 fps analysis if needed); UI stays responsive.
- **Reliability:** recording never stops even if detection lags; events queue and flush.
- **Usability:** an operator reaches any event's footage in one click; dark theme reduces eye strain.
- **Portability:** runs on a single laptop; SQLite + local files, no external services required for the demo.
- **Documentation:** README with architecture, setup steps, and dependency acknowledgements; API docs via `/docs`.

## 15. Milestones — 5-day plan

| Day | Date | Deliverable |
|---|---|---|
| 1 | Aug 4 | Repo + FastAPI skeleton; YOLOv8 running on webcam + sample clips; SQLite schema locked; scope frozen |
| 2 | Aug 5 | Detection zones (polygon + point-in-polygon); event generation with thumbnail + clip; class/confidence filter |
| 3 | Aug 6 | Frontend: live grid, player, and the timeline with markers + click-to-seek (protect this day) |
| 4 | Aug 7 | Dashboard tiles, analytics view, loitering/dwell rule, visual polish |
| 5 | Aug 8 | **Feature freeze.** Record demo video; write 3-page PDF; clean README + sample data |
| — | Aug 9 | Buffer + morning submission (do not wait until 11:58 PM) |

## 16. Deliverables (mapped to Unstop submission requirements)

1. **Mandatory demo video** — 3–5 min, link embedded in the PDF.
2. **Source code** — public GitHub repository.
3. **Project documentation** — README: architecture, features, setup, dependency acknowledgements.
4. **Database schema** — the SQLite schema in Section 10.
5. **API documentation** — FastAPI `/docs` (OpenAPI), plus the table in Section 11.
6. **Presentation / PDF** — max 3 pages (excluding cover page + both resumes); see Section 18.
7. **Sample data / config** — seed cameras, sample surveillance clips, pre-drawn zones so judges can reproduce the demo.

**File naming:** `TeamName_CollegeName_A-1Launchpad_2026.pdf`

## 17. Demo video script (3–5 min)

1. **Hook (20s):** "A-1's operators face thousands of false alarms a day. Here's a VMS smart enough to ignore the tree and catch the intruder."
2. **Live grid (30s):** show multiple feeds, camera status, dark UI.
3. **Raw vs filtered (45s):** run a clip with naïve motion detection lighting up constantly, then the same clip through our zone + class filter firing once. State the false-alarm reduction number.
4. **Detection + timeline (45s):** a person enters a zone → event fires → marker appears on the timeline → click it to replay the moment. This is the core "wow."
5. **Zone editor (30s):** draw a polygon, enable it, show it changes what alerts.
6. **Dashboard + analytics (30s):** four tiles updating live; detections-per-hour chart.
7. **Close (20s):** relevance to A-1's PIDS product line; one line on the roadmap (RTSP, cloud, auth).

## 18. Three-page PDF structure

- **Page 1 — Problem & solution:** the pain (split live/playback + alert fatigue), our one-line solution, the architecture diagram, tech stack.
- **Page 2 — Features & AI approach:** annotated screenshots (timeline with markers, zone editor, dashboard); the four-layer false-alarm pipeline explained visually.
- **Page 3 — Impact & links:** metrics (false-alarm reduction, one-click investigation, detection latency), what's built vs roadmap, **GitHub link + video link** prominently.

## 19. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Timeline UI eats too much time | It's the demo's spine — start Day 3, keep it simple (canvas markers, seek), polish only if time allows |
| YOLO too slow on CPU | Use YOLOv8-nano; motion pre-filter gates it; throttle analysis fps; pre-record the hero clip |
| Scope creep from the full checklist | Freeze scope Day 1 to MVP + two boosters; everything else is roadmap |
| Real CCTV integration rabbit hole | Explicitly out of scope; webcam + sample clips are enough for judging |
| Last-minute submission failure | Submit Aug 9 morning with buffer, not at the deadline |

## 20. Future roadmap (mention, don't build)

- RTSP/ONVIF integration with real IP cameras.
- Cloud storage with retention policies and remote access.
- User authentication, roles, and audit trails.
- Advanced analytics: heatmaps, cross-camera tracking, license-plate/face recognition.
- Direct integration with A-1's Vigil PIDS sensor network for sensor-fused alerts.
- Edge deployment on-site for low-latency, bandwidth-light operation.

## 21. Acknowledgements / references

To be completed before submission — list every library, model, dataset, and asset used (e.g. Ultralytics YOLOv8, OpenCV, FastAPI, React, Tailwind, sample surveillance clips and their source/license). Required by the case-study rules.

---

_This PRD is the single source of truth for the build. Update the header status and Section 15 as milestones complete._
