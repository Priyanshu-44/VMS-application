# Demo Video Script (3–5 min)

Adapted from `prd.md` Section 17, filled in with the real numbers this build
produces — not placeholders. Re-run `verify_yolo.py` / let the app run for
a few minutes before recording and swap in your own session's numbers from
the Analytics page if they differ.

**Recording note:** this is a script for *you* to record (screen capture +
voiceover) — it isn't something that can be generated automatically. Run
the backend + frontend per the README, let it run for ~2 minutes so the
Analytics page has real numbers, then record in this order.

---

### 1. Hook (20s)
> "A-1's operators face thousands of false alarms a day. Here's a VMS smart
> enough to ignore the tree and catch the intruder."

*(Show the dark-themed Live Grid full-screen for a beat before talking.)*

### 2. Live grid (30s)
- Show all 4 camera tiles streaming, online status dots, camera names/locations.
- Point out the dark, operator-friendly UI.

### 3. Raw vs. filtered (45s) — **the core pitch**
- Navigate to **Analytics**.
- Point at the headline stat: **"False-alarm reduction: 85.9%"** (or your
  session's live number — it updates every 8s).
- Say the numbers out loud: *"85 raw motion triggers, only 12 became
  confirmed events — that's what a naive motion detector would have fired
  fifty-plus times on, filtered down to real signal."*
- Point at the per-zone breakdown: **Perimeter Cam 2 (Tree Line) sits at
  zero detections** — the wind moving the tree registers as motion, but
  never survives the class filter.

### 4. Detection + timeline (45s) — **the "wow" moment**
- Go to **Playback** for Perimeter Cam 1 (Rear Gate).
- Either wait for a live alert flash on the Live Grid and click through, or
  click **Next event ▶** to jump to the most recent one.
- Show the marker appearing on the timeline in real time (if timed with a
  live event) or click directly on a marker — **one click, footage plays
  from that exact moment.**
- Hover another marker to show the thumbnail preview tooltip.

### 5. Zone editor (30s)
- Go to **Zones**, select a camera, click **+ New Zone**.
- Click 4-5 points on the paused frame to draw a polygon live on camera.
- Save it, show it appear as a labeled colored overlay.
- Toggle a zone's **Enabled** checkbox off — mention this instantly stops
  events from firing for that zone, no restart needed.

### 6. Dashboard + analytics (30s)
- Back to **Dashboard**: point at all 4 tiles updating — camera status,
  active alerts, storage usage, recent detections feed (click one to jump
  straight to its playback moment).
- Quick pass over the detections-per-hour chart on Analytics.

### 7. Close (20s)
> "This maps directly onto A-1's PIDS product line — same false-alarm
> problem, same fix. Roadmap from here: real RTSP camera integration,
> cloud storage, and fusing this with A-1's Vigil sensor network for
> sensor-fused alerts."

---

**Total: ~3.5 min core content** — pad with a 10-15s intro title card and
outro (GitHub link + team name) to land in the 3-5 min window.
