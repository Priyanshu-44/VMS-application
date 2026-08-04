import { useState } from 'react'
import { api } from '../lib/api'

export default function CameraTile({ camera, isAlerting, onClick }) {
  const [errored, setErrored] = useState(false)

  return (
    <button
      onClick={onClick}
      className={`group relative aspect-video rounded-xl overflow-hidden border text-left transition-all
        ${isAlerting ? 'border-danger shadow-[0_0_0_3px_rgba(239,68,68,0.25)] animate-pulse' : 'border-border hover:border-accent/50'}
        bg-panel-2`}
    >
      {!errored ? (
        <img
          src={api.streamUrl(camera.id)}
          alt={camera.name}
          className="w-full h-full object-cover"
          onError={() => setErrored(true)}
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center text-text-dim text-sm">
          Feed unavailable
        </div>
      )}

      <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent px-3 pt-6 pb-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-white truncate">{camera.name}</span>
          <span className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${camera.status === 'online' ? 'bg-success' : 'bg-text-dim'}`}
            />
            <span className="text-[11px] text-white/70 capitalize">{camera.status}</span>
          </span>
        </div>
        {camera.location && (
          <div className="text-[11px] text-white/50 truncate">{camera.location}</div>
        )}
      </div>

      {isAlerting && (
        <div className="absolute top-2 right-2 bg-danger text-white text-[10px] font-semibold px-2 py-0.5 rounded-full">
          ALERT
        </div>
      )}
    </button>
  )
}
