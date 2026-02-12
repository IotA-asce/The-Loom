import { useState } from 'react'
import './ExtractionSettingsPanel.css'

export interface ExtractionSettings {
  detailLevel: 'summary' | 'standard' | 'detailed'
  language: 'auto' | 'ja' | 'en' | 'zh' | 'ko'
  preseedCharacters: string[]
  chunkSize: 'auto' | '4' | '8' | '12' | '16'
  enableCheckpointing: boolean
  saveRawResponses: boolean
}

const DEFAULT_SETTINGS: ExtractionSettings = {
  detailLevel: 'standard',
  language: 'auto',
  preseedCharacters: [],
  chunkSize: 'auto',
  enableCheckpointing: true,
  saveRawResponses: true,
}

interface ExtractionSettingsPanelProps {
  settings: ExtractionSettings
  onChange: (settings: ExtractionSettings) => void
  onClose: () => void
  mangaTitle?: string
}

export function ExtractionSettingsPanel({
  settings,
  onChange,
  onClose,
  mangaTitle,
}: ExtractionSettingsPanelProps) {
  const [localSettings, setLocalSettings] = useState<ExtractionSettings>({
    ...DEFAULT_SETTINGS,
    ...settings,
  })
  const [characterInput, setCharacterInput] = useState('')

  const handleChange = <K extends keyof ExtractionSettings>(
    key: K,
    value: ExtractionSettings[K]
  ) => {
    const newSettings = { ...localSettings, [key]: value }
    setLocalSettings(newSettings)
    onChange(newSettings)
  }

  const addCharacter = () => {
    if (characterInput.trim() && !localSettings.preseedCharacters.includes(characterInput.trim())) {
      handleChange('preseedCharacters', [
        ...localSettings.preseedCharacters,
        characterInput.trim(),
      ])
      setCharacterInput('')
    }
  }

  const removeCharacter = (char: string) => {
    handleChange(
      'preseedCharacters',
      localSettings.preseedCharacters.filter((c) => c !== char)
    )
  }

  return (
    <div className="extraction-settings-overlay" onClick={onClose}>
      <div className="extraction-settings-panel" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <h3>{mangaTitle ? `Extract: ${mangaTitle}` : 'Extraction Settings'}</h3>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="settings-content">
          {/* Detail Level */}
          <div className="setting-group">
            <label className="setting-label">
              Detail Level
              <span className="setting-hint">Controls extraction depth and token usage</span>
            </label>
            <div className="setting-options">
              {[
                { value: 'summary', label: 'Summary', desc: 'Faster, less detail' },
                { value: 'standard', label: 'Standard', desc: 'Balanced' },
                { value: 'detailed', label: 'Detailed', desc: 'Slower, comprehensive' },
              ].map((opt) => (
                <button
                  key={opt.value}
                  className={`option-btn ${localSettings.detailLevel === opt.value ? 'active' : ''}`}
                  onClick={() => handleChange('detailLevel', opt.value as ExtractionSettings['detailLevel'])}
                >
                  <span className="option-label">{opt.label}</span>
                  <span className="option-desc">{opt.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Language */}
          <div className="setting-group">
            <label className="setting-label">Source Language</label>
            <select
              value={localSettings.language}
              onChange={(e) => handleChange('language', e.target.value as ExtractionSettings['language'])}
              className="setting-select"
            >
              <option value="auto">Auto-detect</option>
              <option value="ja">Japanese</option>
              <option value="en">English</option>
              <option value="zh">Chinese</option>
              <option value="ko">Korean</option>
            </select>
          </div>

          {/* Chunk Size */}
          <div className="setting-group">
            <label className="setting-label">
              Chunk Size
              <span className="setting-hint">Pages processed per API call</span>
            </label>
            <div className="setting-options horizontal">
              {[
                { value: 'auto', label: 'Auto' },
                { value: '4', label: '4 pages' },
                { value: '8', label: '8 pages' },
                { value: '12', label: '12 pages' },
                { value: '16', label: '16 pages' },
              ].map((opt) => (
                <button
                  key={opt.value}
                  className={`option-btn small ${localSettings.chunkSize === opt.value ? 'active' : ''}`}
                  onClick={() => handleChange('chunkSize', opt.value as ExtractionSettings['chunkSize'])}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Pre-seed Characters */}
          <div className="setting-group">
            <label className="setting-label">
              Known Characters
              <span className="setting-hint">Help AI identify characters correctly</span>
            </label>
            <div className="character-input-row">
              <input
                type="text"
                value={characterInput}
                onChange={(e) => setCharacterInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addCharacter()}
                placeholder="Character name..."
                className="character-input"
              />
              <button onClick={addCharacter} className="add-btn">
                Add
              </button>
            </div>
            <div className="character-tags">
              {localSettings.preseedCharacters.map((char) => (
                <span key={char} className="character-tag">
                  {char}
                  <button onClick={() => removeCharacter(char)} className="remove-btn">
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Advanced Options */}
          <div className="setting-group advanced">
            <label className="setting-label">Advanced Options</label>
            <div className="checkbox-row">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={localSettings.enableCheckpointing}
                  onChange={(e) => handleChange('enableCheckpointing', e.target.checked)}
                />
                <span>Enable checkpointing (resume if interrupted)</span>
              </label>
            </div>
            <div className="checkbox-row">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={localSettings.saveRawResponses}
                  onChange={(e) => handleChange('saveRawResponses', e.target.checked)}
                />
                <span>Save raw LLM responses (for debugging)</span>
              </label>
            </div>
          </div>

          {/* Token Estimate */}
          <div className="token-estimate">
            <h4>Estimated Token Usage</h4>
            <div className="estimate-grid">
              <div className="estimate-item">
                <span className="estimate-label">Vision tokens:</span>
                <span className="estimate-value">~256 per page</span>
              </div>
              <div className="estimate-item">
                <span className="estimate-label">Output tokens:</span>
                <span className="estimate-value">~500 per page</span>
              </div>
              <div className="estimate-item">
                <span className="estimate-label">Overhead:</span>
                <span className="estimate-value">10%</span>
              </div>
            </div>
          </div>
        </div>

        <div className="settings-footer">
          <button className="reset-btn" onClick={() => setLocalSettings(DEFAULT_SETTINGS)}>
            Reset to Defaults
          </button>
          <button className="done-btn" onClick={onClose}>
            {mangaTitle ? 'Start Extraction' : 'Done'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ExtractionSettingsPanel
