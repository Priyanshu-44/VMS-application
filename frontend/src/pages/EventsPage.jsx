import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useEventsSocket } from '../hooks/useEventsSocket'
import { api } from '../lib/api'
import { formatClock, formatRelative, tsToEpoch } from '../lib/time'

const TYPE_COLORS = { intrusion: '#ef4444', loitering: '#f59e0b', motion: '#8b97a8' }

export default function EventsPage() {
  const [events, setEvents] = useState([])
  const [cameras, setCameras] = useState([])
  const [cameraFilter, setCameraFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [ackFilter, setAckFilter] = useState('')
  const navigate = useNavigate()

  const load = () => {
    api
      .listEvents({
        camera_id: cameraFilter || undefined,
        type: typeFilter || undefined,
        limit: 300,
      })
      .then(setEvents)
      .catch(console.error)
  }

  useEffect(() => {
    api.listCameras().then(setCameras).catch(console.error)
  }, [])

  useEffect(load, [cameraFilter, typeFilter])

  useEventsSocket((event) => {
    setEvents((prev) => (prev.some((e) => e.id === event.id) ? prev : [event, ...prev]))
  })

  const cameraById = useMemo(() => Object.fromEntries(cameras.map((c) => [c.id, c])), [cameras])

  const visible = events.filter((e) => {
    // events can arrive live over the WebSocket independent of the filtered
    // fetch in load() above, so filters need to be re-applied here too --
    // otherwise a live push for a camera/type outside the current filter
    // slips into the list.
    if (cameraFilter && String(e.camera_id) !== String(cameraFilter)) return false
    if (typeFilter && e.type !== typeFilter) return false
    if (ackFilter === 'unacknowledged' && e.acknowledged) return false
    if (ackFilter === 'acknowledged' && !e.acknowledged) return false
    return true
  })

  async function acknowledge(id, e) {
    e.stopPropagation()
    const updated = await api.acknowledgeEvent(id)
    setEvents((prev) => prev.map((ev) => (ev.id === id ? updated : ev)))
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-lg font-semibold">Events</h1>
          <p className="text-sm text-text-dim">{visible.length} event{visible.length !== 1 ? 's' : ''}</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={cameraFilter} onChange={setCameraFilter} placeholder="All cameras">
            {cameras.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </Select>
          <Select value={typeFilter} onChange={setTypeFilter} placeholder="All types">
            <option value="intrusion">Intrusion</option>
            <option value="loitering">Loitering</option>
            <option value="motion">Motion</option>
          </Select>
          <Select value={ackFilter} onChange={setAckFilter} placeholder="All statuses">
            <option value="unacknowledged">Unacknowledged</option>
            <option value="acknowledged">Acknowledged</option>
          </Select>
        </div>
      </div>

      <div className="rounded-xl border border-border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-panel-2 text-text-dim text-xs uppercase tracking-wide">
            <tr>
              <th className="text-left px-4 py-2.5 font-medium">Thumbnail</th>
              <th className="text-left px-4 py-2.5 font-medium">Time</th>
              <th className="text-left px-4 py-2.5 font-medium">Camera</th>
              <th className="text-left px-4 py-2.5 font-medium">Type</th>
              <th className="text-left px-4 py-2.5 font-medium">Class</th>
              <th className="text-left px-4 py-2.5 font-medium">Confidence</th>
              <th className="text-left px-4 py-2.5 font-medium">Status</th>
              <th className="text-right px-4 py-2.5 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {visible.map((e) => (
              <tr
                key={e.id}
                onClick={() => navigate(`/playback/${e.camera_id}?event=${e.id}`)}
                className="border-t border-border hover:bg-panel-2 cursor-pointer transition-colors"
              >
                <td className="px-4 py-2">
                  <img
                    src={api.thumbnailUrl(e.id)}
                    alt=""
                    className="w-16 h-10 object-cover rounded bg-panel-2"
                  />
                </td>
                <td className="px-4 py-2 whitespace-nowrap">
                  <div>{formatClock(tsToEpoch(e.ts))}</div>
                  <div className="text-[11px] text-text-dim">{formatRelative(tsToEpoch(e.ts))}</div>
                </td>
                <td className="px-4 py-2">{cameraById[e.camera_id]?.name || `Camera ${e.camera_id}`}</td>
                <td className="px-4 py-2">
                  <span
                    className="inline-flex items-center gap-1.5 capitalize px-2 py-0.5 rounded-full text-xs border"
                    style={{
                      color: TYPE_COLORS[e.type],
                      borderColor: `${TYPE_COLORS[e.type]}40`,
                      background: `${TYPE_COLORS[e.type]}15`,
                    }}
                  >
                    {e.type}
                  </span>
                </td>
                <td className="px-4 py-2 capitalize">{e.object_class}</td>
                <td className="px-4 py-2">{Math.round((e.confidence || 0) * 100)}%</td>
                <td className="px-4 py-2">
                  {e.acknowledged ? (
                    <span className="text-text-dim text-xs">Acknowledged</span>
                  ) : (
                    <span className="text-warning text-xs">Pending</span>
                  )}
                </td>
                <td className="px-4 py-2 text-right">
                  {!e.acknowledged && (
                    <button
                      onClick={(ev) => acknowledge(e.id, ev)}
                      className="text-xs px-2.5 py-1 rounded-lg border border-border hover:border-accent/40 hover:text-accent-2"
                    >
                      Acknowledge
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {visible.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-10 text-center text-text-dim">
                  No events match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Select({ value, onChange, placeholder, children }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="bg-panel-2 border border-border rounded-lg text-sm px-3 py-1.5 text-text focus:outline-none focus:border-accent/50"
    >
      <option value="">{placeholder}</option>
      {children}
    </select>
  )
}
