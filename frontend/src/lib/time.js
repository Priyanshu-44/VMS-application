/** SQLite CURRENT_TIMESTAMP / datetime() produce "YYYY-MM-DD HH:MM:SS" in UTC
 * with no timezone marker — treat it as UTC explicitly so the browser
 * doesn't interpret it as local time. */
export function tsToEpoch(sqliteTs) {
  if (!sqliteTs) return null
  return new Date(sqliteTs.replace(' ', 'T') + 'Z').getTime() / 1000
}

export function formatClock(epochSeconds) {
  if (epochSeconds == null) return ''
  return new Date(epochSeconds * 1000).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function formatRelative(epochSeconds) {
  const diff = Date.now() / 1000 - epochSeconds
  if (diff < 60) return `${Math.max(0, Math.round(diff))}s ago`
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`
  return `${Math.round(diff / 3600)}h ago`
}
