import { useEffect, useRef } from 'react'
import { api } from '../lib/api'

/** Subscribes to /ws/events and calls onEvent(eventDict) for every push.
 * Auto-reconnects with a short backoff if the connection drops. */
export function useEventsSocket(onEvent) {
  const onEventRef = useRef(onEvent)
  onEventRef.current = onEvent

  useEffect(() => {
    let ws
    let closedByUs = false
    let retryTimer

    function connect() {
      ws = new WebSocket(`${api.wsBase}/ws/events`)
      ws.onmessage = (msg) => {
        try {
          const parsed = JSON.parse(msg.data)
          if (parsed.kind === 'event') onEventRef.current?.(parsed.data)
        } catch {
          // ignore malformed frames
        }
      }
      ws.onclose = () => {
        if (!closedByUs) retryTimer = setTimeout(connect, 2000)
      }
      ws.onerror = () => ws.close()
    }

    connect()
    return () => {
      closedByUs = true
      clearTimeout(retryTimer)
      ws?.close()
    }
  }, [])
}
