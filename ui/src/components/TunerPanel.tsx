import { useEffect } from 'react'
import { useAppStore } from '../store'
import './TunerPanel.css'

export function TunerPanel() {
  const {
    tunerOpen,
    tunerSettings,
    tunerResolution,
    updateTuner,
    toggleTuner,
  } = useAppStore()

  // Update tuner when settings change
  useEffect(() => {
    if (tunerOpen) {
      updateTuner(tunerSettings)
    }
  }, [tunerSettings, tunerOpen, updateTuner])

  if (!tunerOpen) return null

  const handleSliderChange = (key: 'violence' | 'humor' | 'romance', value: number) => {
    updateTuner({ ...tunerSettings, [key]: value })
  }

  const getSliderDescriptor = (value: number, type: string) => {
    const descriptors: Record<string, [string, string, string]> = {
      violence: ['Contained', 'Tense', 'Volatile'],
      humor: ['Dry', 'Wry', 'Playful'],
      romance: ['Subtle', 'Warm', 'Intimate'],
    }
    const options = descriptors[type]
    if (value < 0.34) return options[0]
    if (value < 0.67) return options[1]
    return options[2]
  }

  return (
    <div className="tuner-panel" role="region" aria-labelledby="tuner-title">
      <div className="panel-header">
        <h2 id="tuner-title" className="panel-title">Tuner</h2>
        <button
          onClick={toggleTuner}
          className="close-button"
          aria-label="Close tuner panel"
        >
          ×
        </button>
      </div>
      
      <div className="tuner-controls">
        {/* Violence slider */}
        <div className="tuner-control">
          <label htmlFor="violence-slider" className="control-label">
            <span>Violence</span>
            <span className="control-value">
              {getSliderDescriptor(tunerSettings.violence, 'violence')}
            </span>
          </label>
          <input
            id="violence-slider"
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={tunerSettings.violence}
            onChange={(e) => handleSliderChange('violence', parseFloat(e.target.value))}
            className="tuner-slider violence"
            aria-valuemin={0}
            aria-valuemax={1}
            aria-valuenow={tunerSettings.violence}
            aria-label="Violence intensity"
          />
          <div className="slider-labels">
            <span>Low</span>
            <span>High</span>
          </div>
        </div>

        {/* Humor slider */}
        <div className="tuner-control">
          <label htmlFor="humor-slider" className="control-label">
            <span>Humor</span>
            <span className="control-value">
              {getSliderDescriptor(tunerSettings.humor, 'humor')}
            </span>
          </label>
          <input
            id="humor-slider"
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={tunerSettings.humor}
            onChange={(e) => handleSliderChange('humor', parseFloat(e.target.value))}
            className="tuner-slider humor"
            aria-valuemin={0}
            aria-valuemax={1}
            aria-valuenow={tunerSettings.humor}
            aria-label="Humor level"
          />
          <div className="slider-labels">
            <span>Low</span>
            <span>High</span>
          </div>
        </div>

        {/* Romance slider */}
        <div className="tuner-control">
          <label htmlFor="romance-slider" className="control-label">
            <span>Romance</span>
            <span className="control-value">
              {getSliderDescriptor(tunerSettings.romance, 'romance')}
            </span>
          </label>
          <input
            id="romance-slider"
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={tunerSettings.romance}
            onChange={(e) => handleSliderChange('romance', parseFloat(e.target.value))}
            className="tuner-slider romance"
            aria-valuemin={0}
            aria-valuemax={1}
            aria-valuenow={tunerSettings.romance}
            aria-label="Romance intensity"
          />
          <div className="slider-labels">
            <span>Low</span>
            <span>High</span>
          </div>
        </div>
      </div>

      {/* Warnings */}
      {tunerResolution && tunerResolution.warnings.length > 0 && (
        <div className="tuner-warnings" role="alert">
          <h3 className="warnings-title">⚠️ Warnings</h3>
          <ul className="warnings-list">
            {tunerResolution.warnings.map((warning, index) => (
              <li key={index} className="warning-item">
                {warning}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Preview */}
      {tunerResolution && (
        <div className="tuner-preview" role="status">
          <h3 className="preview-title">Preview</h3>
          <p className="preview-text">
            Tone: {getSliderDescriptor(tunerResolution.violence, 'violence')} conflict,{' '}
            {getSliderDescriptor(tunerResolution.humor, 'humor')} relief,{' '}
            {getSliderDescriptor(tunerResolution.romance, 'romance')} connection
          </p>
          <p className="preview-intensity">
            Expected intensity:{' '}
            <span className="intensity-value">
              {((tunerResolution.violence * 0.6 + tunerResolution.romance * 0.25 + tunerResolution.humor * 0.15) * 100).toFixed(0)}%
            </span>
          </p>
        </div>
      )}

      {/* Precedence info */}
      {tunerResolution && (
        <div className="tuner-precedence">
          <span className="precedence-label">Precedence:</span>
          <span className="precedence-order">
            {tunerResolution.precedenceOrder.join(' > ')}
          </span>
        </div>
      )}
    </div>
  )
}
