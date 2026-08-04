import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useEventsSocket } from '../hooks/useEventsSocket'
import { api } from '../lib/api'
import { formatClock, formatRelative, tsToEpoch } from '../lib/time'

const TYPE_COLORS = { intrusion: '#ef4444', loitering: '#f59e0b', motion: '#8b97a8' }
const REFRESH_MS = 5000

export default function DashboardPage() {
  const [stats, setStats] = useState(null)
  const [cameras, setCameras] = useState([])
  const navigate = useNavigate()

  const load = () => {
    api.dashboardStats().then(setStats).catch(console.error)
  }

  useEffect(() => {
    api.listCameras().then(setCameras).catch(console.error)
    load()
    const id = setInterval(load, REFRESH_MS)
    return () => clearInterval(id)
  }, [])

  // Live-refresh immediately on any new event, don't wait for the poll tick
  useEventsSocket(() => load())

  const cameraById = Object.fromEntries(cameras.map((c) => [c.id, c]))

  return (
    <div className="p-6">
      <h1 className="text-lg font-semibold mb-1">Dashboard</h1>
      <p className="text-sm text-text-dim mb-5">Real-time operations overview</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Tile
          label="Camera Status"
          value={stats ? `${stats.cameras_online}/${stats.cameras_total}` : '—'}
          sub="online"
          accent={stats && stats.cameras_online === stats.cameras_total ? 'success' : 'warning'}
          icon="camera"
        />
        <Tile
          label="Active Alerts"
          value={stats ? stats.active_alerts : '—'}
          sub="unacknowledged"
          accent={stats?.active_alerts > 0 ? 'danger' : 'success'}
          icon="alert"
        />
        <Tile
          label="Storage Used"
          value={stats ? stats.storage_used_readable : '—'}
          sub="recordings + thumbnails"
          accent="accent"
          icon="storage"
        />
        <Tile
          label="Recent Detections"
          value={stats ? stats.recent_detections.length : '—'}
          sub="last 8 events"
          accent="accent"
          icon="detection"
        />
      </div>

      <div className="rounded-xl border border-border bg-panel">
        <div className="px-4 py-3 border-b border-border text-sm font-medium">Recent AI Detections</div>
        <div className="divide-y divide-border">
          {(stats?.recent_detections ?? []).map((e) => (
            <div
              key={e.id}
              onClick={() => navigate(`/playback/${e.camera_id}?event=${e.id}`)}
              className="flex items-center gap-3 px-4 py-2.5 hover:bg-panel-2 cursor-pointer transition-colors"
            >
              <img src={api.thumbnailUrl(e.id)} alt="" className="w-14 h-9 object-cover rounded bg-panel-2 shrink-0" />
              <div className="min-w-0 flex-1">
                <div className="text-sm truncate">
                  {cameraById[e.camera_id]?.name || `Camera ${e.camera_id}`}
                  <span className="text-text-dim"> · {e.object_class}</span>
                </div>
                <div className="text-[11px] text-text-dim">{formatRelative(tsToEpoch(e.ts))}</div>
              </div>
              <span
                className="text-[11px] capitalize px-2 py-0.5 rounded-full shrink-0"
                style={{ color: TYPE_COLORS[e.type], background: `${TYPE_COLORS[e.type]}15` }}
              >
                {e.type}
              </span>
              <span className="text-[11px] text-text-dim shrink-0 w-14 text-right">
                {formatClock(tsToEpoch(e.ts))}
              </span>
            </div>
          ))}
          {stats && stats.recent_detections.length === 0 && (
            <div className="px-4 py-8 text-center text-text-dim text-sm">No detections yet.</div>
          )}
        </div>
      </div>
    </div>
  )
}

const ICONS = {
  camera: 'M4 8h3l2-2h6l2 2h3v10H4V8zm8 3a3 3 0 100 6 3 3 0 000-6z',
  alert: 'M12 3l9 16H3l9-16zm0 6v4m0 3h.01',
  storage: 'M4 6h16v4H4V6zm0 8h16v4H4v-4zm4-6h.01M8 16h.01',
  detection: 'M12 4a4 4 0 100 8 4 4 0 000-8zM4 20c0-4 4-6 8-6s8 2 8 6',
}

const ACCENT_CLASSES = {
  success: 'text-success bg-success/10 border-success/30',
  warning: 'text-warning bg-warning/10 border-warning/30',
  danger: 'text-danger bg-danger/10 border-danger/30',
  accent: 'text-accent-2 bg-accent/10 border-accent/30',
}

function Tile({ label, value, sub, accent, icon }) {
  return (
    <div className="rounded-xl border border-border bg-panel p-4">
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs text-text-dim">{label}</span>
        <span className={`w-7 h-7 rounded-lg border flex items-center justify-center ${ACCENT_CLASSES[accent]}`}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
               strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
            <path d={ICONS[icon]} />
          </svg>
        </span>
      </div>
      <div className="text-2xl font-semibold">{value}</div>
      <div className="text-[11px] text-text-dim mt-0.5">{sub}</div>
    </div>
  )
}
