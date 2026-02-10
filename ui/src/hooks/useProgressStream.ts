// React hook for progress streaming
// Works with WebSocket primarily, with SSE fallback

import { useCallback, useEffect, useRef, useState } from 'react'
import { wsClient, WebSocketMessage, GenerationProgressPayload, JobCompletePayload, ErrorPayload } from '../api/websocket'
import { useEventSource, UseEventSourceOptions } from './useEventSource'

export interface ProgressState {
  /** Progress percentage (0-100) */
  progress: number
  /** Current status message */
  status: string
  /** Estimated time remaining in seconds */
  eta: number
  /** Whether the job is complete */
  isComplete: boolean
  /** Any error that occurred */
  error: Error | null
  /** Additional progress details */
  details?: unknown
}

export interface UseProgressStreamOptions {
  /** Use SSE fallback instead of WebSocket */
  useSSE?: boolean
  /** SSE URL template (use {jobId} placeholder) */
  sseUrlTemplate?: string
  /** Additional SSE options */
  sseOptions?: Omit<UseEventSourceOptions, 'autoConnect' | 'onMessage' | 'onError'>
  /** Called when progress updates */
  onProgress?: (progress: number, state: ProgressState) => void
  /** Called when job completes */
  onComplete?: (result: unknown) => void
  /** Called when an error occurs */
  onError?: (error: Error) => void
}

const DEFAULT_SSE_URL_TEMPLATE = '/api/jobs/{jobId}/progress'

const initialState: ProgressState = {
  progress: 0,
  status: 'pending',
  eta: 0,
  isComplete: false,
  error: null,
}

/**
 * React hook for streaming progress updates
 *
 * Features:
 * - Primary WebSocket support with automatic subscription
 * - SSE fallback for environments without WebSocket
 * - Progress tracking (0-100), ETA, status messages
 * - Completion and error handling
 * - Auto-cleanup on unmount
 *
 * @example
 * ```tsx
 * function GenerationProgress({ jobId }: { jobId: string }) {
 *   const { progress, status, eta, isComplete, error } = useProgressStream(jobId)
 *
 *   if (error) {
 *     return <div className="error">Error: {error.message}</div>
 *   }
 *
 *   return (
 *     <div className="progress-container">
 *       <div className="progress-bar" style={{ width: `${progress}%` }} />
 *       <div className="progress-info">
 *         <span>{status}</span>
 *         {!isComplete && eta > 0 && <span>ETA: {eta}s</span>}
 *       </div>
 *       {isComplete && <div className="complete">✓ Complete!</div>}
 *     </div>
 *   )
 * }
 * ```
 */
export function useProgressStream(
  jobId: string,
  options: UseProgressStreamOptions = {}
): ProgressState {
  const {
    useSSE = false,
    sseUrlTemplate = DEFAULT_SSE_URL_TEMPLATE,
    sseOptions,
    onProgress,
    onComplete,
    onError,
  } = options

  const [state, setState] = useState<ProgressState>(initialState)
  const unsubscribeRef = useRef<(() => void) | null>(null)
  const hasCompletedRef = useRef(false)

  // Construct SSE URL
  const sseUrl = useSSE ? sseUrlTemplate.replace('{jobId}', jobId) : null

  // Handle SSE data
  const handleSSEData = useCallback((data: unknown) => {
    if (typeof data !== 'object' || data === null) return

    const msg = data as Record<string, unknown>

    switch (msg.type) {
      case 'generation_progress': {
        const payload = msg.payload as GenerationProgressPayload | undefined
        if (!payload) return

        const newState: ProgressState = {
          progress: payload.progress,
          status: payload.status,
          eta: payload.eta ?? 0,
          isComplete: false,
          error: null,
          details: payload.message,
        }

        setState(newState)
        onProgress?.(payload.progress, newState)
        break
      }

      case 'job_complete': {
        const payload = msg.payload as JobCompletePayload | undefined
        if (!payload) return

        hasCompletedRef.current = true
        const newState: ProgressState = {
          progress: 100,
          status: 'complete',
          eta: 0,
          isComplete: true,
          error: null,
        }

        setState(newState)
        onComplete?.(payload.result)
        break
      }

      case 'error': {
        const payload = msg.payload as ErrorPayload | undefined
        const error = new Error(payload?.message || 'Unknown error')

        setState((prev) => ({
          ...prev,
          isComplete: true,
          error,
        }))
        onError?.(error)
        break
      }
    }
  }, [onProgress, onComplete, onError])

  // SSE fallback hook
  const { error: sseError } = useEventSource(sseUrl ?? '', {
    autoConnect: useSSE && !!sseUrl,
    autoReconnect: true,
    eventType: 'progress',
    onMessage: handleSSEData,
    onError: () => {
      const error = new Error('SSE connection failed')
      setState((prev) => ({ ...prev, error }))
      onError?.(error)
    },
    ...sseOptions,
  })

  // WebSocket implementation
  useEffect(() => {
    if (useSSE) return // Skip WebSocket if using SSE

    // Reset state when jobId changes
    hasCompletedRef.current = false
    setState(initialState)

    // Subscribe to job-specific messages
    const unsubscribe = wsClient.subscribeToJob(jobId, (message: WebSocketMessage) => {
      if (hasCompletedRef.current) return

      switch (message.type) {
        case 'generation_progress': {
          const payload = message.payload as GenerationProgressPayload
          if (!payload) return

          const newState: ProgressState = {
            progress: Math.min(100, Math.max(0, payload.progress)),
            status: payload.status,
            eta: payload.eta ?? 0,
            isComplete: false,
            error: null,
            details: payload.message,
          }

          setState(newState)
          onProgress?.(newState.progress, newState)
          break
        }

        case 'job_complete': {
          const payload = message.payload as JobCompletePayload
          if (!payload) return

          hasCompletedRef.current = true
          const newState: ProgressState = {
            progress: 100,
            status: 'complete',
            eta: 0,
            isComplete: true,
            error: null,
          }

          setState(newState)
          onComplete?.(payload.result)
          break
        }

        case 'error': {
          const payload = message.payload as ErrorPayload
          const error = new Error(
            payload?.message || 'Unknown error during generation'
          )

          hasCompletedRef.current = true
          setState((prev) => ({
            ...prev,
            isComplete: true,
            error,
          }))
          onError?.(error)
          break
        }
      }
    })

    unsubscribeRef.current = unsubscribe

    return () => {
      unsubscribe()
      unsubscribeRef.current = null
    }
  }, [jobId, useSSE, onProgress, onComplete, onError])

  // Handle SSE errors
  useEffect(() => {
    if (useSSE && sseError) {
      setState((prev) => ({
        ...prev,
        error: sseError,
        isComplete: true,
      }))
    }
  }, [useSSE, sseError])

  return state
}

/**
 * Hook to check if WebSocket is available and working
 * Useful for determining whether to use WebSocket or SSE
 */
export function useWebSocketAvailability(): boolean {
  const [isAvailable, setIsAvailable] = useState(false)

  useEffect(() => {
    // Check if WebSocket is supported by the browser
    if (typeof WebSocket === 'undefined') {
      setIsAvailable(false)
      return
    }

    // Check connection state
    const unsubscribe = wsClient.onConnectionStateChange((state) => {
      setIsAvailable(state === 'connected')
    })

    // Try to connect if not already connected
    if (wsClient.getConnectionState() === 'disconnected') {
      wsClient.connect()
    }

    return () => {
      unsubscribe()
    }
  }, [])

  return isAvailable
}

/**
 * Hook that automatically selects WebSocket or SSE based on availability
 */
export function useAdaptiveProgressStream(
  jobId: string,
  options: Omit<UseProgressStreamOptions, 'useSSE'> = {}
): ProgressState & { transport: 'websocket' | 'sse' } {
  const wsAvailable = useWebSocketAvailability()
  const preferSSE = options.sseOptions !== undefined

  // Prefer WebSocket unless SSE is explicitly configured
  const useSSE = preferSSE || !wsAvailable

  const state = useProgressStream(jobId, {
    ...options,
    useSSE,
  })

  return {
    ...state,
    transport: useSSE ? 'sse' : 'websocket',
  }
}

export default useProgressStream
