import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import CameraTile from '../components/CameraTile'
import { useEventsSocket } from '../hooks/useEventsSocket'
import { api } from '../lib/api'

const ALERT_FLASH_MS = 6000

export default function LiveGrid() {
  const [cameras, setCameras] = useState([])
  const [alerting, setAlerting] = useState({}) // camera_id -> timestamp
  const navigate = useNavigate()

  useEffect(() => {
    api.listCameras().then(setCameras).catch(console.error)
  }, [])

  useEventsSocket((event) => {
    setAlerting((prev) => ({ ...prev, [event.camera_id]: Date.now() }))
  })

  // Sweep expired alert flashes
  useEffect(() => {
    const id = setInterval(() => {
      setAlerting((prev) => {
        const now = Date.now()
        const next = {}
        for (const [camId, ts] of Object.entries(prev)) {
          if (now - ts < ALERT_FLASH_MS) next[camId] = ts
        }
        return next
      })
    }, 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-lg font-semibold">Live Grid</h1>
          <p className="text-sm text-text-dim">
            {cameras.length} camera{cameras.length !== 1 ? 's' : ''} ·{' '}
            {cameras.filter((c) => c.status === 'online').length} online
          </p>
        </div>
      </div>

      {cameras.length === 0 ? (
        <div className="text-text-dim text-sm">No cameras registered yet.</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {cameras.map((cam) => (
            <CameraTile
              key={cam.id}
              camera={cam}
              isAlerting={!!alerting[cam.id]}
              onClick={() => navigate(`/playback/${cam.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
