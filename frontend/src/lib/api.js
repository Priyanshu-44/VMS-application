const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const WS_BASE = import.meta.env.VITE_WS_BASE || 'ws://localhost:8000'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`${options.method || 'GET'} ${path} failed: ${res.status} ${text}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  base: API_BASE,
  wsBase: WS_BASE,

  // Cameras
  listCameras: () => request('/cameras'),
  getCamera: (id) => request(`/cameras/${id}`),
  streamUrl: (id) => `${API_BASE}/cameras/${id}/stream`,

  // Zones
  listZonesForCamera: (cameraId) => request(`/cameras/${cameraId}/zones`),
  createZone: (zone) => request('/zones', { method: 'POST', body: JSON.stringify(zone) }),
  updateZone: (id, patch) => request(`/zones/${id}`, { method: 'PUT', body: JSON.stringify(patch) }),
  deleteZone: (id) => request(`/zones/${id}`, { method: 'DELETE' }),

  // Events
  listEvents: (params = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
    ).toString()
    return request(`/events${qs ? `?${qs}` : ''}`)
  },
  getEvent: (id) => request(`/events/${id}`),
  acknowledgeEvent: (id) => request(`/events/${id}/acknowledge`, { method: 'POST' }),
  thumbnailUrl: (eventId) => `${API_BASE}/events/${eventId}/thumbnail`,

  // Recordings / playback
  listRecordings: (cameraId, params = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
    ).toString()
    return request(`/recordings/${cameraId}${qs ? `?${qs}` : ''}`)
  },
  playbackUrl: ({ eventId, cameraId, ts }) => {
    const qs = new URLSearchParams()
    if (eventId != null) qs.set('event_id', eventId)
    if (cameraId != null) qs.set('camera_id', cameraId)
    if (ts != null) qs.set('ts', ts)
    return `${API_BASE}/playback?${qs.toString()}`
  },

  // Dashboard / analytics (Stage 4)
  dashboardStats: () => request('/dashboard/stats'),
  analytics: () => request('/analytics'),
}
