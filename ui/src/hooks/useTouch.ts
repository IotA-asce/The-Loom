import { useCallback, useEffect, useRef, useState } from 'react'

// Default configuration values
const DEFAULT_CONFIG: Required<TouchConfig> = {
  tapThreshold: 10,        // Max distance (px) for a tap
  doubleTapDelay: 300,     // Max time (ms) between taps for double tap
  longPressDelay: 500,     // Time (ms) to trigger long press
  swipeThreshold: 50,      // Min distance (px) for a swipe
  swipeVelocity: 0.3,      // Min velocity (px/ms) for a swipe
  pinchThreshold: 0.1,     // Min scale change for pinch
  preventDefault: true,    // Prevent default on handled gestures
  stopPropagation: false,  // Stop event propagation
}

export interface TouchConfig {
  /** Maximum distance (px) for a tap to be recognized */
  tapThreshold?: number
  /** Maximum delay (ms) between taps for double tap */
  doubleTapDelay?: number
  /** Time (ms) to hold for long press */
  longPressDelay?: number
  /** Minimum distance (px) for a swipe */
  swipeThreshold?: number
  /** Minimum velocity (px/ms) for a swipe */
  swipeVelocity?: number
  /** Minimum scale change for pinch */
  pinchThreshold?: number
  /** Prevent default browser behavior on handled gestures */
  preventDefault?: boolean
  /** Stop event propagation */
  stopPropagation?: boolean
}

export interface SwipeData {
  direction: 'up' | 'down' | 'left' | 'right'
  distance: number
  velocity: number
  startX: number
  startY: number
  endX: number
  endY: number
}

export interface PinchData {
  scale: number
  delta: number
  centerX: number
  centerY: number
}

export interface TouchPosition {
  x: number
  y: number
}

export interface TouchHandlers {
  /** Called on single tap */
  onTap?: (position: TouchPosition) => void
  /** Called on double tap */
  onDoubleTap?: (position: TouchPosition) => void
  /** Called when long press starts */
  onLongPress?: (position: TouchPosition) => void
  /** Called when long press ends (finger lifted) */
  onLongPressEnd?: (position: TouchPosition) => void
  /** Called on swipe */
  onSwipe?: (data: SwipeData) => void
  /** Called when pinch starts */
  onPinchStart?: (data: PinchData) => void
  /** Called during pinch gesture */
  onPinch?: (data: PinchData) => void
  /** Called when pinch ends */
  onPinchEnd?: (data: PinchData) => void
  /** Called on touch start (for any touch) */
  onTouchStart?: (position: TouchPosition) => void
  /** Called on touch move (for any touch) */
  onTouchMove?: (position: TouchPosition) => void
  /** Called on touch end (for any touch) */
  onTouchEnd?: (position: TouchPosition) => void
}

export interface TouchState {
  /** Whether a touch is currently active */
  isTouching: boolean
  /** Whether a long press is currently active */
  isLongPressing: boolean
  /** Whether a pinch is currently active */
  isPinching: boolean
  /** Current number of active touches */
  touchCount: number
  /** Current touch position */
  position: TouchPosition | null
}

interface TouchRef {
  startTime: number
  startX: number
  startY: number
  lastX: number
  lastY: number
  lastTime: number
  longPressTimer: ReturnType<typeof setTimeout> | null
  lastTapTime: number
  lastTapX: number
  lastTapY: number
  initialPinchDistance: number
  initialPinchScale: number
  lastPinchScale: number
  pinchCenterX: number
  pinchCenterY: number
  isLongPressTriggered: boolean
}

/**
 * Hook for handling touch gestures on an element.
 * Supports tap, double tap, long press, swipe, and pinch gestures.
 *
 * @param handlers - Object containing gesture handlers
 * @param config - Optional configuration for gesture thresholds
 * @returns Object with ref to attach to element and current touch state
 *
 * @example
 * const { ref, state } = useTouch({
 *   onTap: (pos) => console.log('Tapped at', pos),
 *   onSwipe: (data) => console.log('Swiped', data.direction),
 *   onPinch: (data) => console.log('Scale:', data.scale),
 * })
 *
 * return <div ref={ref}>Touch me</div>
 */
export function useTouch(
  handlers: TouchHandlers = {},
  config: TouchConfig = {}
): {
  ref: React.RefObject<HTMLElement>
  state: TouchState
  reset: () => void
} {
  const cfg = { ...DEFAULT_CONFIG, ...config }
  const elementRef = useRef<HTMLElement>(null)
  const touchRef = useRef<TouchRef>({
    startTime: 0,
    startX: 0,
    startY: 0,
    lastX: 0,
    lastY: 0,
    lastTime: 0,
    longPressTimer: null,
    lastTapTime: 0,
    lastTapX: 0,
    lastTapY: 0,
    initialPinchDistance: 0,
    initialPinchScale: 1,
    lastPinchScale: 1,
    pinchCenterX: 0,
    pinchCenterY: 0,
    isLongPressTriggered: false,
  })

  const [state, setState] = useState<TouchState>({
    isTouching: false,
    isLongPressing: false,
    isPinching: false,
    touchCount: 0,
    position: null,
  })

  const reset = useCallback((): void => {
    const touch = touchRef.current
    if (touch.longPressTimer) {
      clearTimeout(touch.longPressTimer)
      touch.longPressTimer = null
    }
    touch.isLongPressTriggered = false

    setState({
      isTouching: false,
      isLongPressing: false,
      isPinching: false,
      touchCount: 0,
      position: null,
    })
  }, [])

  const getDistance = useCallback(
    (touch1: Touch, touch2: Touch): number => {
      const dx = touch2.clientX - touch1.clientX
      const dy = touch2.clientY - touch1.clientY
      return Math.sqrt(dx * dx + dy * dy)
    },
    []
  )

  const getCenter = useCallback(
    (touch1: Touch, touch2: Touch): { x: number; y: number } => {
      return {
        x: (touch1.clientX + touch2.clientX) / 2,
        y: (touch1.clientY + touch2.clientY) / 2,
      }
    },
    []
  )

  const handleTouchStart = useCallback(
    (event: TouchEvent): void => {
      const touch = touchRef.current
      const touches = event.touches

      if (cfg.stopPropagation) {
        event.stopPropagation()
      }

      touch.startTime = Date.now()
      touch.startX = touches[0].clientX
      touch.startY = touches[0].clientY
      touch.lastX = touch.startX
      touch.lastY = touch.startY
      touch.lastTime = touch.startTime

      const position: TouchPosition = { x: touch.startX, y: touch.startY }

      setState((prev) => ({
        ...prev,
        isTouching: true,
        touchCount: touches.length,
        position,
      }))

      handlers.onTouchStart?.(position)

      // Handle pinch start (2 fingers)
      if (touches.length === 2 && (handlers.onPinch || handlers.onPinchStart)) {
        if (cfg.preventDefault) {
          event.preventDefault()
        }

        touch.initialPinchDistance = getDistance(touches[0], touches[1])
        touch.initialPinchScale = touch.lastPinchScale
        const center = getCenter(touches[0], touches[1])
        touch.pinchCenterX = center.x
        touch.pinchCenterY = center.y

        setState((prev) => ({ ...prev, isPinching: true }))

        handlers.onPinchStart?.({
          scale: touch.initialPinchScale,
          delta: 0,
          centerX: touch.pinchCenterX,
          centerY: touch.pinchCenterY,
        })
      }

      // Set up long press timer (only for single touch)
      if (touches.length === 1 && handlers.onLongPress) {
        touch.longPressTimer = setTimeout(() => {
          touch.isLongPressTriggered = true
          setState((prev) => ({ ...prev, isLongPressing: true }))
          handlers.onLongPress?.(position)
        }, cfg.longPressDelay)
      }
    },
    [cfg, handlers, getDistance, getCenter]
  )

  const handleTouchMove = useCallback(
    (event: TouchEvent): void => {
      const touch = touchRef.current
      const touches = event.touches
      const currentTime = Date.now()

      if (touches.length > 0) {
        touch.lastX = touches[0].clientX
        touch.lastY = touches[0].clientY
        touch.lastTime = currentTime

        setState((prev) => ({
          ...prev,
          position: { x: touch.lastX, y: touch.lastY },
          touchCount: touches.length,
        }))

        handlers.onTouchMove?.({ x: touch.lastX, y: touch.lastY })
      }

      // Check if moved too far for tap (cancel long press)
      if (touches.length === 1 && touch.longPressTimer) {
        const distance = Math.sqrt(
          Math.pow(touches[0].clientX - touch.startX, 2) +
          Math.pow(touches[0].clientY - touch.startY, 2)
        )
        if (distance > cfg.tapThreshold) {
          clearTimeout(touch.longPressTimer)
          touch.longPressTimer = null
        }
      }

      // Handle pinch
      if (touches.length === 2 && state.isPinching) {
        if (cfg.preventDefault) {
          event.preventDefault()
        }

        const distance = getDistance(touches[0], touches[1])
        const scale = distance / touch.initialPinchDistance * touch.initialPinchScale
        const center = getCenter(touches[0], touches[1])

        touch.lastPinchScale = scale

        handlers.onPinch?.({
          scale,
          delta: scale - touch.initialPinchScale,
          centerX: center.x,
          centerY: center.y,
        })
      }
    },
    [cfg, handlers, state.isPinching, getDistance, getCenter]
  )

  const handleTouchEnd = useCallback(
    (event: TouchEvent): void => {
      const touch = touchRef.current
      const endTime = Date.now()
      const duration = endTime - touch.startTime
      const changedTouches = event.changedTouches

      if (changedTouches.length === 0) return

      const endX = changedTouches[0].clientX
      const endY = changedTouches[0].clientY
      const position: TouchPosition = { x: endX, y: endY }

      handlers.onTouchEnd?.(position)

      // Clear long press timer
      if (touch.longPressTimer) {
        clearTimeout(touch.longPressTimer)
        touch.longPressTimer = null
      }

      // Handle long press end
      if (touch.isLongPressTriggered) {
        touch.isLongPressTriggered = false
        setState((prev) => ({ ...prev, isLongPressing: false }))
        handlers.onLongPressEnd?.(position)
      }

      // Handle pinch end
      if (state.isPinching && event.touches.length < 2) {
        setState((prev) => ({ ...prev, isPinching: false }))
        handlers.onPinchEnd?.({
          scale: touch.lastPinchScale,
          delta: touch.lastPinchScale - touch.initialPinchScale,
          centerX: touch.pinchCenterX,
          centerY: touch.pinchCenterY,
        })
      }

      // Only process gestures if this was a single touch
      if (event.touches.length === 0 && changedTouches.length === 1) {
        const distance = Math.sqrt(
          Math.pow(endX - touch.startX, 2) + Math.pow(endY - touch.startY, 2)
        )

        // Check for swipe
        if (distance >= cfg.swipeThreshold && handlers.onSwipe) {
          const velocity = distance / duration

          if (velocity >= cfg.swipeVelocity) {
            const dx = endX - touch.startX
            const dy = endY - touch.startY
            let direction: SwipeData['direction']

            if (Math.abs(dx) > Math.abs(dy)) {
              direction = dx > 0 ? 'right' : 'left'
            } else {
              direction = dy > 0 ? 'down' : 'up'
            }

            if (cfg.preventDefault) {
              event.preventDefault()
            }

            handlers.onSwipe({
              direction,
              distance,
              velocity,
              startX: touch.startX,
              startY: touch.startY,
              endX,
              endY,
            })

            setState((prev) => ({ ...prev, isTouching: false, touchCount: 0 }))
            return
          }
        }

        // Check for double tap
        const tapDistance = Math.sqrt(
          Math.pow(endX - touch.lastTapX, 2) + Math.pow(endY - touch.lastTapY, 2)
        )
        const tapInterval = endTime - touch.lastTapTime

        if (
          tapInterval < cfg.doubleTapDelay &&
          tapDistance < cfg.tapThreshold &&
          handlers.onDoubleTap
        ) {
          if (cfg.preventDefault) {
            event.preventDefault()
          }

          handlers.onDoubleTap(position)
          touch.lastTapTime = 0 // Reset to prevent triple-tap
        }
        // Check for single tap
        else if (distance < cfg.tapThreshold && handlers.onTap) {
          if (cfg.preventDefault) {
            event.preventDefault()
          }

          handlers.onTap(position)
          touch.lastTapTime = endTime
          touch.lastTapX = endX
          touch.lastTapY = endY
        }
      }

      // Update state if no more touches
      if (event.touches.length === 0) {
        setState({
          isTouching: false,
          isLongPressing: false,
          isPinching: false,
          touchCount: 0,
          position: null,
        })
      } else {
        setState((prev) => ({
          ...prev,
          touchCount: event.touches.length,
        }))
      }
    },
    [cfg, handlers, state.isPinching]
  )

  const handleTouchCancel = useCallback((): void => {
    const touch = touchRef.current

    if (touch.longPressTimer) {
      clearTimeout(touch.longPressTimer)
      touch.longPressTimer = null
    }

    touch.isLongPressTriggered = false

    setState({
      isTouching: false,
      isLongPressing: false,
      isPinching: false,
      touchCount: 0,
      position: null,
    })
  }, [])

  useEffect(() => {
    const element = elementRef.current
    if (!element) return

    // Use passive listeners by default for better scroll performance
    // But mark as non-passive if we need to preventDefault
    const options: AddEventListenerOptions = {
      passive: !cfg.preventDefault,
    }

    element.addEventListener('touchstart', handleTouchStart, options)
    element.addEventListener('touchmove', handleTouchMove, options)
    element.addEventListener('touchend', handleTouchEnd)
    element.addEventListener('touchcancel', handleTouchCancel)

    return () => {
      element.removeEventListener('touchstart', handleTouchStart, options)
      element.removeEventListener('touchmove', handleTouchMove, options)
      element.removeEventListener('touchend', handleTouchEnd)
      element.removeEventListener('touchcancel', handleTouchCancel)
    }
  }, [handleTouchStart, handleTouchMove, handleTouchEnd, handleTouchCancel, cfg.preventDefault])

  return { ref: elementRef as React.RefObject<HTMLElement>, state, reset }
}

/**
 * Hook to detect if the device supports touch events.
 * SSR-safe: returns false on server.
 *
 * @returns true if device supports touch
 */
export function useIsTouchDevice(): boolean {
  const [isTouchDevice, setIsTouchDevice] = useState(false)

  useEffect(() => {
    setIsTouchDevice(
      'ontouchstart' in window ||
      navigator.maxTouchPoints > 0 ||
      // @ts-expect-error - msMaxTouchPoints for IE
      navigator.msMaxTouchPoints > 0
    )
  }, [])

  return isTouchDevice
}
