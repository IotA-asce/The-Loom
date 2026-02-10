import { useMemo, useCallback, useEffect, useState } from 'react'
import {
  useMediaQuery,
  useIsMobile,
  useIsTablet,
  useIsDesktop,
  useOrientation,
  useWindowSize,
  useBreakpoints,
  usePrefersReducedMotion,
  useCanHover,
  useIsCoarsePointer,
  BREAKPOINTS,
  type BreakpointState,
} from './useMediaQuery'
import { useTouch, useIsTouchDevice, type TouchState, type TouchHandlers, type TouchConfig } from './useTouch'

export type { TouchState, TouchHandlers, TouchConfig, BreakpointState }

export interface ResponsiveState extends BreakpointState {
  // Viewport
  /** Current window width in pixels */
  width: number
  /** Current window height in pixels */
  height: number
  /** Current device orientation */
  orientation: 'portrait' | 'landscape'

  // Device capabilities
  /** Whether the device supports touch */
  isTouchDevice: boolean
  /** Whether the primary input is coarse (touch) */
  isCoarsePointer: boolean
  /** Whether the primary input can hover (mouse/stylus) */
  canHover: boolean
  /** Whether the user prefers reduced motion (accessibility) */
  prefersReducedMotion: boolean

  // Derived helpers
  /** True if in a compact layout (mobile or tablet portrait) */
  isCompact: boolean
  /** True if in a wide layout (desktop or tablet landscape) */
  isWide: boolean

  // Touch state (if useTouchOptions provided)
  /** Current touch gesture state (null if touch not enabled) */
  touch: TouchState | null
}

export interface UseResponsiveOptions {
  /** Enable touch gesture handling on the returned ref */
  enableTouch?: boolean
  /** Touch handlers to attach (only used if enableTouch is true) */
  touchHandlers?: TouchHandlers
  /** Touch configuration (only used if enableTouch is true) */
  touchConfig?: TouchConfig
  /** Additional media queries to track */
  mediaQueries?: Record<string, string>
}

export interface UseResponsiveReturn {
  /** Complete responsive state object */
  state: ResponsiveState
  /** Ref to attach for touch handling (if enabled) */
  ref: React.RefObject<HTMLElement> | null
  /** Additional media query results (if mediaQueries provided) */
  mediaQueryResults: Record<string, boolean>
  /** Force update the responsive state */
  refresh: () => void
}

/**
 * Combined hook for responsive design that provides viewport, breakpoint,
 * device capability, and optional touch gesture information.
 *
 * This hook combines useMediaQuery, useTouch, and other responsive hooks
 * into a single convenient interface that auto-updates on resize,
 * orientation change, and touch events.
 *
 * @param options - Configuration options for the hook
 * @returns Object containing responsive state, ref, and utilities
 *
 * @example
 * // Basic usage - viewport and breakpoint info
 * const { state } = useResponsive()
 * console.log(state.isMobile, state.orientation)
 *
 * @example
 * // With touch gestures
 * const { state, ref } = useResponsive({
 *   enableTouch: true,
 *   touchHandlers: {
 *     onTap: () => console.log('tapped'),
 *     onSwipe: (data) => console.log('swiped', data.direction),
 *   }
 * })
 *
 * return <div ref={ref}>Touch me</div>
 *
 * @example
 * // With custom media queries
 * const { state, mediaQueryResults } = useResponsive({
 *   mediaQueries: {
 *     isSmallHeight: '(max-height: 600px)',
 *     prefersDark: '(prefers-color-scheme: dark)',
 *   }
 * })
 * console.log(mediaQueryResults.isSmallHeight)
 */
export function useResponsive(options: UseResponsiveOptions = {}): UseResponsiveReturn {
  const {
    enableTouch = false,
    touchHandlers = {},
    touchConfig = {},
    mediaQueries = {},
  } = options

  // Get all individual responsive values
  const { width, height } = useWindowSize()
  const breakpoints = useBreakpoints()
  const orientation = useOrientation()
  const isTouchDevice = useIsTouchDevice()
  const isCoarsePointer = useIsCoarsePointer()
  const canHover = useCanHover()
  const prefersReducedMotion = usePrefersReducedMotion()

  // Touch handling (if enabled)
  const touchResult = enableTouch
    ? useTouch(touchHandlers, touchConfig)
    : { ref: null, state: null, reset: () => {} }

  // Custom media queries
  const mediaQueryEntries = Object.entries(mediaQueries)
  const mediaQueryResults: Record<string, boolean> = {}

  for (const [key, query] of mediaQueryEntries) {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    mediaQueryResults[key] = useMediaQuery(query)
  }

  // Memoized responsive state
  const state: ResponsiveState = useMemo(() => {
    const isCompact = breakpoints.isMobile || (breakpoints.isTablet && orientation === 'portrait')
    const isWide = !isCompact

    return {
      ...breakpoints,
      width,
      height,
      orientation,
      isTouchDevice,
      isCoarsePointer,
      canHover,
      prefersReducedMotion,
      isCompact,
      isWide,
      touch: touchResult.state,
    }
  }, [
    breakpoints,
    width,
    height,
    orientation,
    isTouchDevice,
    isCoarsePointer,
    canHover,
    prefersReducedMotion,
    touchResult.state,
  ])

  // Refresh function to force re-evaluation
  const refresh = useCallback((): void => {
    // Dispatch a resize event to trigger all dependent hooks
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event('resize'))
    }
    // Reset touch state if touch is enabled
    touchResult.reset()
  }, [touchResult])

  return {
    state,
    ref: touchResult.ref,
    mediaQueryResults,
    refresh,
  }
}

/**
 * Hook that returns responsive class names based on current viewport.
 * Useful for applying different styles at different breakpoints.
 *
 * @param classMap - Object mapping breakpoints to class names
 * @returns The appropriate class name for current breakpoint
 *
 * @example
 * const className = useResponsiveClass({
 *   mobile: 'text-sm p-2',
 *   tablet: 'text-base p-4',
 *   desktop: 'text-lg p-6',
 * })
 */
export function useResponsiveClass(classMap: {
  mobile?: string
  tablet?: string
  desktop?: string
  default?: string
}): string {
  const { isMobile, isTablet, isDesktop } = useBreakpoints()

  return useMemo(() => {
    if (isMobile && classMap.mobile) return classMap.mobile
    if (isTablet && classMap.tablet) return classMap.tablet
    if (isDesktop && classMap.desktop) return classMap.desktop
    return classMap.default ?? ''
  }, [isMobile, isTablet, isDesktop, classMap])
}

/**
 * Hook that returns a responsive value based on current viewport.
 * Similar to useResponsiveClass but for any value type.
 *
 * @param valueMap - Object mapping breakpoints to values
 * @returns The appropriate value for current breakpoint
 *
 * @example
 * const columns = useResponsiveValue({
 *   mobile: 1,
 *   tablet: 2,
 *   desktop: 4,
 * })
 */
export function useResponsiveValue<T>(valueMap: {
  mobile?: T
  tablet?: T
  desktop?: T
  default?: T
}): T | undefined {
  const { isMobile, isTablet, isDesktop } = useBreakpoints()

  return useMemo(() => {
    if (isMobile && valueMap.mobile !== undefined) return valueMap.mobile
    if (isTablet && valueMap.tablet !== undefined) return valueMap.tablet
    if (isDesktop && valueMap.desktop !== undefined) return valueMap.desktop
    return valueMap.default
  }, [isMobile, isTablet, isDesktop, valueMap])
}

/**
 * Hook for responsive layout calculations.
 * Returns the number of columns that fit given constraints.
 *
 * @param options - Configuration for column calculation
 * @returns Number of columns that fit
 *
 * @example
 * const columns = useResponsiveColumns({
 *   minColumnWidth: 200,
 *   maxColumns: 4,
 *   gap: 16,
 * })
 */
export function useResponsiveColumns(options: {
  minColumnWidth: number
  maxColumns?: number
  gap?: number
  containerRef?: React.RefObject<HTMLElement>
}): number {
  const { minColumnWidth, maxColumns = Infinity, gap = 0, containerRef } = options
  const { width: windowWidth } = useWindowSize()
  const [columns, setColumns] = useState(1)

  useEffect(() => {
    const containerWidth = containerRef?.current?.clientWidth ?? windowWidth
    if (containerWidth === 0) return

    const availableWidth = containerWidth
    const calculated = Math.floor((availableWidth + gap) / (minColumnWidth + gap))
    const clamped = Math.max(1, Math.min(calculated, maxColumns))

    setColumns(clamped)
  }, [windowWidth, minColumnWidth, maxColumns, gap, containerRef])

  return columns
}

/**
 * Hook to detect if an element is in viewport.
 * Useful for lazy loading or scroll-triggered animations.
 *
 * @param ref - Ref to the element to observe
 * @param options - Intersection observer options
 * @returns Object with isInView and intersection ratio
 */
export function useInView(
  ref: React.RefObject<HTMLElement>,
  options: IntersectionObserverInit = {}
): { isInView: boolean; ratio: number } {
  const [state, setState] = useState({ isInView: false, ratio: 0 })

  useEffect(() => {
    const element = ref.current
    if (!element) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        setState({
          isInView: entry.isIntersecting,
          ratio: entry.intersectionRatio,
        })
      },
      {
        threshold: 0,
        rootMargin: '0px',
        ...options,
      }
    )

    observer.observe(element)

    return () => {
      observer.disconnect()
    }
  }, [ref, options.root, options.rootMargin, options.threshold])

  return state
}

/**
 * Hook for virtualized list calculations.
 * Returns visible range and item positions for large lists.
 *
 * @param options - Virtualization options
 * @returns Virtualization state for rendering
 *
 * @example
 * const { visibleRange, totalHeight, getItemStyle } = useVirtualizer({
 *   itemCount: 1000,
 *   itemHeight: 50,
 *   overscan: 5,
 * })
 */
export function useVirtualizer(options: {
  itemCount: number
  itemHeight: number
  overscan?: number
  containerRef: React.RefObject<HTMLElement>
}): {
  visibleRange: { start: number; end: number }
  totalHeight: number
  getItemStyle: (index: number) => React.CSSProperties
  scrollToIndex: (index: number) => void
} {
  const { itemCount, itemHeight, overscan = 3, containerRef } = options
  const [scrollTop, setScrollTop] = useState(0)
  const [containerHeight, setContainerHeight] = useState(0)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const handleScroll = (): void => {
      setScrollTop(container.scrollTop)
    }

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerHeight(entry.contentRect.height)
      }
    })

    setScrollTop(container.scrollTop)
    setContainerHeight(container.clientHeight)

    container.addEventListener('scroll', handleScroll)
    resizeObserver.observe(container)

    return () => {
      container.removeEventListener('scroll', handleScroll)
      resizeObserver.disconnect()
    }
  }, [containerRef])

  const visibleRange = useMemo(() => {
    const startIndex = Math.floor(scrollTop / itemHeight)
    const visibleCount = Math.ceil(containerHeight / itemHeight)

    return {
      start: Math.max(0, startIndex - overscan),
      end: Math.min(itemCount, startIndex + visibleCount + overscan),
    }
  }, [scrollTop, containerHeight, itemHeight, overscan, itemCount])

  const totalHeight = itemCount * itemHeight

  const getItemStyle = useCallback(
    (index: number): React.CSSProperties => ({
      position: 'absolute',
      top: index * itemHeight,
      height: itemHeight,
      left: 0,
      right: 0,
    }),
    [itemHeight]
  )

  const scrollToIndex = useCallback(
    (index: number): void => {
      const container = containerRef.current
      if (!container) return

      const targetScrollTop = index * itemHeight
      container.scrollTop = targetScrollTop
    },
    [containerRef, itemHeight]
  )

  return {
    visibleRange,
    totalHeight,
    getItemStyle,
    scrollToIndex,
  }
}

// Re-export everything from useMediaQuery and useTouch for convenience
export {
  useMediaQuery,
  useIsMobile,
  useIsTablet,
  useIsDesktop,
  useOrientation,
  useWindowSize,
  useBreakpoints,
  usePrefersReducedMotion,
  useCanHover,
  useIsCoarsePointer,
  useTouch,
  useIsTouchDevice,
  BREAKPOINTS,
}
