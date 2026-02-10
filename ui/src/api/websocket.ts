// WebSocket Client for The Loom UI
// Provides real-time bidirectional communication with the backend

// ==================== TYPES ====================

export type ConnectionState = 'connected' | 'disconnected' | 'reconnecting'

export type WebSocketMessageType =
  | 'generation_progress'
  | 'job_complete'
  | 'error'
  | 'ping'
  | 'pong'
  | 'subscribe'
  | 'unsubscribe'

export interface WebSocketMessage {
  type: WebSocketMessageType
  job_id?: string
  payload?: unknown
  timestamp?: number
}

export interface GenerationProgressPayload {
  job_id: string
  progress: number
  status: string
  eta?: number
  message?: string
}

export interface JobCompletePayload {
  job_id: string
  result: unknown
  duration_ms: number
}

export interface ErrorPayload {
  job_id?: string
  code: string
  message: string
  details?: unknown
}

export type MessageHandler = (message: WebSocketMessage) => void
export type ConnectionStateHandler = (state: ConnectionState) => void

// ==================== CONFIGURATION ====================

interface WebSocketClientConfig {
  url: string
  reconnectInterval: number
  maxReconnectInterval: number
  reconnectDecay: number
  maxReconnectAttempts: number
  heartbeatInterval: number
  heartbeatTimeout: number
}

const getDefaultWsUrl = (): string => {
  // Check for Vite environment variable
  const viteEnv = (import.meta as unknown as { env?: { VITE_WS_URL?: string } }).env
  return viteEnv?.VITE_WS_URL || 'ws://localhost:8000/ws'
}

const DEFAULT_CONFIG: WebSocketClientConfig = {
  url: getDefaultWsUrl(),
  reconnectInterval: 1000,
  maxReconnectInterval: 30000,
  reconnectDecay: 1.5,
  maxReconnectAttempts: 10,
  heartbeatInterval: 30000,
  heartbeatTimeout: 5000,
}

// ==================== WEBSOCKET CLIENT ====================

export class WebSocketClient {
  private ws: WebSocket | null = null
  private config: WebSocketClientConfig
  private connectionState: ConnectionState = 'disconnected'
  private reconnectAttempts = 0
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private heartbeatTimeoutTimer: ReturnType<typeof setTimeout> | null = null
  private subscriptions = new Map<string, Set<MessageHandler>>()
  private stateHandlers = new Set<ConnectionStateHandler>()
  private messageQueue: WebSocketMessage[] = []
  private isManualClose = false

  constructor(config: Partial<WebSocketClientConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  // ==================== CONNECTION MANAGEMENT ====================

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected')
      return
    }

    if (this.ws?.readyState === WebSocket.CONNECTING) {
      console.log('[WebSocket] Already connecting')
      return
    }

    this.isManualClose = false
    this.setConnectionState('reconnecting')

    try {
      console.log(`[WebSocket] Connecting to ${this.config.url}`)
      this.ws = new WebSocket(this.config.url)

      this.ws.onopen = this.handleOpen.bind(this)
      this.ws.onclose = this.handleClose.bind(this)
      this.ws.onerror = this.handleError.bind(this)
      this.ws.onmessage = this.handleMessage.bind(this)
    } catch (error) {
      console.error('[WebSocket] Connection error:', error)
      this.handleError(error as Event)
    }
  }

  disconnect(): void {
    this.isManualClose = true
    this.clearTimers()

    if (this.ws) {
      console.log('[WebSocket] Disconnecting...')
      this.ws.close(1000, 'Manual disconnect')
      this.ws = null
    }

    this.reconnectAttempts = 0
    this.setConnectionState('disconnected')
  }

  private reconnect(): void {
    if (this.isManualClose) {
      return
    }

    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnection attempts reached')
      this.setConnectionState('disconnected')
      return
    }

    this.reconnectAttempts++
    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(this.config.reconnectDecay, this.reconnectAttempts - 1),
      this.config.maxReconnectInterval
    )

    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`)
    this.setConnectionState('reconnecting')

    this.reconnectTimer = setTimeout(() => {
      this.connect()
    }, delay)
  }

  // ==================== EVENT HANDLERS ====================

  private handleOpen(): void {
    console.log('[WebSocket] Connected')
    this.reconnectAttempts = 0
    this.setConnectionState('connected')
    this.startHeartbeat()
    this.flushMessageQueue()
  }

  private handleClose(event: CloseEvent): void {
    console.log(`[WebSocket] Closed: ${event.code} - ${event.reason}`)
    this.clearTimers()

    if (!this.isManualClose) {
      // Reconnect on abnormal closure codes
      const shouldReconnect = event.code !== 1000 && event.code !== 1001
      if (shouldReconnect) {
        this.reconnect()
      } else {
        this.setConnectionState('disconnected')
      }
    }
  }

  private handleError(event: Event): void {
    console.error('[WebSocket] Error:', event)
    // Error handling is done in handleClose
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message = JSON.parse(event.data) as WebSocketMessage
      message.timestamp = Date.now()

      // Handle ping/pong for heartbeat
      if (message.type === 'ping') {
        this.send({ type: 'pong', timestamp: Date.now() })
        return
      }

      if (message.type === 'pong') {
        this.clearHeartbeatTimeout()
        return
      }

      // Notify subscribers
      this.notifySubscribers(message)
    } catch (error) {
      console.error('[WebSocket] Failed to parse message:', error)
    }
  }

  // ==================== HEARTBEAT ====================

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping', timestamp: Date.now() })

        // Set timeout for pong response
        this.heartbeatTimeoutTimer = setTimeout(() => {
          console.warn('[WebSocket] Heartbeat timeout - connection may be stale')
          this.ws?.close(4000, 'Heartbeat timeout')
        }, this.config.heartbeatTimeout)
      }
    }, this.config.heartbeatInterval)
  }

  private clearHeartbeatTimeout(): void {
    if (this.heartbeatTimeoutTimer) {
      clearTimeout(this.heartbeatTimeoutTimer)
      this.heartbeatTimeoutTimer = null
    }
  }

  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
    this.clearHeartbeatTimeout()
  }

  // ==================== MESSAGE HANDLING ====================

  send(message: WebSocketMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      // Queue message if not connected
      this.messageQueue.push(message)
      console.warn('[WebSocket] Message queued - not connected')
    }
  }

  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift()
      if (message) {
        this.send(message)
      }
    }
  }

  // ==================== SUBSCRIPTION MANAGEMENT ====================

  subscribe(type: WebSocketMessageType, handler: MessageHandler): () => void {
    if (!this.subscriptions.has(type)) {
      this.subscriptions.set(type, new Set())
    }

    const handlers = this.subscriptions.get(type)!
    handlers.add(handler)

    // Return unsubscribe function
    return () => {
      handlers.delete(handler)
      if (handlers.size === 0) {
        this.subscriptions.delete(type)
      }
    }
  }

  subscribeToJob(jobId: string, handler: MessageHandler): () => void {
    // Subscribe to all messages related to a specific job
    const unsubscribeProgress = this.subscribe('generation_progress', (msg) => {
      if (msg.job_id === jobId) {
        handler(msg)
      }
    })

    const unsubscribeComplete = this.subscribe('job_complete', (msg) => {
      if (msg.job_id === jobId) {
        handler(msg)
      }
    })

    const unsubscribeError = this.subscribe('error', (msg) => {
      if (msg.job_id === jobId) {
        handler(msg)
      }
    })

    // Send subscription message to server
    this.send({ type: 'subscribe', job_id: jobId, payload: { job_id: jobId } })

    // Return combined unsubscribe function
    return () => {
      unsubscribeProgress()
      unsubscribeComplete()
      unsubscribeError()
      this.send({ type: 'unsubscribe', job_id: jobId, payload: { job_id: jobId } })
    }
  }

  private notifySubscribers(message: WebSocketMessage): void {
    // Notify type-specific subscribers
    const handlers = this.subscriptions.get(message.type)
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(message)
        } catch (error) {
          console.error('[WebSocket] Error in message handler:', error)
        }
      })
    }

    // Notify wildcard subscribers (if any)
    const wildcardHandlers = this.subscriptions.get('*' as WebSocketMessageType)
    if (wildcardHandlers) {
      wildcardHandlers.forEach((handler) => {
        try {
          handler(message)
        } catch (error) {
          console.error('[WebSocket] Error in wildcard handler:', error)
        }
      })
    }
  }

  // ==================== STATE MANAGEMENT ====================

  private setConnectionState(state: ConnectionState): void {
    if (this.connectionState !== state) {
      this.connectionState = state
      this.stateHandlers.forEach((handler) => {
        try {
          handler(state)
        } catch (error) {
          console.error('[WebSocket] Error in state handler:', error)
        }
      })
    }
  }

  onConnectionStateChange(handler: ConnectionStateHandler): () => void {
    this.stateHandlers.add(handler)
    // Immediately call with current state
    handler(this.connectionState)

    return () => {
      this.stateHandlers.delete(handler)
    }
  }

  getConnectionState(): ConnectionState {
    return this.connectionState
  }

  isConnected(): boolean {
    return this.connectionState === 'connected'
  }

  // ==================== UTILITY ====================

  getReconnectAttempts(): number {
    return this.reconnectAttempts
  }

  getQueuedMessageCount(): number {
    return this.messageQueue.length
  }

  clearQueue(): void {
    this.messageQueue = []
  }
}

// ==================== EXPORTED INSTANCES ====================

export const wsClient = new WebSocketClient()

export default wsClient
