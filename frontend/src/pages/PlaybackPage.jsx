import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import Timeline from '../components/Timeline'
import { useEventsSocket } from '../hooks/useEventsSocket'
import { api } from '../lib/api'
import { formatClock, tsToEpoch } from '../lib/time'

const WINDOW_CAP_SECONDS = 30 * 60 // never show more than the last 30 minutes on the track

const TYPE_COLORS = { intrusion: '#ef4444', loitering: '#f59e0b', motion: '#8b97a8' }

export default function PlaybackPage() {
  const { cameraId } = useParams()
  const id = Number(cameraId)
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const videoRef = useRef(null)

  const [camera, setCamera] = useState(null)
  const [events, setEvents] = useState([])
  const [recordings, setRecordings] = useState([])
  const [mode, setMode] = useState('live') // 'live' | 'playback'
  const [currentTs, setCurrentTs] = useState(null)
  const [videoSrc, setVideoSrc] = useState(null)
  const pendingOffsetRef = useRef(null)
  const [now, setNow] = useState(Date.now() / 1000)

  useEffect(() => {
    api.getCamera(id).then(setCamera).catch(console.error)
  }, [id])

  const refreshEvents = () => {
    api.listEvents({ camera_id: id, limit: 300 }).then(setEvents).catch(console.error)
  }
  const refreshRecordings = () => {
    api.listRecordings(id).then(setRecordings).catch(console.error)
  }

  useEffect(() => {
    refreshEvents()
    refreshRecordings()
    const poll = setInterval(() => {
      refreshRecordings()
      setNow(Date.now() / 1000)
    }, 5000)
    return () => clearInterval(poll)
  }, [id])

  useEventsSocket((event) => {
    if (event.camera_id === id) setEvents((prev) => [event, ...prev])
  })

  // Deep-link support: /playback/:cameraId?event=123
  useEffect(() => {
    const eventId = searchParams.get('event')
    if (eventId) seekToEvent(Number(eventId))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams.get('event')])

  const windowStart = useMemo(() => {
    if (recordings.length === 0) return now - WINDOW_CAP_SECONDS
    const earliest = tsToEpoch(recordings[0].start_ts)
    return Math.max(earliest, now - WINDOW_CAP_SECONDS)
  }, [recordings, now])
  const windowEnd = now

  function findRecordingForTs(ts) {
    return recordings.find((r) => {
      const start = tsToEpoch(r.start_ts)
      const end = r.end_ts ? tsToEpoch(r.end_ts) : now
      return ts >= start && ts <= end
    })
  }

  function seekToEvent(eventId) {
    const ev = events.find((e) => e.id === eventId)
    if (!ev) {
      // not loaded locally yet — resolve straight from the API
      api.getEvent(eventId).then((full) => applySeek(tsToEpoch(full.ts), full))
      return
    }
    applySeek(tsToEpoch(ev.ts), ev)
  }

  function applySeek(ts, ev) {
    setMode('playback')
    setCurrentTs(ts)
    if (ev?.id) {
      pendingOffsetRef.current = ev.clip_offset ?? 0
      setVideoSrc(api.playbackUrl({ eventId: ev.id }))
    } else {
      const rec = findRecordingForTs(ts)
      if (!rec) return
      pendingOffsetRef.current = ts - tsToEpoch(rec.start_ts)
      setVideoSrc(api.playbackUrl({ cameraId: id, ts }))
    }
  }

  function handleTimelineSeek(ts, ev) {
    applySeek(ts, ev)
  }

  function handleLoadedMetadata() {
    if (pendingOffsetRef.current != null && videoRef.current) {
      videoRef.current.currentTime = Math.max(0, pendingOffsetRef.current)
      pendingOffsetRef.current = null
    }
  }

  const sortedEvents = useMemo(
    () => [...events].sort((a, b) => tsToEpoch(a.ts) - tsToEpoch(b.ts)),
    [events]
  )

  function jumpToEvent(direction) {
    if (sortedEvents.length === 0) return
    if (currentTs == null) {
      const target = direction === 'next' ? sortedEvents[0] : sortedEvents[sortedEvents.length - 1]
      applySeek(tsToEpoch(target.ts), target)
      return
    }
    if (direction === 'next') {
      const target = sortedEvents.find((e) => tsToEpoch(e.ts) > currentTs + 0.5)
      if (target) applySeek(tsToEpoch(target.ts), target)
    } else {
      const candidates = sortedEvents.filter((e) => tsToEpoch(e.ts) < currentTs - 0.5)
      const target = candidates[candidates.length - 1]
      if (target) applySeek(tsToEpoch(target.ts), target)
    }
  }

  function goLive() {
    setMode('live')
    setCurrentTs(null)
    setVideoSrc(null)
  }

  if (!camera) return <div className="p-6 text-text-dim">Loading camera…</div>

  return (
    <div className="p-6 flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <button onClick={() => navigate('/')} className="text-xs text-text-dim hover:text-text mb-1">
            ← Live Grid
          </button>
          <h1 className="text-lg font-semibold">{camera.name}</h1>
          <p className="text-sm text-text-dim">{camera.location}</p>
        </div>
        <div className="flex items-center gap-2">
          {mode === 'playback' && (
            <span className="text-xs text-accent-2 bg-accent/10 border border-accent/30 px-2.5 py-1 rounded-full">
              Playback {currentTs ? `· ${formatClock(currentTs)}` : ''}
            </span>
          )}
          <button
            onClick={goLive}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              mode === 'live'
                ? 'bg-success/15 border-success/40 text-success'
                : 'border-border text-text-dim hover:text-text'
            }`}
          >
            ● Go Live
          </button>
        </div>
      </div>

      <div className="rounded-xl overflow-hidden border border-border bg-black aspect-video flex items-center justify-center mb-4">
        {mode === 'live' ? (
          <img src={api.streamUrl(id)} alt={camera.name} className="w-full h-full object-contain" />
        ) : (
          <video
            ref={videoRef}
            src={videoSrc}
            controls
            autoPlay
            onLoadedMetadata={handleLoadedMetadata}
            className="w-full h-full object-contain"
          />
        )}
      </div>

      <div className="flex items-center gap-2 mb-3">
        <button
          onClick={() => jumpToEvent('prev')}
          className="text-xs px-3 py-1.5 rounded-lg border border-border text-text-dim hover:text-text hover:border-accent/40"
        >
          ◀ Prev event
        </button>
        <button
          onClick={() => jumpToEvent('next')}
          className="text-xs px-3 py-1.5 rounded-lg border border-border text-text-dim hover:text-text hover:border-accent/40"
        >
          Next event ▶
        </button>
        <div className="flex-1" />
        <Legend />
      </div>

      <div className="rounded-xl border border-border bg-panel p-3">
        <Timeline
          events={events}
          windowStart={windowStart}
          windowEnd={windowEnd}
          currentTime={currentTs}
          onSeek={handleTimelineSeek}
        />
      </div>
    </div>
  )
}

function Legend() {
  return (
    <div className="flex items-center gap-3 text-[11px] text-text-dim">
      {Object.entries(TYPE_COLORS).map(([type, color]) => (
        <span key={type} className="flex items-center gap-1.5 capitalize">
          <span className="w-2 h-2 rounded-full" style={{ background: color }} />
          {type}
        </span>
      ))}
    </div>
  )
}
