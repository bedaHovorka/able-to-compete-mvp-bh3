import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuthStore } from '../store/authStore'

const MIN_RECONNECT_DELAY_MS = 1000
const MAX_RECONNECT_DELAY_MS = 30000

/** Minimum shape of every WebSocket message sent by the backend. */
export interface WsMessage {
  type: string
  data: Record<string, unknown>
}

export interface UseWebSocketReturn {
  connected: boolean
}

/**
 * Generic WebSocket hook with auto-reconnect and JWT token passing.
 *
 * @param path - WebSocket path relative to the current host (e.g. `/ws/monitoring`)
 * @param onMessage - Callback invoked with each parsed JSON message object
 */
export function useWebSocket(
  path: string,
  onMessage: (msg: WsMessage) => void,
): UseWebSocketReturn {
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectDelayRef = useRef(MIN_RECONNECT_DELAY_MS)
  const unmountedRef = useRef(false)

  // Keep the latest callback in a ref so reconnects always use the current version
  const onMessageRef = useRef(onMessage)
  useEffect(() => {
    onMessageRef.current = onMessage
  })

  const connect = useCallback(() => {
    if (unmountedRef.current) return

    const token = useAuthStore.getState().token
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const baseUrl = `${wsProtocol}//${window.location.host}${path}`
    const url = token ? `${baseUrl}?token=${encodeURIComponent(token)}` : baseUrl

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      if (unmountedRef.current) {
        ws.close()
        return
      }
      setConnected(true)
      reconnectDelayRef.current = MIN_RECONNECT_DELAY_MS
    }

    ws.onmessage = (event: MessageEvent) => {
      try {
        const msg = JSON.parse(event.data as string) as WsMessage
        if (typeof msg.type === 'string') {
          onMessageRef.current(msg)
        }
      } catch {
        // Ignore non-JSON frames (e.g. plain-text pong)
      }
    }

    ws.onclose = () => {
      setConnected(false)
      wsRef.current = null
      if (!unmountedRef.current) {
        if (reconnectTimerRef.current !== null) {
          clearTimeout(reconnectTimerRef.current)
        }
        reconnectTimerRef.current = setTimeout(() => {
          reconnectDelayRef.current = Math.min(
            reconnectDelayRef.current * 2,
            MAX_RECONNECT_DELAY_MS,
          )
          connect()
        }, reconnectDelayRef.current)
      }
    }

    ws.onerror = () => {
      // onclose will fire after onerror, which triggers the reconnect logic
      ws.close()
    }
  }, [path])

  useEffect(() => {
    unmountedRef.current = false
    connect()

    return () => {
      unmountedRef.current = true
      if (reconnectTimerRef.current !== null) {
        clearTimeout(reconnectTimerRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  return { connected }
}
