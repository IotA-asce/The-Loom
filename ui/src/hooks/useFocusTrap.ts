import { useEffect, useRef, useCallback } from 'react'

interface UseFocusTrapOptions {
  enabled?: boolean
  onEscape?: () => void
  onFocusOut?: () => void
}

/**
 * Hook to trap focus within a container element.
 * Used for modals, dialogs, and other overlay components.
 */
export function useFocusTrap<T extends HTMLElement>(options: UseFocusTrapOptions = {}) {
  const { enabled = true, onEscape, onFocusOut } = options
  const containerRef = useRef<T>(null)
  const previousFocusRef = useRef<HTMLElement | null>(null)
  const firstFocusableRef = useRef<HTMLElement | null>(null)
  const lastFocusableRef = useRef<HTMLElement | null>(null)

  // Get all focusable elements within the container
  const getFocusableElements = useCallback((): HTMLElement[] => {
    const container = containerRef.current
    if (!container) return []

    const focusableSelectors = [
      'button:not([disabled])',
      'a[href]',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable]',
    ]

    return Array.from(
      container.querySelectorAll(focusableSelectors.join(', '))
    ).filter((el): el is HTMLElement => {
      // Filter out hidden elements
      const style = window.getComputedStyle(el)
      return style.display !== 'none' && style.visibility !== 'hidden'
    })
  }, [])

  // Update first and last focusable element refs
  const updateFocusableRefs = useCallback(() => {
    const focusableElements = getFocusableElements()
    firstFocusableRef.current = focusableElements[0] || null
    lastFocusableRef.current = focusableElements[focusableElements.length - 1] || null
  }, [getFocusableElements])

  // Handle tab key to trap focus
  const handleTabKey = useCallback((e: KeyboardEvent) => {
    if (e.key !== 'Tab') return

    updateFocusableRefs()
    const firstFocusable = firstFocusableRef.current
    const lastFocusable = lastFocusableRef.current

    if (!firstFocusable || !lastFocusable) {
      e.preventDefault()
      return
    }

    // Shift + Tab: move to last element if at first
    if (e.shiftKey) {
      if (document.activeElement === firstFocusable) {
        e.preventDefault()
        lastFocusable.focus()
      }
    } else {
      // Tab: move to first element if at last
      if (document.activeElement === lastFocusable) {
        e.preventDefault()
        firstFocusable.focus()
      }
    }
  }, [updateFocusableRefs])

  // Handle escape key
  const handleEscape = useCallback((event: KeyboardEvent) => {
    if (event.key === 'Escape' && onEscape) {
      onEscape()
    }
  }, [onEscape])

  // Handle focus out
  const handleFocusOut = useCallback((_event: FocusEvent) => {
    const container = containerRef.current
    if (!container) return

    // Small delay to allow focus to settle
    setTimeout(() => {
      if (!container.contains(document.activeElement)) {
        onFocusOut?.()
        // Refocus the container or first focusable element
        firstFocusableRef.current?.focus()
      }
    }, 0)
  }, [onFocusOut])

  useEffect(() => {
    if (!enabled) return

    const container = containerRef.current
    if (!container) return

    // Store the previously focused element
    previousFocusRef.current = document.activeElement as HTMLElement

    // Set up focus trap
    updateFocusableRefs()

    // Focus the first focusable element or the container itself
    if (firstFocusableRef.current) {
      firstFocusableRef.current.focus()
    } else {
      container.focus()
    }

    // Add event listeners
    container.addEventListener('keydown', handleTabKey)
    container.addEventListener('keydown', handleEscape)
    container.addEventListener('focusout', handleFocusOut)

    // Prevent scrolling on body
    const originalOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    return () => {
      container.removeEventListener('keydown', handleTabKey)
      container.removeEventListener('keydown', handleEscape)
      container.removeEventListener('focusout', handleFocusOut)

      // Restore body scroll
      document.body.style.overflow = originalOverflow

      // Restore previous focus
      previousFocusRef.current?.focus()
    }
  }, [enabled, handleTabKey, handleEscape, handleFocusOut, updateFocusableRefs])

  return containerRef
}

/**
 * Hook to manage focus within a component with initial focus and return focus.
 */
export function useFocusManager<T extends HTMLElement>() {
  const containerRef = useRef<T>(null)
  const previousFocusRef = useRef<HTMLElement | null>(null)

  const focusFirst = useCallback(() => {
    const container = containerRef.current
    if (!container) return

    const focusable = container.querySelector<HTMLElement>(
      'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    )
    focusable?.focus()
  }, [])

  const focusElement = useCallback((selector: string) => {
    containerRef.current?.querySelector<HTMLElement>(selector)?.focus()
  }, [])

  const saveFocus = useCallback(() => {
    previousFocusRef.current = document.activeElement as HTMLElement
  }, [])

  const restoreFocus = useCallback(() => {
    previousFocusRef.current?.focus()
  }, [])

  return {
    containerRef,
    focusFirst,
    focusElement,
    saveFocus,
    restoreFocus,
  }
}
