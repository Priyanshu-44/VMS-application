import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { formatClock, tsToEpoch } from '../lib/time'

const TYPE_COLORS = {
  intrusion: '#ef4444',
  loitering: '#f59e0b',
  motion: '#8b97a8',
}

const TRACK_HEIGHT = 92
const BASELINE_Y = TRACK_HEIGHT - 26

/**
 * The demo's centerpiece (PRD Section 13): a horizontal track spanning the
 * recording window, with colored event markers, hover-to-preview, and
 * click-to-seek. Canvas-rendered for crisp custom markers at any density;
 * the hover thumbnail is a plain positioned <img> overlay (simpler and more
 * reliable than drawing bitmaps into the canvas).
 */
export default function Timeline({ events, windowStart, windowEnd, currentTime, onSeek }) {
  const canvasRef = useRef(null)
  const containerRef = useRef(null)
  const [hover, setHover] = useState(null)
  const [width, setWidth] = useState(800)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver((entries) => setWidth(entries[0].contentRect.width))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const span = Math.max(windowEnd - windowStart, 1)
  const xForTs = (ts) => ((ts - windowStart) / span) * width

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || width === 0) return
    const dpr = window.devicePixelRatio || 1
    canvas.width = width * dpr
    canvas.height = TRACK_HEIGHT * dpr
    canvas.style.width = `${width}px`
    canvas.style.height = `${TRACK_HEIGHT}px`
    const ctx = canvas.getContext('2d')
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, width, TRACK_HEIGHT)

    // Baseline track
    ctx.strokeStyle = '#232d3d'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(4, BASELINE_Y)
    ctx.lineTo(width - 4, BASELINE_Y)
    ctx.stroke()

    // Gridlines + time labels
    const tickCount = Math.max(2, Math.min(8, Math.floor(width / 130)))
    ctx.font = '11px system-ui, sans-serif'
    ctx.textAlign = 'center'
    for (let i = 0; i <= tickCount; i++) {
      const ts = windowStart + (span * i) / tickCount
      const x = xForTs(ts)
      ctx.strokeStyle = '#1a2230'
      ctx.beginPath()
      ctx.moveTo(x, 4)
      ctx.lineTo(x, BASELINE_Y)
      ctx.stroke()
      ctx.fillStyle = '#8b97a8'
      ctx.fillText(formatClock(ts), Math.min(Math.max(x, 24), width - 24), TRACK_HEIGHT - 8)
    }

    // Playhead
    if (currentTime != null && currentTime >= windowStart && currentTime <= windowEnd) {
      const x = xForTs(currentTime)
      ctx.strokeStyle = '#22d3ee'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, BASELINE_Y)
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(x - 5, 0)
      ctx.lineTo(x + 5, 0)
      ctx.lineTo(x, 8)
      ctx.closePath()
      ctx.fillStyle = '#22d3ee'
      ctx.fill()
    }

    // Event markers
    for (const ev of events) {
      const ts = tsToEpoch(ev.ts)
      if (ts == null || ts < windowStart || ts > windowEnd) continue
      const x = xForTs(ts)
      const color = TYPE_COLORS[ev.type] || TYPE_COLORS.motion
      const isHovered = hover?.event?.id === ev.id

      ctx.beginPath()
      ctx.moveTo(x, BASELINE_Y)
      ctx.lineTo(x, BASELINE_Y - 12)
      ctx.strokeStyle = color
      ctx.lineWidth = isHovered ? 2.5 : 1.5
      ctx.stroke()

      ctx.beginPath()
      ctx.arc(x, BASELINE_Y - 12, isHovered ? 6.5 : 5, 0, Math.PI * 2)
      ctx.fillStyle = color
      ctx.fill()
      ctx.lineWidth = 1.5
      ctx.strokeStyle = '#0b0f14'
      ctx.stroke()
    }
  }, [events, width, windowStart, windowEnd, currentTime, hover])

  function nearestEvent(x) {
    let nearest = null
    let nearestDist = 9
    for (const ev of events) {
      const ts = tsToEpoch(ev.ts)
      if (ts == null) continue
      const dist = Math.abs(xForTs(ts) - x)
      if (dist < nearestDist) {
        nearestDist = dist
        nearest = ev
      }
    }
    return nearest
  }

  function handleMouseMove(e) {
    const rect = canvasRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const found = nearestEvent(x)
    setHover(found ? { event: found, x } : null)
  }

  function handleClick(e) {
    const rect = canvasRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const found = nearestEvent(x)
    const ts = found ? tsToEpoch(found.ts) : windowStart + (x / width) * span
    onSeek(ts, found)
  }

  return (
    <div ref={containerRef} className="relative w-full select-none">
      <canvas
        ref={canvasRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHover(null)}
        onClick={handleClick}
        className="cursor-pointer w-full block"
      />
      {events.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center text-xs text-text-dim pointer-events-none">
          No events in this window
        </div>
      )}
      {hover && (
        <div
          className="absolute z-10 bg-panel border border-border rounded-lg shadow-2xl p-2 pointer-events-none"
          style={{
            left: Math.min(Math.max(hover.x - 64, 4), Math.max(width - 136, 4)),
            top: -108,
            width: 128,
          }}
        >
          <img
            src={api.thumbnailUrl(hover.event.id)}
            alt=""
            className="w-full h-20 object-cover rounded bg-panel-2"
          />
          <div className="text-[11px] mt-1 flex items-center gap-1">
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: TYPE_COLORS[hover.event.type] || TYPE_COLORS.motion }}
            />
            <span className="font-medium capitalize">{hover.event.type}</span>
          </div>
          <div className="text-[10px] text-text-dim">
            {hover.event.object_class} · {Math.round((hover.event.confidence || 0) * 100)}%
          </div>
          <div className="text-[10px] text-text-dim">{formatClock(tsToEpoch(hover.event.ts))}</div>
        </div>
      )}
    </div>
  )
}
