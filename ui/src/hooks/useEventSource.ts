// React hook for Server-Sent Events (SSE)
// Provides fallback for real-time updates when WebSocket is not available

import { useCallback, useEffect, useRef, useState } from 'react'

export interface UseEventSourceReturn {
  /** The last data received from the event source */
  data: unknown | null
  /** Any error that occurred */
  error: Error | null
  /** Whether the connection is currently open */
  isConnected: boolean
  /** Manually close the connection */
  close: () => void
  /** Manually reconnect to the event source */
  reconnect: () => void
}

export interface UseEventSourceOptions {
  /** Auto-connect on mount (default: true) */
  autoConnect?: boolean
  /** Reconnect on error (default: true) */
  autoReconnect?: boolean
  /** Initial reconnect delay in ms (default: 1000) */
  reconnectInterval?: number
  /** Maximum reconnect delay in ms (default: 30000) */
  maxReconnectInterval?: number
  /** Exponential backoff multiplier (default: 1.5) */
  reconnectDecay?: number
  /** Maximum number of reconnection attempts (default: 10) */
  maxReconnectAttempts?: number
  /** Event type to listen for (default: 'message') */
  eventType?: string
  /** Custom headers to send with the request */
  headers?: Record<string, string>
  /** Called when the connection opens */
  onOpen?: () => void
  /** Called when the connection closes */
  onClose?: () => void
  /** Called when an error occurs */
  onError?: (error: Event) => void
  /** Called when a message is received */
  onMessage?: (data: unknown) => void
}

/**
 * React hook for Server-Sent Events (SSE)
 *
 * Features:
 * - Auto-connect on mount with configurable options
 * - Auto-reconnect on error with exponential backoff
 * - Type-safe data handling
 * - Connection state tracking
 *
 * @example
 * ```tsx
 * function ProgressComponent({ jobId }: { jobId: string }) {
 *   const { data, error, isConnected } = useEventSource(
 *     `/api/jobs/${jobId}/progress`,
 *     { eventType: 'progress' }
 *   )
 *
 *   if (error) return <div>Error: {error.message}</div>
 *
 *   return (
 *     <div>
 *       <span>{isConnected ? '●' : '○'}</span>
 *       <pre>{JSON.stringify(data, null, 2)}</pre>
 *     </div>
 *   )
 * }
 * ```
 */
export function useEventSource(
  url: string,
  options: UseEventSourceOptions = {}
): UseEventSourceReturn {
  const {
    autoConnect = true,
    autoReconnect = true,
    reconnectInterval = 1000,
    maxReconnectInterval = 30000,
    reconnectDecay = 1.5,
    maxReconnectAttempts = 10,
    eventType = 'message',
    onOpen,
    onClose,
    onError,
    onMessage,
  } = options

  const [data, setData] = useState<unknown | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isManualCloseRef = useRef(false)

  const close = useCallback((): void => {
    isManualCloseRef.current = true

    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }

    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }

    reconnectAttemptsRef.current = 0
    setIsConnected(false)
    onClose?.()
  }, [onClose])

  const connect = useCallback((): void => {
    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    isManualCloseRef.current = false

    try {
      const es = new EventSource(url)
      eventSourceRef.current = es

      es.onopen = () => {
        console.log(`[SSE] Connected to ${url}`)
        reconnectAttemptsRef.current = 0
        setIsConnected(true)
        setError(null)
        onOpen?.()
      }

      es.onerror = (event) => {
        console.error(`[SSE] Error:`, event)
        setIsConnected(false)
        onError?.(event)

        // Handle reconnection
        if (!isManualCloseRef.current && autoReconnect) {
          if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
            setError(new Error('Max reconnection attempts reached'))
            return
          }

          reconnectAttemptsRef.current++
          const delay = Math.min(
            reconnectInterval * Math.pow(reconnectDecay, reconnectAttemptsRef.current - 1),
            maxReconnectInterval
          )

          console.log(`[SSE] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`)

          if (reconnectTimerRef.current) {
            clearTimeout(reconnectTimerRef.current)
          }

          reconnectTimerRef.current = setTimeout(() => {
            connect()
          }, delay)
        }
      }

      // Handle specific event type
      es.addEventListener(eventType, (event) => {
        try {
          const parsedData = JSON.parse(event.data)
          setData(parsedData)
          onMessage?.(parsedData)
        } catch {
          // If not JSON, use raw data
          setData(event.data)
          onMessage?.(event.data)
        }
      })

      // Also handle default 'message' events if different from eventType
      if (eventType !== 'message') {
        es.addEventListener('message', (event) => {
          try {
            const parsedData = JSON.parse(event.data)
            setData(parsedData)
            onMessage?.(parsedData)
          } catch {
            setData(event.data)
            onMessage?.(event.data)
          }
        })
      }
    } catch (err) {
      console.error('[SSE] Failed to create EventSource:', err)
      setError(err instanceof Error ? err : new Error('Failed to connect'))
      setIsConnected(false)
    }
  }, [
    url,
    eventType,
    autoReconnect,
    reconnectInterval,
    maxReconnectInterval,
    reconnectDecay,
    maxReconnectAttempts,
    onOpen,
    onError,
    onMessage,
  ])

  const reconnect = useCallback((): void => {
    close()
    reconnectAttemptsRef.current = 0
    connect()
  }, [close, connect])

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    return () => {
      close()
    }
  }, [autoConnect, connect, close])

  // Reconnect when URL changes
  useEffect(() => {
    if (autoConnect && eventSourceRef.current) {
      reconnect()
    }
  }, [url, autoConnect, reconnect])

  return {
    data,
    error,
    isConnected,
    close,
    reconnect,
  }
}

export default useEventSource
