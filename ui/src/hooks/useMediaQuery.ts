import { useEffect, useState } from 'react'

// Breakpoint constants (in pixels)
const BREAKPOINTS = {
  mobile: 768,
  tablet: 1024,
} as const

/**
 * Check if we're in a browser environment (SSR-safe)
 */
const isBrowser = (): boolean => {
  return typeof window !== 'undefined'
}

/**
 * Hook for tracking a media query match state.
 * SSR-safe: returns false on server, actual value on client.
 *
 * @param query - CSS media query string (e.g., '(max-width: 768px)')
 * @returns boolean indicating if the media query matches
 *
 * @example
 * const isSmall = useMediaQuery('(max-width: 768px)')
 * const prefersDark = useMediaQuery('(prefers-color-scheme: dark)')
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState<boolean>(false)

  useEffect(() => {
    if (!isBrowser()) {
      return
    }

    const mediaQuery = window.matchMedia(query)

    // Set initial value
    setMatches(mediaQuery.matches)

    // Handle changes
    const handleChange = (event: MediaQueryListEvent): void => {
      setMatches(event.matches)
    }

    // Use addEventListener for modern browsers, fallback to addListener for older ones
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange)
    } else {
      // Safari < 14 compatibility
      mediaQuery.addListener(handleChange)
    }

    return () => {
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', handleChange)
      } else {
        // Safari < 14 compatibility
        mediaQuery.removeListener(handleChange)
      }
    }
  }, [query])

  return matches
}

/**
 * Hook to detect mobile breakpoint (< 768px).
 * SSR-safe: returns false on server.
 *
 * @returns true if viewport width is less than 768px
 */
export function useIsMobile(): boolean {
  return useMediaQuery(`(max-width: ${BREAKPOINTS.mobile - 1}px)`)
}

/**
 * Hook to detect tablet breakpoint (768px - 1024px).
 * SSR-safe: returns false on server.
 *
 * @returns true if viewport width is between 768px and 1024px (inclusive)
 */
export function useIsTablet(): boolean {
  const isMinTablet = useMediaQuery(`(min-width: ${BREAKPOINTS.mobile}px)`)
  const isMaxTablet = useMediaQuery(`(max-width: ${BREAKPOINTS.tablet}px)`)
  return isMinTablet && isMaxTablet
}

/**
 * Hook to detect desktop breakpoint (> 1024px).
 * SSR-safe: returns false on server.
 *
 * @returns true if viewport width is greater than 1024px
 */
export function useIsDesktop(): boolean {
  return useMediaQuery(`(min-width: ${BREAKPOINTS.tablet + 1}px)`)
}

/**
 * Hook to detect device orientation.
 * SSR-safe: returns 'portrait' on server.
 *
 * @returns 'portrait' or 'landscape' based on viewport orientation
 */
export function useOrientation(): 'portrait' | 'landscape' {
  const isLandscape = useMediaQuery('(orientation: landscape)')
  return isLandscape ? 'landscape' : 'portrait'
}

/**
 * Hook to get the current window dimensions.
 * SSR-safe: returns default values on server.
 *
 * @returns Object with width and height
 */
export function useWindowSize(): { width: number; height: number } {
  const [size, setSize] = useState<{ width: number; height: number }>(() => {
    if (!isBrowser()) {
      return { width: 0, height: 0 }
    }
    return {
      width: window.innerWidth,
      height: window.innerHeight,
    }
  })

  useEffect(() => {
    if (!isBrowser()) {
      return
    }

    const handleResize = (): void => {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight,
      })
    }

    // Use requestAnimationFrame for better performance
    let rafId: number | null = null
    const throttledResize = (): void => {
      if (rafId !== null) return
      rafId = requestAnimationFrame(() => {
        handleResize()
        rafId = null
      })
    }

    window.addEventListener('resize', throttledResize)

    // Also listen for orientation changes on mobile
    window.addEventListener('orientationchange', handleResize)

    return () => {
      window.removeEventListener('resize', throttledResize)
      window.removeEventListener('orientationchange', handleResize)
      if (rafId !== null) {
        cancelAnimationFrame(rafId)
      }
    }
  }, [])

  return size
}

/**
 * Hook to check for reduced motion preference.
 * Useful for accessibility - respect user's motion preferences.
 * SSR-safe: returns false on server.
 *
 * @returns true if user prefers reduced motion
 */
export function usePrefersReducedMotion(): boolean {
  return useMediaQuery('(prefers-reduced-motion: reduce)')
}

/**
 * Hook to check for hover capability.
 * Useful for touch vs mouse device detection.
 * SSR-safe: returns false on server.
 *
 * @returns true if primary input can hover
 */
export function useCanHover(): boolean {
  return useMediaQuery('(hover: hover)')
}

/**
 * Hook to check for coarse pointer (touch) vs fine pointer (mouse/stylus).
 * SSR-safe: returns false on server.
 *
 * @returns true if primary pointer is coarse (touch)
 */
export function useIsCoarsePointer(): boolean {
  return useMediaQuery('(pointer: coarse)')
}

export interface BreakpointState {
  isMobile: boolean
  isTablet: boolean
  isDesktop: boolean
  isMobileOrTablet: boolean
}

/**
 * Hook that returns all breakpoint states at once.
 * More efficient than calling individual hooks when you need multiple values.
 * SSR-safe: returns false values on server.
 *
 * @returns Object with all breakpoint booleans
 */
export function useBreakpoints(): BreakpointState {
  const isMobile = useIsMobile()
  const isTablet = useIsTablet()
  const isDesktop = useIsDesktop()

  return {
    isMobile,
    isTablet,
    isDesktop,
    isMobileOrTablet: isMobile || isTablet,
  }
}

export { BREAKPOINTS }
