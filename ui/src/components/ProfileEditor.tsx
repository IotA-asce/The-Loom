import { useState } from 'react'
import { useProfileStore, AVAILABLE_GENRES } from '../stores/profileStore'
import './ProfileEditor.css'

interface ProfileEditorProps {
  isOpen: boolean
  onClose: () => void
}

export function ProfileEditor({ isOpen, onClose }: ProfileEditorProps) {
  const {
    tones,
    overrides,
    genres,
    versions,
    auditTrail,
    activeTab,
    setActiveTab,
    updateTone,
    addOverride,
    removeOverride,
    addGenre,
    removeGenre,
    saveVersion,
    restoreVersion,
    comparingVersionId,
    compareVersions,
    clearComparison,
    getVersionDiff,
  } = useProfileStore()
  
  const [newGenreName, setNewGenreName] = useState('')
  const [newGenreCategory, setNewGenreCategory] = useState<'primary' | 'secondary' | 'theme'>('secondary')
  const [overrideReason, setOverrideReason] = useState('')
  const [versionDescription, setVersionDescription] = useState('')
  const [selectedToneCategory, setSelectedToneCategory] = useState<string | null>(null)
  const [selectedToneValue, setSelectedToneValue] = useState(5)
  
  if (!isOpen) return null
  
  const toneCategories = [
    { key: 'narrative', label: 'Narrative Voice', icon: '📖' },
    { key: 'dialogue', label: 'Dialogue Style', icon: '💬' },
    { key: 'description', label: 'Description Density', icon: '🎨' },
    { key: 'pacing', label: 'Story Pacing', icon: '⏱️' },
    { key: 'atmosphere', label: 'Atmosphere', icon: '🌫️' },
    { key: 'humor', label: 'Humor Level', icon: '😄' },
    { key: 'intensity', label: 'Drama Intensity', icon: '🔥' },
    { key: 'romance', label: 'Romance Level', icon: '💕' },
  ] as const
  
  const getSliderGradient = (value: number) => {
    const percentage = (value / 10) * 100
    return `linear-gradient(to right, var(--accent-primary, #4a9eff) 0%, var(--accent-primary, #4a9eff) ${percentage}%, var(--bg-tertiary, #333) ${percentage}%, var(--bg-tertiary, #333) 100%)`
  }
  
  const getIntensityLabel = (value: number) => {
    if (value <= 2) return 'Minimal'
    if (value <= 4) return 'Light'
    if (value <= 6) return 'Moderate'
    if (value <= 8) return 'Strong'
    return 'Extreme'
  }
  
  const handleSaveVersion = () => {
    if (!versionDescription.trim()) return
    saveVersion(versionDescription)
    setVersionDescription('')
  }
  
  const handleAddOverride = () => {
    if (!selectedToneCategory || !overrideReason.trim()) return
    addOverride({
      category: selectedToneCategory as any,
      setting: toneCategories.find(t => t.key === selectedToneCategory)?.label || selectedToneCategory,
      value: selectedToneValue,
      reason: overrideReason,
    })
    setOverrideReason('')
    setSelectedToneCategory(null)
  }
  
  const handleAddGenre = () => {
    if (!newGenreName.trim()) return
    addGenre(newGenreName, newGenreCategory)
    setNewGenreName('')
  }
  
  const diff = comparingVersionId ? getVersionDiff(comparingVersionId) : null
  const comparingVersion = versions.find(v => v.id === comparingVersionId)
  
  return (
    <div className="profile-overlay" onClick={onClose}>
      <div className="profile-panel" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="profile-header">
          <h2>👤 Profile Editor</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        {/* Tabs */}
        <div className="profile-tabs">
          <button
            className={`tab-btn ${activeTab === 'editor' ? 'active' : ''}`}
            onClick={() => setActiveTab('editor')}
          >
            <span>✏️</span>
            <span>Editor</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'versions' ? 'active' : ''}`}
            onClick={() => setActiveTab('versions')}
          >
            <span>📜</span>
            <span>Versions</span>
            {versions.length > 0 && <span className="tab-badge">{versions.length}</span>}
          </button>
          <button
            className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
            onClick={() => setActiveTab('audit')}
          >
            <span>📋</span>
            <span>Audit Trail</span>
            {auditTrail.length > 0 && <span className="tab-badge">{auditTrail.length}</span>}
          </button>
        </div>
        
        {/* Content */}
        <div className="profile-content">
          {/* Editor Tab */}
          {activeTab === 'editor' && (
            <div className="editor-tab">
              {/* Tone Sliders */}
              <div className="editor-section">
                <h3>🎛️ Tone Adjustments</h3>
                <div className="tone-sliders">
                  {toneCategories.map(({ key, label, icon }) => (
                    <div key={key} className="tone-control">
                      <div className="tone-header">
                        <span className="tone-icon">{icon}</span>
                        <span className="tone-label">{label}</span>
                        <span className="tone-value">
                          {tones[key]} - {getIntensityLabel(tones[key])}
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="10"
                        step="1"
                        value={tones[key]}
                        onChange={(e) => updateTone(key, Number(e.target.value))}
                        className="tone-slider"
                        style={{ background: getSliderGradient(tones[key]) }}
                      />
                      <div className="tone-scale">
                        <span>Min</span>
                        <span>Max</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Overrides */}
              <div className="editor-section">
                <h3>⚡ Active Overrides</h3>
                {overrides.length > 0 ? (
                  <div className="overrides-list">
                    {overrides.map(override => (
                      <div key={override.id} className="override-item">
                        <div className="override-info">
                          <span className="override-setting">{override.setting}</span>
                          <span className="override-value">→ {override.value}</span>
                          <p className="override-reason">{override.reason}</p>
                        </div>
                        <button
                          className="remove-override-btn"
                          onClick={() => removeOverride(override.id)}
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="empty-text">No active overrides</p>
                )}
                
                {/* Add Override */}
                <div className="add-override">
                  <select
                    value={selectedToneCategory || ''}
                    onChange={(e) => setSelectedToneCategory(e.target.value)}
                  >
                    <option value="">Select tone to override...</option>
                    {toneCategories.map(({ key, label }) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </select>
                  {selectedToneCategory && (
                    <>
                      <input
                        type="range"
                        min="0"
                        max="10"
                        value={selectedToneValue}
                        onChange={(e) => setSelectedToneValue(Number(e.target.value))}
                      />
                      <input
                        type="text"
                        placeholder="Reason for override..."
                        value={overrideReason}
                        onChange={(e) => setOverrideReason(e.target.value)}
                      />
                      <button
                        className="add-btn"
                        onClick={handleAddOverride}
                        disabled={!overrideReason.trim()}
                      >
                        Add Override
                      </button>
                    </>
                  )}
                </div>
              </div>
              
              {/* Genre Tags */}
              <div className="editor-section">
                <h3>🏷️ Genre Tags</h3>
                <div className="genre-tags">
                  {genres.map(genre => (
                    <span
                      key={genre.id}
                      className={`genre-tag ${genre.category}`}
                    >
                      {genre.name}
                      <button
                        className="remove-genre-btn"
                        onClick={() => removeGenre(genre.id)}
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
                
                <div className="add-genre">
                  <select
                    value={newGenreName}
                    onChange={(e) => setNewGenreName(e.target.value)}
                  >
                    <option value="">Select genre...</option>
                    {AVAILABLE_GENRES.filter(g => !genres.some(g2 => g2.name === g)).map(genre => (
                      <option key={genre} value={genre}>{genre}</option>
                    ))}
                  </select>
                  <select
                    value={newGenreCategory}
                    onChange={(e) => setNewGenreCategory(e.target.value as any)}
                  >
                    <option value="primary">Primary</option>
                    <option value="secondary">Secondary</option>
                    <option value="theme">Theme</option>
                  </select>
                  <button
                    className="add-btn"
                    onClick={handleAddGenre}
                    disabled={!newGenreName}
                  >
                    Add Genre
                  </button>
                </div>
              </div>
              
              {/* Save Version */}
              <div className="editor-section save-version">
                <h3>💾 Save Version</h3>
                <div className="version-input">
                  <input
                    type="text"
                    placeholder="Version description..."
                    value={versionDescription}
                    onChange={(e) => setVersionDescription(e.target.value)}
                  />
                  <button
                    className="save-btn"
                    onClick={handleSaveVersion}
                    disabled={!versionDescription.trim()}
                  >
                    Save Version
                  </button>
                </div>
              </div>
            </div>
          )}
          
          {/* Versions Tab */}
          {activeTab === 'versions' && (
            <div className="versions-tab">
              {diff && comparingVersion && (
                <div className="diff-panel">
                  <div className="diff-header">
                    <h4>Comparing with {new Date(comparingVersion.timestamp).toLocaleDateString()}</h4>
                    <button className="close-diff" onClick={clearComparison}>×</button>
                  </div>
                  
                  {diff.added.length > 0 && (
                    <div className="diff-section">
                      <h5>Added</h5>
                      <ul>
                        {diff.added.map((item, i) => (
                          <li key={i} className="diff-added">+ {item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {diff.removed.length > 0 && (
                    <div className="diff-section">
                      <h5>Removed</h5>
                      <ul>
                        {diff.removed.map((item, i) => (
                          <li key={i} className="diff-removed">- {item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {diff.changed.length > 0 && (
                    <div className="diff-section">
                      <h5>Changed</h5>
                      <ul>
                        {diff.changed.map((item, i) => (
                          <li key={i} className="diff-changed">~ {item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {diff.added.length === 0 && diff.removed.length === 0 && diff.changed.length === 0 && (
                    <p className="no-diff">No differences found</p>
                  )}
                </div>
              )}
              
              <div className="versions-list">
                {versions.length > 0 ? (
                  versions.map(version => (
                    <div key={version.id} className="version-card">
                      <div className="version-header">
                        <span className="version-date">
                          {new Date(version.timestamp).toLocaleString()}
                        </span>
                        <span className="version-id">{version.id.slice(-6)}</span>
                      </div>
                      <p className="version-description">{version.description}</p>
                      
                      {version.changes.length > 0 && (
                        <div className="version-changes">
                          <span>Recent changes:</span>
                          <ul>
                            {version.changes.slice(0, 3).map((change, i) => (
                              <li key={i}>{change}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      <div className="version-actions">
                        <button
                          className="version-btn"
                          onClick={() => compareVersions(version.id)}
                          disabled={comparingVersionId === version.id}
                        >
                          {comparingVersionId === version.id ? 'Comparing...' : 'Compare'}
                        </button>
                        <button
                          className="version-btn restore"
                          onClick={() => {
                            if (confirm('Restore this version? Current changes will be lost.')) {
                              restoreVersion(version.id)
                            }
                          }}
                        >
                          Restore
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="empty-state">
                    <span className="empty-icon">📜</span>
                    <p>No saved versions</p>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Audit Tab */}
          {activeTab === 'audit' && (
            <div className="audit-tab">
              {auditTrail.length > 0 ? (
                <div className="audit-list">
                  {auditTrail.map(entry => (
                    <div key={entry.id} className={`audit-entry ${entry.action}`}>
                      <div className="audit-header">
                        <span className="audit-action">{entry.action.replace('_', ' ')}</span>
                        <span className="audit-time">
                          {new Date(entry.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <p className="audit-description">{entry.description}</p>
                      {entry.oldValue && entry.newValue && (
                        <div className="audit-change">
                          <span className="old">{entry.oldValue}</span>
                          <span className="arrow">→</span>
                          <span className="new">{entry.newValue}</span>
                        </div>
                      )}
                      {entry.reason && (
                        <p className="audit-reason">Reason: {entry.reason}</p>
                      )}
                      <span className="audit-author">by {entry.author}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <span className="empty-icon">📋</span>
                  <p>No audit entries</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
