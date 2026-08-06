import { useEffect, useState } from 'react'
import {
  Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { api } from '../lib/api'

const REFRESH_MS = 8000

export default function AnalyticsPage() {
  const [data, setData] = useState(null)

  useEffect(() => {
    const load = () => api.analytics().then(setData).catch(console.error)
    load()
    const id = setInterval(load, REFRESH_MS)
    return () => clearInterval(id)
  }, [])

  if (!data) return <div className="p-6 text-text-dim">Loading analytics…</div>

  const { confirmed_vs_false: cf, detections_per_hour, detections_per_zone } = data
  const hourData = detections_per_hour.map((d) => ({ hour: d.hour.slice(11, 16), count: d.count }))
  const maxZoneCount = Math.max(1, ...detections_per_zone.map((z) => z.count))

  return (
    <div className="p-6">
      <h1 className="text-lg font-semibold mb-1">Analytics</h1>
      <p className="text-sm text-text-dim mb-5">False-alarm suppression, quantified</p>

      {/* The pitch's headline number */}
      <div className="rounded-xl border border-accent/30 bg-gradient-to-br from-accent/10 to-transparent p-5 mb-6">
        <div className="flex flex-wrap items-end gap-x-10 gap-y-4">
          <div>
            <div className="text-xs text-text-dim mb-1">False-alarm reduction</div>
            <div className="text-4xl font-bold text-accent-2">
              {cf.motion_triggers > 0 ? `${cf.reduction_pct}%` : '—'}
            </div>
            <div className="text-[11px] text-text-dim mt-1">
              vs. raw motion detection since this session started
            </div>
          </div>
          <Stat label="Motion triggers" value={cf.motion_triggers} hint="what raw motion detection would fire on" />
          <Stat label="Confirmed events" value={cf.confirmed_events} hint="survived zone + class + dwell filters" />
          <Stat label="Suppressed" value={cf.suppressed} hint="noise the pipeline filtered out" accent="success" />
        </div>
        {cf.motion_triggers === 0 && (
          <div className="text-xs text-text-dim mt-3">
            No motion observed yet this session — numbers populate as cameras run.
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="rounded-xl border border-border bg-panel p-4">
          <div className="text-sm font-medium mb-3">Detections per hour</div>
          {hourData.length === 0 ? (
            <EmptyChart />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={hourData}>
                <CartesianGrid stroke="#1a2230" vertical={false} />
                <XAxis dataKey="hour" stroke="#8b97a8" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#8b97a8" fontSize={11} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ background: '#121821', border: '1px solid #232d3d', borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: '#e5e9f0' }}
                  cursor={{ fill: 'rgba(59,130,246,0.08)' }}
                />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} maxBarSize={56} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="rounded-xl border border-border bg-panel p-4">
          <div className="text-sm font-medium mb-3">Detections per zone</div>
          {detections_per_zone.length === 0 ? (
            <EmptyChart />
          ) : (
            <div className="space-y-3">
              {detections_per_zone.map((z) => (
                <div key={z.zone_id}>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="truncate">
                      {z.zone_name} <span className="text-text-dim">· {z.camera_name}</span>
                    </span>
                    <span className="text-text-dim shrink-0 ml-2">{z.count}</span>
                  </div>
                  <div className="h-2 rounded-full bg-panel-2 overflow-hidden">
                    <div
                      className="h-full bg-accent-2 rounded-full"
                      style={{ width: `${(z.count / maxZoneCount) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Stat({ label, value, hint, accent }) {
  return (
    <div>
      <div className="text-xs text-text-dim mb-1">{label}</div>
      <div className={`text-2xl font-semibold ${accent === 'success' ? 'text-success' : ''}`}>{value}</div>
      <div className="text-[11px] text-text-dim mt-1 max-w-[160px]">{hint}</div>
    </div>
  )
}

function EmptyChart() {
  return <div className="h-[220px] flex items-center justify-center text-sm text-text-dim">No data yet</div>
}
