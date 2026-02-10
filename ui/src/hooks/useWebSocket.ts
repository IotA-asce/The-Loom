// React hook for WebSocket connection
// Provides reactive access to WebSocket state and messaging

import { useCallback, useEffect, useRef, useState } from 'react'
import { wsClient, WebSocketMessage, ConnectionState } from '../api/websocket'

export interface UseWebSocketReturn {
  /** Whether the WebSocket is currently connected */
  isConnected: boolean
  /** Send a message through the WebSocket */
  send: (message: object) => void
  /** The last message received */
  lastMessage: WebSocketMessage | null
  /** Current connection state */
  connectionState: ConnectionState
  /** Manually reconnect to the WebSocket */
  reconnect: () => void
  /** Manually disconnect from the WebSocket */
  disconnect: () => void
}

/**
 * React hook for WebSocket connectivity
 *
 * Features:
 * - Auto-connect on mount, disconnect on unmount
 * - Tracks connection state reactively
 * - Provides last received message
 * - Handles reconnection state
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { isConnected, send, lastMessage } = useWebSocket()
 *
 *   useEffect(() => {
 *     if (lastMessage?.type === 'generation_progress') {
 *       console.log('Progress:', lastMessage.payload)
 *     }
 *   }, [lastMessage])
 *
 *   return (
 *     <button
 *       onClick={() => send({ type: 'subscribe', job_id: '123' })}
 *       disabled={!isConnected}
 *     >
 *       Subscribe to Job
 *     </button>
 *   )
 * }
 * ```
 */
export function useWebSocket(): UseWebSocketReturn {
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const unsubscribeRef = useRef<(() => void) | null>(null)

  // Subscribe to connection state changes
  useEffect(() => {
    const unsubscribe = wsClient.onConnectionStateChange((state) => {
      setConnectionState(state)
    })

    return () => {
      unsubscribe()
    }
  }, [])

  // Subscribe to all messages
  useEffect(() => {
    // Subscribe to wildcard to catch all messages
    // Note: This relies on the '*' subscription feature in WebSocketClient
    const unsubscribe = wsClient.subscribe('*' as WebSocketMessage['type'], (message) => {
      setLastMessage(message)
    })

    unsubscribeRef.current = unsubscribe

    return () => {
      unsubscribe()
      unsubscribeRef.current = null
    }
  }, [])

  // Auto-connect on mount
  useEffect(() => {
    wsClient.connect()

    return () => {
      // Note: We don't disconnect on unmount to allow
      // other components to maintain the connection
      // The singleton wsClient manages connection lifecycle
    }
  }, [])

  const send = useCallback((message: object): void => {
    wsClient.send(message as WebSocketMessage)
  }, [])

  const reconnect = useCallback((): void => {
    wsClient.disconnect()
    wsClient.connect()
  }, [])

  const disconnect = useCallback((): void => {
    wsClient.disconnect()
  }, [])

  return {
    isConnected: connectionState === 'connected',
    send,
    lastMessage,
    connectionState,
    reconnect,
    disconnect,
  }
}

export default useWebSocket
