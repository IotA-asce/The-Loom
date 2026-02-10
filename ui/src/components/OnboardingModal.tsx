import { useState, useEffect } from 'react'
import './OnboardingModal.css'

interface OnboardingModalProps {
  isOpen: boolean
  onClose: () => void
  onDontShowAgain: () => void
}

interface Feature {
  icon: string
  title: string
  description: string
}

const FEATURES: Feature[] = [
  {
    icon: '🕸️',
    title: 'Interactive Story Graph',
    description: 'Navigate your narrative as a visual graph of interconnected scenes, branches, and story beats.',
  },
  {
    icon: '✍️',
    title: 'AI-Assisted Writing',
    description: 'Generate context-aware text with style matching, character voice enforcement, and smart continuity.',
  },
  {
    icon: '🔀',
    title: 'Branch & Merge',
    description: 'Explore alternative storylines, create branches at any point, and merge them back when ready.',
  },
  {
    icon: '🎛️',
    title: 'Tone & Style Control',
    description: 'Fine-tune violence, humor, and romance levels with real-time previews and consistency checking.',
  },
]

export function OnboardingModal({ isOpen, onClose, onDontShowAgain }: OnboardingModalProps) {
  const [dontShowAgain, setDontShowAgain] = useState(false)
  const [isAnimating, setIsAnimating] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setIsAnimating(true)
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }

    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        handleClose()
      }
    }

    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [isOpen])

  const handleClose = () => {
    if (dontShowAgain) {
      onDontShowAgain()
    }
    setIsAnimating(false)
    // Small delay to allow exit animation
    setTimeout(onClose, 200)
  }

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDontShowAgain(e.target.checked)
  }

  if (!isOpen && !isAnimating) return null

  return (
    <div
      className={`onboarding-overlay ${isOpen ? 'visible' : ''}`}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          handleClose()
        }
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="onboarding-title"
      aria-describedby="onboarding-description"
    >
      <div className="onboarding-modal">
        {/* Hero Section */}
        <div className="onboarding-hero">
          <div className="hero-icon">🧵</div>
          <h1 id="onboarding-title" className="hero-title">
            Welcome to The Loom
          </h1>
          <p id="onboarding-description" className="hero-subtitle">
            Weave complex interactive narratives with AI-powered assistance
          </p>
        </div>

        {/* Feature Highlights */}
        <div className="onboarding-features">
          <h2 className="features-title">Key Features</h2>
          <div className="features-grid" role="list">
            {FEATURES.map((feature, index) => (
              <div
                key={index}
                className="feature-card"
                role="listitem"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <span className="feature-icon" aria-hidden="true">
                  {feature.icon}
                </span>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-description">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="onboarding-actions">
          <button
            onClick={handleClose}
            className="get-started-btn"
            aria-label="Get started with The Loom"
          >
            Get Started
          </button>

          <label className="dont-show-checkbox">
            <input
              type="checkbox"
              checked={dontShowAgain}
              onChange={handleCheckboxChange}
              aria-label="Do not show this welcome screen again"
            />
            <span>Don&apos;t show again</span>
          </label>
        </div>

        {/* Close button */}
        <button
          onClick={handleClose}
          className="modal-close-btn"
          aria-label="Close welcome modal"
        >
          ×
        </button>
      </div>
    </div>
  )
}
