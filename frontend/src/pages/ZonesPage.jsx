import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../lib/api'

const ZONE_COLORS = ['#3b82f6', '#22d3ee', '#f59e0b', '#a78bfa', '#f472b6', '#34d399']

/**
 * Zone editor (FR-14/15/16/17/18/21): pick a camera, click points on a
 * paused frame to draw a polygon, save it with a name/sensitivity/dwell.
 * Existing zones render as labeled overlays; toggling enabled and tuning
 * sensitivity/dwell happens inline in the list, no re-drawing required.
 */
export default function ZonesPage() {
  const [cameras, setCameras] = useState([])
  const [cameraId, setCameraId] = useState(null)
  const [zones, setZones] = useState([])
  const [snapshotKey, setSnapshotKey] = useState(0)
  const [draftPoints, setDraftPoints] = useState([])
  const [drawing, setDrawing] = useState(false)
  const [form, setForm] = useState({ name: '', sensitivity: 0.5, dwell_seconds: 2 })
  const [imgSize, setImgSize] = useState({ w: 1280, h: 720 })
  const [error, setError] = useState(null)

  const canvasRef = useRef(null)
  const imgRef = useRef(null)

  useEffect(() => {
    api.listCameras().then((cams) => {
      setCameras(cams)
      if (cams.length && cameraId == null) setCameraId(cams[0].id)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const refreshZones = () => {
    if (cameraId == null) return
    api.listZonesForCamera(cameraId).then(setZones).catch(console.error)
  }
  useEffect(refreshZones, [cameraId])

  // Load snapshot image
  useEffect(() => {
    if (cameraId == null) return
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      imgRef.current = img
      setImgSize({ w: img.naturalWidth, h: img.naturalHeight })
      draw()
    }
    img.src = api.snapshotUrl(cameraId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cameraId, snapshotKey])

  const width = 800
  const height = Math.round((width * imgSize.h) / imgSize.w)

  function draw() {
    const canvas = canvasRef.current
    if (!canvas || !imgRef.current) return
    const ctx = canvas.getContext('2d')
    canvas.width = width
    canvas.height = height
    ctx.clearRect(0, 0, width, height)
    ctx.drawImage(imgRef.current, 0, 0, width, height)

    // Existing zones
    zones.forEach((z, i) => {
      const color = ZONE_COLORS[i % ZONE_COLORS.length]
      drawPolygon(ctx, z.polygon, color, z.enabled ? 0.22 : 0.08)
      const [lx, ly] = z.polygon[0]
      ctx.fillStyle = color
      ctx.font = '12px system-ui, sans-serif'
      ctx.fillText(z.name, lx * width + 4, ly * height - 6)
    })

    // Draft polygon being drawn
    if (draftPoints.length > 0) {
      drawPolygon(ctx, draftPoints, '#e5e9f0', 0.15, draftPoints.length < 3)
      draftPoints.forEach(([x, y]) => {
        ctx.beginPath()
        ctx.arc(x * width, y * height, 4, 0, Math.PI * 2)
        ctx.fillStyle = '#22d3ee'
        ctx.fill()
      })
    }
  }

  useEffect(draw, [zones, draftPoints, width, height])

  function drawPolygon(ctx, points, color, alpha, openPath = false) {
    if (points.length < 2) return
    ctx.beginPath()
    points.forEach(([x, y], i) => {
      const px = x * width
      const py = y * height
      if (i === 0) ctx.moveTo(px, py)
      else ctx.lineTo(px, py)
    })
    if (!openPath) ctx.closePath()
    ctx.fillStyle = color + Math.round(alpha * 255).toString(16).padStart(2, '0')
    if (!openPath) ctx.fill()
    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.stroke()
  }

  function handleCanvasClick(e) {
    if (!drawing) return
    const rect = canvasRef.current.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height
    setDraftPoints((prev) => [...prev, [Number(x.toFixed(4)), Number(y.toFixed(4))]])
  }

  function startDrawing() {
    setDrawing(true)
    setDraftPoints([])
    setForm({ name: `Zone ${zones.length + 1}`, sensitivity: 0.5, dwell_seconds: 2 })
  }

  function cancelDrawing() {
    setDrawing(false)
    setDraftPoints([])
  }

  async function saveZone() {
    if (draftPoints.length < 3) return
    setError(null)
    try {
      await api.createZone({
        camera_id: cameraId,
        name: form.name || `Zone ${zones.length + 1}`,
        polygon: draftPoints,
        enabled: true,
        sensitivity: Number(form.sensitivity),
        dwell_seconds: Number(form.dwell_seconds),
      })
      setDrawing(false)
      setDraftPoints([])
      refreshZones()
    } catch (e) {
      setError(e.message)
    }
  }

  async function toggleZone(zone) {
    await api.updateZone(zone.id, { enabled: !zone.enabled })
    refreshZones()
  }

  async function patchZone(zone, field, value) {
    await api.updateZone(zone.id, { [field]: value })
    refreshZones()
  }

  async function deleteZone(zone) {
    setError(null)
    try {
      await api.deleteZone(zone.id)
      refreshZones()
    } catch (e) {
      setError(e.message)
    }
  }

  const selectedCamera = useMemo(() => cameras.find((c) => c.id === cameraId), [cameras, cameraId])

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-lg font-semibold">Zone Editor</h1>
          <p className="text-sm text-text-dim">Draw a polygon; events only fire inside enabled zones.</p>
        </div>
        <select
          value={cameraId ?? ''}
          onChange={(e) => {
            setCameraId(Number(e.target.value))
            cancelDrawing()
          }}
          className="bg-panel-2 border border-border rounded-lg text-sm px-3 py-1.5"
        >
          {cameras.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      {error && (
        <div className="mb-4 flex items-start gap-2 rounded-lg border border-danger/40 bg-danger/10 text-danger text-sm px-3 py-2">
          <span className="flex-1">{error}</span>
          <button onClick={() => setError(null)} className="text-danger/70 hover:text-danger">✕</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-5">
        <div>
          <div className="flex items-center gap-2 mb-2">
            {!drawing ? (
              <>
                <button
                  onClick={startDrawing}
                  className="text-xs px-3 py-1.5 rounded-lg bg-accent/15 border border-accent/40 text-accent-2 hover:bg-accent/25"
                >
                  + New Zone
                </button>
                <button
                  onClick={() => setSnapshotKey((k) => k + 1)}
                  className="text-xs px-3 py-1.5 rounded-lg border border-border text-text-dim hover:text-text"
                >
                  ↻ Refresh Frame
                </button>
              </>
            ) : (
              <>
                <span className="text-xs text-text-dim">
                  Click points on the frame · {draftPoints.length} placed (min 3)
                </span>
                <button
                  disabled={draftPoints.length < 3}
                  onClick={saveZone}
                  className="text-xs px-3 py-1.5 rounded-lg bg-success/15 border border-success/40 text-success disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  ✓ Finish & Save
                </button>
                <button
                  onClick={cancelDrawing}
                  className="text-xs px-3 py-1.5 rounded-lg border border-border text-text-dim hover:text-text"
                >
                  ✕ Cancel
                </button>
              </>
            )}
          </div>

          <div className="rounded-xl border border-border overflow-hidden bg-black inline-block">
            <canvas
              ref={canvasRef}
              onClick={handleCanvasClick}
              className={drawing ? 'cursor-crosshair' : 'cursor-default'}
              style={{ width, height }}
            />
          </div>

          {drawing && (
            <div className="mt-3 flex flex-wrap items-end gap-3 bg-panel border border-border rounded-lg p-3">
              <Field label="Name">
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="bg-panel-2 border border-border rounded px-2 py-1 text-sm w-40"
                />
              </Field>
              <Field label={`Sensitivity (${form.sensitivity})`}>
                <input
                  type="range" min="0.1" max="0.9" step="0.05"
                  value={form.sensitivity}
                  onChange={(e) => setForm({ ...form, sensitivity: e.target.value })}
                  className="w-32"
                />
              </Field>
              <Field label="Dwell (s)">
                <input
                  type="number" min="0" max="30"
                  value={form.dwell_seconds}
                  onChange={(e) => setForm({ ...form, dwell_seconds: e.target.value })}
                  className="bg-panel-2 border border-border rounded px-2 py-1 text-sm w-16"
                />
              </Field>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <div className="text-sm font-medium mb-1">Zones on {selectedCamera?.name}</div>
          {zones.length === 0 && (
            <div className="text-xs text-text-dim border border-dashed border-border rounded-lg p-4 text-center">
              No zones yet — draw one on the frame.
            </div>
          )}
          {zones.map((z, i) => (
            <div key={z.id} className="rounded-lg border border-border bg-panel p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: ZONE_COLORS[i % ZONE_COLORS.length] }} />
                  {z.name}
                </span>
                <label className="flex items-center gap-1.5 text-xs text-text-dim cursor-pointer">
                  <input type="checkbox" checked={z.enabled} onChange={() => toggleZone(z)} />
                  Enabled
                </label>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <label className="text-text-dim">
                  Sensitivity
                  <input
                    type="number" min="0.1" max="0.9" step="0.05"
                    defaultValue={z.sensitivity}
                    onBlur={(e) => patchZone(z, 'sensitivity', Number(e.target.value))}
                    className="mt-1 w-full bg-panel-2 border border-border rounded px-2 py-1 text-text"
                  />
                </label>
                <label className="text-text-dim">
                  Dwell (s)
                  <input
                    type="number" min="0" max="30"
                    defaultValue={z.dwell_seconds}
                    onBlur={(e) => patchZone(z, 'dwell_seconds', Number(e.target.value))}
                    className="mt-1 w-full bg-panel-2 border border-border rounded px-2 py-1 text-text"
                  />
                </label>
              </div>
              <button
                onClick={() => deleteZone(z)}
                className="text-[11px] text-danger/80 hover:text-danger mt-2"
              >
                Delete zone
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div>
      <div className="text-[11px] text-text-dim mb-1">{label}</div>
      {children}
    </div>
  )
}
