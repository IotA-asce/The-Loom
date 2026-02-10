import { useEffect, useState, useRef, useCallback } from 'react'
import { createPortal } from 'react-dom'
import './TutorialOverlay.css'

export type TooltipPosition = 'top' | 'bottom' | 'left' | 'right'

export interface TutorialStep {
  target: string
  title: string
  content: string
  position: TooltipPosition
}

interface TutorialOverlayProps {
  isActive: boolean
  steps: TutorialStep[]
  onComplete: () => void
  onSkip: () => void
}

interface TargetRect {
  x: number
  y: number
  width: number
  height: number
}

const PADDING = 8
const TOOLTIP_OFFSET = 16

export function TutorialOverlay({
  isActive,
  steps,
  onComplete,
  onSkip,
}: TutorialOverlayProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [targetRect, setTargetRect] = useState<TargetRect | null>(null)
  const [tooltipPosition, setTooltipPosition] = useState<TooltipPosition>('bottom')
  const [isTransitioning, setIsTransitioning] = useState(false)
  const tooltipRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const currentStep = steps[currentStepIndex]
  const isFirstStep = currentStepIndex === 0
  const isLastStep = currentStepIndex === steps.length - 1

  // Calculate target element position
  const updateTargetRect = useCallback(() => {
    if (!isActive || !currentStep) return

    const element = document.querySelector(currentStep.target)
    if (!element) {
      setTargetRect(null)
      return
    }

    const rect = element.getBoundingClientRect()
    setTargetRect({
      x: rect.left - PADDING,
      y: rect.top - PADDING,
      width: rect.width + PADDING * 2,
      height: rect.height + PADDING * 2,
    })
  }, [isActive, currentStep])

  // Determine best tooltip position based on available space
  const calculateTooltipPosition = useCallback((): TooltipPosition => {
    if (!targetRect || !tooltipRef.current) return currentStep?.position || 'bottom'

    const tooltipRect = tooltipRef.current.getBoundingClientRect()
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight
    const { x, y, width, height } = targetRect

    const positions: Record<TooltipPosition, boolean> = {
      top: y - tooltipRect.height - TOOLTIP_OFFSET > 0,
      bottom: y + height + tooltipRect.height + TOOLTIP_OFFSET < viewportHeight,
      left: x - tooltipRect.width - TOOLTIP_OFFSET > 0,
      right: x + width + tooltipRect.width + TOOLTIP_OFFSET < viewportWidth,
    }

    // Prefer requested position if it fits, otherwise find first that fits
    if (positions[currentStep.position]) {
      return currentStep.position
    }

    const fallback = (Object.keys(positions) as TooltipPosition[]).find((pos) => positions[pos])
    return fallback || 'bottom'
  }, [targetRect, currentStep])

  // Calculate tooltip coordinates based on position
  const getTooltipCoords = useCallback((): { left: number; top: number } => {
    if (!targetRect || !tooltipRef.current) return { left: 0, top: 0 }

    const tooltipRect = tooltipRef.current.getBoundingClientRect()
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight
    const { x, y, width, height } = targetRect

    let left = 0
    let top = 0

    switch (tooltipPosition) {
      case 'top':
        left = x + width / 2 - tooltipRect.width / 2
        top = y - tooltipRect.height - TOOLTIP_OFFSET
        break
      case 'bottom':
        left = x + width / 2 - tooltipRect.width / 2
        top = y + height + TOOLTIP_OFFSET
        break
      case 'left':
        left = x - tooltipRect.width - TOOLTIP_OFFSET
        top = y + height / 2 - tooltipRect.height / 2
        break
      case 'right':
        left = x + width + TOOLTIP_OFFSET
        top = y + height / 2 - tooltipRect.height / 2
        break
    }

    // Clamp to viewport bounds
    left = Math.max(16, Math.min(left, viewportWidth - tooltipRect.width - 16))
    top = Math.max(16, Math.min(top, viewportHeight - tooltipRect.height - 16))

    return { left, top }
  }, [targetRect, tooltipPosition])

  // Update target rect on step change and window events
  useEffect(() => {
    if (!isActive) return

    updateTargetRect()

    const handleResize = () => {
      updateTargetRect()
    }

    const handleScroll = () => {
      updateTargetRect()
    }

    window.addEventListener('resize', handleResize)
    window.addEventListener('scroll', handleScroll, true)

    return () => {
      window.removeEventListener('resize', handleResize)
      window.removeEventListener('scroll', handleScroll, true)
    }
  }, [isActive, updateTargetRect])

  // Recalculate tooltip position when target or step changes
  useEffect(() => {
    if (!isActive || !targetRect) return
    setTooltipPosition(calculateTooltipPosition())
  }, [isActive, targetRect, calculateTooltipPosition])

  // Handle step transitions
  const goToStep = useCallback(
    (index: number) => {
      setIsTransitioning(true)
      setTimeout(() => {
        setCurrentStepIndex(index)
        setIsTransitioning(false)
      }, 200)
    },
    [setCurrentStepIndex]
  )

  const handleNext = useCallback(() => {
    if (isLastStep) {
      onComplete()
      setCurrentStepIndex(0)
    } else {
      goToStep(currentStepIndex + 1)
    }
  }, [isLastStep, currentStepIndex, onComplete, goToStep])

  const handlePrev = useCallback(() => {
    if (!isFirstStep) {
      goToStep(currentStepIndex - 1)
    }
  }, [isFirstStep, currentStepIndex, goToStep])

  const handleSkip = useCallback(() => {
    onSkip()
    setCurrentStepIndex(0)
  }, [onSkip])

  // Keyboard navigation
  useEffect(() => {
    if (!isActive) return

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowRight':
        case 'Enter':
          e.preventDefault()
          handleNext()
          break
        case 'ArrowLeft':
          e.preventDefault()
          handlePrev()
          break
        case 'Escape':
          e.preventDefault()
          handleSkip()
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isActive, handleNext, handlePrev, handleSkip])

  // Prevent body scroll when active
  useEffect(() => {
    if (isActive) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isActive])

  if (!isActive || !currentStep) return null

  const tooltipCoords = getTooltipCoords()

  const overlay = (
    <div
      ref={containerRef}
      className="tutorial-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="tutorial-title"
    >
      {/* SVG Spotlight Mask */}
      <svg className="tutorial-spotlight" aria-hidden="true">
        <defs>
          <mask id="tutorial-mask">
            <rect width="100%" height="100%" fill="white" />
            {targetRect && (
              <rect
                x={targetRect.x}
                y={targetRect.y}
                width={targetRect.width}
                height={targetRect.height}
                rx="4"
                ry="4"
                fill="black"
              />
            )}
          </mask>
        </defs>
        <rect
          width="100%"
          height="100%"
          fill="rgba(0, 0, 0, 0.75)"
          mask="url(#tutorial-mask)"
          className={`tutorial-dim ${isTransitioning ? 'tutorial-dim-transitioning' : ''}`}
        />
      </svg>

      {/* Spotlight border highlight */}
      {targetRect && (
        <div
          className={`tutorial-highlight ${isTransitioning ? 'tutorial-highlight-transitioning' : ''}`}
          style={{
            left: targetRect.x,
            top: targetRect.y,
            width: targetRect.width,
            height: targetRect.height,
          }}
          aria-hidden="true"
        />
      )}

      {/* Tooltip */}
      <div
        ref={tooltipRef}
        className={`tutorial-tooltip tutorial-tooltip-${tooltipPosition} ${isTransitioning ? 'tutorial-tooltip-transitioning' : ''}`}
        style={{
          left: tooltipCoords.left,
          top: tooltipCoords.top,
        }}
      >
        {/* Arrow */}
        <div className={`tutorial-arrow tutorial-arrow-${tooltipPosition}`} aria-hidden="true" />

        {/* Header */}
        <div className="tutorial-header">
          <h3 id="tutorial-title" className="tutorial-title">
            {currentStep.title}
          </h3>
          <span className="tutorial-progress">
            {currentStepIndex + 1} of {steps.length}
          </span>
        </div>

        {/* Content */}
        <div className="tutorial-content">
          <p>{currentStep.content}</p>
        </div>

        {/* Footer */}
        <div className="tutorial-footer">
          {/* Progress dots */}
          <div className="tutorial-dots" role="progressbar" aria-label={`Step ${currentStepIndex + 1} of ${steps.length}`}>
            {steps.map((_, index) => (
              <button
                key={index}
                className={`tutorial-dot ${index === currentStepIndex ? 'tutorial-dot-active' : ''} ${
                  index < currentStepIndex ? 'tutorial-dot-completed' : ''
                }`}
                onClick={() => goToStep(index)}
                aria-label={`Go to step ${index + 1}`}
                aria-current={index === currentStepIndex ? 'step' : undefined}
              />
            ))}
          </div>

          {/* Navigation buttons */}
          <div className="tutorial-actions">
            <button
              className="tutorial-btn tutorial-btn-skip"
              onClick={handleSkip}
              aria-label="Skip tutorial"
            >
              Skip
            </button>
            <div className="tutorial-nav-buttons">
              <button
                className="tutorial-btn tutorial-btn-prev"
                onClick={handlePrev}
                disabled={isFirstStep}
                aria-label="Previous step"
              >
                ← Prev
              </button>
              <button
                className="tutorial-btn tutorial-btn-next"
                onClick={handleNext}
                aria-label={isLastStep ? 'Complete tutorial' : 'Next step'}
              >
                {isLastStep ? 'Finish' : 'Next →'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Hidden live region for screen reader announcements */}
      <div className="tutorial-live-region" aria-live="polite" aria-atomic="true">
        Step {currentStepIndex + 1} of {steps.length}: {currentStep.title}
      </div>
    </div>
  )

  return createPortal(overlay, document.body)
}

// Hook for managing tutorial state
interface UseTutorialOptions {
  steps: TutorialStep[]
  onComplete?: () => void
  onSkip?: () => void
}

export function useTutorial(options: UseTutorialOptions) {
  const { onComplete, onSkip } = options
  const [isActive, setIsActive] = useState(false)

  const start = useCallback(() => {
    setIsActive(true)
  }, [])

  const complete = useCallback(() => {
    setIsActive(false)
    onComplete?.()
  }, [onComplete])

  const skip = useCallback(() => {
    setIsActive(false)
    onSkip?.()
  }, [onSkip])

  return {
    isActive,
    start,
    complete,
    skip,
  }
}

export default TutorialOverlay
