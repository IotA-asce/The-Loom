import { useState, useEffect } from 'react'
import { useAppStore } from '../store'
import './ArtistPanel.css'

// Atmosphere presets
const ATMOSPHERE_PRESETS = [
  { 
    id: 'light', 
    name: 'Light / Wholesome', 
    description: 'Bright, optimistic, warm tones',
    lighting: { direction: 'top', intensity: 0.8, contrast: 0.3 },
    texture: { detail: 0.5, style: 'clean', weathering: 0.1 }
  },
  { 
    id: 'neutral', 
    name: 'Neutral / Dramatic', 
    description: 'Balanced, cinematic lighting',
    lighting: { direction: 'side', intensity: 0.6, contrast: 0.5 },
    texture: { detail: 0.6, style: 'natural', weathering: 0.3 }
  },
  { 
    id: 'dark', 
    name: 'Dark / Moody', 
    description: 'Low-key, mysterious atmosphere',
    lighting: { direction: 'bottom', intensity: 0.3, contrast: 0.8 },
    texture: { detail: 0.7, style: 'gritty', weathering: 0.5 }
  },
  { 
    id: 'horror', 
    name: 'Horror', 
    description: 'Harsh, unsettling, high contrast',
    lighting: { direction: 'below', intensity: 0.2, contrast: 0.9 },
    texture: { detail: 0.8, style: 'gritty', weathering: 0.7 }
  },
]

// Shot types
const SHOT_TYPES = [
  { id: 'wide', name: 'Wide', description: 'Establishes location' },
  { id: 'medium', name: 'Medium', description: 'Shows character + environment' },
  { id: 'close', name: 'Close-up', description: 'Focus on face/expression' },
  { id: 'extreme', name: 'Extreme Close', description: 'Detail shot' },
]

// Camera angles
const CAMERA_ANGLES = [
  { id: 'eye', name: 'Eye Level', description: 'Neutral, natural' },
  { id: 'high', name: 'High Angle', description: 'Looking down - makes subject smaller' },
  { id: 'low', name: 'Low Angle', description: 'Looking up - makes subject powerful' },
  { id: 'dutch', name: 'Dutch Angle', description: 'Tilted - creates tension' },
]

// Aspect ratios
const ASPECT_RATIOS = [
  { id: '1:1', name: '1:1', value: 1 },
  { id: '4:3', name: '4:3', value: 4/3 },
  { id: '16:9', name: '16:9', value: 16/9 },
  { id: '9:16', name: '9:16', value: 9/16 },
  { id: '21:9', name: 'Cinematic', value: 21/9 },
]

// Samplers
const SAMPLERS = ['Euler', 'Euler a', 'Heun', 'DPM++ 2M', 'DPM++ 2M Karras', 'DDIM']

export function ArtistPanel() {
  const {
    nodes,
    selectedNodeId,
    characters,
    toggleArtistPanel,
    artistPanelOpen,
    sceneBlueprints,
    generatedPanels,
    generationQueue,
    activeGeneration,
    atmosphereSettings,
    setAtmospherePreset,
    updateAtmosphereSettings,
    createSceneBlueprint,
    generatePanels,
    cancelPanelGeneration,
    deleteGeneratedPanel,
    regeneratePanel,
    viewerMode,
    setViewerMode,
    selectedPanelId,
    selectPanel,
    continuityIssues,
  } = useAppStore()

  const [activeTab, setActiveTab] = useState<'blueprint' | 'atmosphere' | 'panels' | 'queue'>('blueprint')
  // Reader mode state placeholder for future use
  const [selectedPanels, setSelectedPanels] = useState<string[]>([])
  const [batchMode, setBatchMode] = useState(false)
  
  // Blueprint state
  const [blueprint, setBlueprint] = useState({
    setting: '',
    timeOfDay: '',
    weather: '',
    lightingDirection: 'top',
    lightingIntensity: 0.5,
    shotType: 'medium',
    cameraAngle: 'eye',
    focusPoint: '',
    props: [] as string[],
    characters: [] as Array<{
      characterId: string
      position: 'left' | 'center' | 'right' | 'background'
      pose: string
      expression: string
    }>,
  })
  
  // Generation params
  const [genParams, setGenParams] = useState({
    panelCount: 4,
    aspectRatio: '16:9',
    seed: '',
    cfgScale: 7,
    steps: 20,
    sampler: 'DPM++ 2M Karras',
    negativePrompt: '',
  })
  
  // New prop input
  const [newProp, setNewProp] = useState('')
  
  const selectedNode = nodes.find(n => n.id === selectedNodeId)
  
  // Load existing blueprint when node changes
  useEffect(() => {
    if (selectedNodeId && sceneBlueprints[selectedNodeId]) {
      setBlueprint(sceneBlueprints[selectedNodeId])
    }
  }, [selectedNodeId, sceneBlueprints])

  if (!artistPanelOpen) return null

  const handleSaveBlueprint = () => {
    if (selectedNodeId) {
      createSceneBlueprint(selectedNodeId, blueprint)
    }
  }
  
  const handleGenerate = () => {
    if (!selectedNodeId) return
    generatePanels({
      nodeId: selectedNodeId,
      blueprint,
      atmosphere: atmosphereSettings,
      params: genParams,
    })
  }
  
  const handleAddProp = () => {
    if (newProp.trim() && !blueprint.props.includes(newProp.trim())) {
      setBlueprint(prev => ({
        ...prev,
        props: [...prev.props, newProp.trim()]
      }))
      setNewProp('')
    }
  }
  
  const handleRemoveProp = (prop: string) => {
    setBlueprint(prev => ({
      ...prev,
      props: prev.props.filter(p => p !== prop)
    }))
  }
  
  const handleCharacterToggle = (characterId: string) => {
    setBlueprint(prev => {
      const exists = prev.characters.find(c => c.characterId === characterId)
      if (exists) {
        return {
          ...prev,
          characters: prev.characters.filter(c => c.characterId !== characterId)
        }
      }
      return {
        ...prev,
        characters: [...prev.characters, {
          characterId,
          position: 'center',
          pose: '',
          expression: 'neutral'
        }]
      }
    })
  }
  
  const updateCharacterInBlueprint = (characterId: string, updates: Partial<typeof blueprint.characters[0]>) => {
    setBlueprint(prev => ({
      ...prev,
      characters: prev.characters.map(c =>
        c.characterId === characterId ? { ...c, ...updates } : c
      )
    }))
  }
  
  const handlePresetSelect = (presetId: string) => {
    const preset = ATMOSPHERE_PRESETS.find(p => p.id === presetId)
    if (preset) {
      setAtmospherePreset(presetId)
      updateAtmosphereSettings(preset.lighting)
    }
  }
  
  const togglePanelSelection = (panelId: string) => {
    setSelectedPanels(prev =>
      prev.includes(panelId)
        ? prev.filter(id => id !== panelId)
        : [...prev, panelId]
    )
  }
  
  const handleBatchDelete = () => {
    selectedPanels.forEach(id => deleteGeneratedPanel(id))
    setSelectedPanels([])
    setBatchMode(false)
  }
  
  const handleBatchRegenerate = () => {
    selectedPanels.forEach(id => regeneratePanel(id))
    setSelectedPanels([])
    setBatchMode(false)
  }

  // Get panels for current node
  const currentPanels = selectedNodeId 
    ? generatedPanels.filter(p => p.nodeId === selectedNodeId)
    : []

  return (
    <div className="artist-panel" role="region" aria-labelledby="artist-title">
      <div className="panel-header">
        <h2 id="artist-title" className="panel-title">🎨 Artist</h2>
        <button
          onClick={toggleArtistPanel}
          className="close-button"
          aria-label="Close artist panel"
        >
          ×
        </button>
      </div>

      {!selectedNodeId ? (
        <div className="empty-state">
          <p>Select a node to generate images</p>
        </div>
      ) : (
        <>
          {/* Node info */}
          <div className="node-info">
            <span className="node-label">{selectedNode?.label}</span>
            <span className="node-type">{selectedNode?.type}</span>
          </div>

          {/* Tabs */}
          <div className="artist-tabs" role="tablist">
            <button
              role="tab"
              aria-selected={activeTab === 'blueprint'}
              onClick={() => setActiveTab('blueprint')}
              className={activeTab === 'blueprint' ? 'active' : ''}
            >
              Blueprint
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'atmosphere'}
              onClick={() => setActiveTab('atmosphere')}
              className={activeTab === 'atmosphere' ? 'active' : ''}
            >
              Atmosphere
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'panels'}
              onClick={() => setActiveTab('panels')}
              className={activeTab === 'panels' ? 'active' : ''}
            >
              Panels ({currentPanels.length})
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'queue'}
              onClick={() => setActiveTab('queue')}
              className={activeTab === 'queue' ? 'active' : ''}
            >
              Queue ({generationQueue.length})
            </button>
          </div>

          {/* Blueprint Tab */}
          {activeTab === 'blueprint' && (
            <div className="tab-content">
              <div className="blueprint-section">
                <h3>Scene Elements</h3>
                
                <div className="form-grid">
                  <div className="form-field">
                    <label>Setting / Location</label>
                    <textarea
                      value={blueprint.setting}
                      onChange={(e) => setBlueprint(prev => ({ ...prev, setting: e.target.value }))}
                      placeholder="Describe the setting..."
                      rows={2}
                    />
                  </div>
                  
                  <div className="form-row">
                    <div className="form-field">
                      <label>Time of Day</label>
                      <select
                        value={blueprint.timeOfDay}
                        onChange={(e) => setBlueprint(prev => ({ ...prev, timeOfDay: e.target.value }))}
                      >
                        <option value="">Select...</option>
                        <option value="dawn">Dawn</option>
                        <option value="morning">Morning</option>
                        <option value="noon">Noon</option>
                        <option value="afternoon">Afternoon</option>
                        <option value="evening">Evening</option>
                        <option value="dusk">Dusk</option>
                        <option value="night">Night</option>
                        <option value="midnight">Midnight</option>
                      </select>
                    </div>
                    
                    <div className="form-field">
                      <label>Weather</label>
                      <select
                        value={blueprint.weather}
                        onChange={(e) => setBlueprint(prev => ({ ...prev, weather: e.target.value }))}
                      >
                        <option value="">Select...</option>
                        <option value="clear">Clear</option>
                        <option value="cloudy">Cloudy</option>
                        <option value="rainy">Rainy</option>
                        <option value="stormy">Stormy</option>
                        <option value="foggy">Foggy</option>
                        <option value="snowy">Snowy</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              <div className="blueprint-section">
                <h3>Camera</h3>
                
                <div className="form-row">
                  <div className="form-field">
                    <label>Shot Type</label>
                    <div className="button-group">
                      {SHOT_TYPES.map(shot => (
                        <button
                          key={shot.id}
                          onClick={() => setBlueprint(prev => ({ ...prev, shotType: shot.id }))}
                          className={blueprint.shotType === shot.id ? 'active' : ''}
                          title={shot.description}
                        >
                          {shot.name}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div className="form-row">
                  <div className="form-field">
                    <label>Camera Angle</label>
                    <div className="button-group">
                      {CAMERA_ANGLES.map(angle => (
                        <button
                          key={angle.id}
                          onClick={() => setBlueprint(prev => ({ ...prev, cameraAngle: angle.id }))}
                          className={blueprint.cameraAngle === angle.id ? 'active' : ''}
                          title={angle.description}
                        >
                          {angle.name}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div className="form-field">
                  <label>Focus Point</label>
                  <input
                    type="text"
                    value={blueprint.focusPoint}
                    onChange={(e) => setBlueprint(prev => ({ ...prev, focusPoint: e.target.value }))}
                    placeholder="What should be in focus? (e.g., 'character face', 'distant mountain')"
                  />
                </div>
              </div>

              <div className="blueprint-section">
                <h3>Characters</h3>
                
                <div className="character-positioning">
                  {characters.map(char => {
                    const inScene = blueprint.characters.find(c => c.characterId === char.id)
                    return (
                      <div 
                        key={char.id} 
                        className={`character-position-card ${inScene ? 'in-scene' : ''}`}
                      >
                        <div className="char-header">
                          <label className="char-checkbox">
                            <input
                              type="checkbox"
                              checked={!!inScene}
                              onChange={() => handleCharacterToggle(char.id)}
                            />
                            <span className="char-name">{char.name}</span>
                          </label>
                        </div>
                        
                        {inScene && (
                          <div className="char-details">
                            <div className="char-controls">
                              <select
                                value={inScene.position}
                                onChange={(e) => updateCharacterInBlueprint(char.id, { 
                                  position: e.target.value as typeof inScene.position 
                                })}
                              >
                                <option value="left">Left</option>
                                <option value="center">Center</option>
                                <option value="right">Right</option>
                                <option value="background">Background</option>
                              </select>
                              
                              <input
                                type="text"
                                value={inScene.pose}
                                onChange={(e) => updateCharacterInBlueprint(char.id, { pose: e.target.value })}
                                placeholder="Pose (e.g., standing, sitting)"
                              />
                              
                              <select
                                value={inScene.expression}
                                onChange={(e) => updateCharacterInBlueprint(char.id, { expression: e.target.value })}
                              >
                                <option value="neutral">Neutral</option>
                                <option value="happy">Happy</option>
                                <option value="sad">Sad</option>
                                <option value="angry">Angry</option>
                                <option value="surprised">Surprised</option>
                                <option value="fearful">Fearful</option>
                                <option value="determined">Determined</option>
                              </select>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="blueprint-section">
                <h3>Props & Environment</h3>
                
                <div className="props-list">
                  {blueprint.props.map(prop => (
                    <span key={prop} className="prop-tag">
                      {prop}
                      <button onClick={() => handleRemoveProp(prop)}>×</button>
                    </span>
                  ))}
                </div>
                
                <div className="prop-input">
                  <input
                    type="text"
                    value={newProp}
                    onChange={(e) => setNewProp(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddProp()}
                    placeholder="Add a prop..."
                  />
                  <button onClick={handleAddProp}>Add</button>
                </div>
              </div>

              <button 
                onClick={handleSaveBlueprint}
                className="save-blueprint-btn"
              >
                💾 Save Blueprint
              </button>
            </div>
          )}

          {/* Atmosphere Tab */}
          {activeTab === 'atmosphere' && (
            <div className="tab-content">
              <div className="atmosphere-section">
                <h3>Atmosphere Presets</h3>
                
                <div className="preset-grid">
                  {ATMOSPHERE_PRESETS.map(preset => (
                    <button
                      key={preset.id}
                      onClick={() => handlePresetSelect(preset.id)}
                      className={`atmosphere-preset ${atmosphereSettings.presetId === preset.id ? 'active' : ''}`}
                    >
                      <span className="preset-name">{preset.name}</span>
                      <span className="preset-desc">{preset.description}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="atmosphere-section">
                <h3>Lighting</h3>
                
                <div className="lighting-controls">
                  <div className="control-row">
                    <label>Direction</label>
                    <div className="direction-picker">
                      {['top', 'side', 'bottom', 'front', 'back'].map(dir => (
                        <button
                          key={dir}
                          onClick={() => updateAtmosphereSettings({ direction: dir })}
                          className={atmosphereSettings.direction === dir ? 'active' : ''}
                          title={`${dir} light`}
                        >
                          {dir === 'top' && '⬇️'}
                          {dir === 'bottom' && '⬆️'}
                          {dir === 'side' && '➡️'}
                          {dir === 'front' && '🎭'}
                          {dir === 'back' && '🔲'}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <div className="control-row">
                    <label>Intensity</label>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.1}
                      value={atmosphereSettings.intensity}
                      onChange={(e) => updateAtmosphereSettings({ intensity: parseFloat(e.target.value) })}
                    />
                    <span>{(atmosphereSettings.intensity * 100).toFixed(0)}%</span>
                  </div>
                  
                  <div className="control-row">
                    <label>Contrast</label>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.1}
                      value={atmosphereSettings.contrast}
                      onChange={(e) => updateAtmosphereSettings({ contrast: parseFloat(e.target.value) })}
                    />
                    <span>{(atmosphereSettings.contrast * 100).toFixed(0)}%</span>
                  </div>
                  
                  <div className="control-row">
                    <label>Shadow Hardness</label>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.1}
                      value={atmosphereSettings.shadowHardness || 0.5}
                      onChange={(e) => updateAtmosphereSettings({ shadowHardness: parseFloat(e.target.value) })}
                    />
                    <span>{((atmosphereSettings.shadowHardness || 0.5) * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>

              <div className="atmosphere-section">
                <h3>Texture</h3>
                
                <div className="texture-controls">
                  <div className="control-row">
                    <label>Detail Level</label>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.1}
                      value={atmosphereSettings.textureDetail || 0.5}
                      onChange={(e) => updateAtmosphereSettings({ textureDetail: parseFloat(e.target.value) })}
                    />
                    <span>{((atmosphereSettings.textureDetail || 0.5) * 100).toFixed(0)}%</span>
                  </div>
                  
                  <div className="control-row">
                    <label>Style</label>
                    <div className="style-toggle">
                      <button
                        onClick={() => updateAtmosphereSettings({ textureStyle: 'clean' })}
                        className={atmosphereSettings.textureStyle === 'clean' ? 'active' : ''}
                      >
                        Clean
                      </button>
                      <button
                        onClick={() => updateAtmosphereSettings({ textureStyle: 'gritty' })}
                        className={atmosphereSettings.textureStyle === 'gritty' ? 'active' : ''}
                      >
                        Gritty
                      </button>
                    </div>
                  </div>
                  
                  <div className="control-row">
                    <label>Weathering</label>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.1}
                      value={atmosphereSettings.weathering || 0.3}
                      onChange={(e) => updateAtmosphereSettings({ weathering: parseFloat(e.target.value) })}
                    />
                    <span>{((atmosphereSettings.weathering || 0.3) * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>

              <div className="atmosphere-preview">
                <h3>Preview</h3>
                <div 
                  className="preview-box"
                  style={{
                    background: `linear-gradient(${atmosphereSettings.direction === 'top' ? '180deg' : 
                      atmosphereSettings.direction === 'bottom' ? '0deg' : '90deg'}, 
                      rgba(255,255,255,${atmosphereSettings.intensity}), 
                      rgba(0,0,0,${atmosphereSettings.contrast}))`,
                    filter: `contrast(${1 + atmosphereSettings.contrast})`,
                  }}
                >
                  <span className="preview-label">
                    {ATMOSPHERE_PRESETS.find(p => p.id === atmosphereSettings.presetId)?.name || 'Custom'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Panels Tab */}
          {activeTab === 'panels' && (
            <div className="tab-content">
              {/* View mode toggle */}
              <div className="view-controls">
                <div className="view-toggle">
                  <button
                    onClick={() => setViewerMode('grid')}
                    className={viewerMode === 'grid' ? 'active' : ''}
                  >
                    ⊞ Grid
                  </button>
                  <button
                    onClick={() => setViewerMode('sequential')}
                    className={viewerMode === 'sequential' ? 'active' : ''}
                  >
                    ⇢ Sequential
                  </button>
                  <button
                    onClick={() => setViewerMode('split')}
                    className={viewerMode === 'split' ? 'active' : ''}
                  >
                    ⚏ Split
                  </button>
                </div>
                
                <div className="batch-controls">
                  <button
                    onClick={() => setBatchMode(!batchMode)}
                    className={batchMode ? 'active' : ''}
                  >
                    Batch
                  </button>
                  {batchMode && selectedPanels.length > 0 && (
                    <>
                      <button onClick={handleBatchRegenerate}>
                        🔄 Regenerate ({selectedPanels.length})
                      </button>
                      <button onClick={handleBatchDelete} className="danger">
                        🗑️ Delete ({selectedPanels.length})
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Grid View */}
              {viewerMode === 'grid' && (
                <div className="panels-grid">
                  {currentPanels.length === 0 ? (
                    <p className="empty-text">No panels generated yet</p>
                  ) : (
                    currentPanels.map((panel, index) => {
                      const issue = continuityIssues.find(i => i.panelId === panel.id)
                      return (
                        <div
                          key={panel.id}
                          className={`panel-card ${selectedPanels.includes(panel.id) ? 'selected' : ''} ${issue ? 'has-issue' : ''}`}
                          onClick={() => batchMode ? togglePanelSelection(panel.id) : selectPanel(panel.id)}
                        >
                          {batchMode && (
                            <input
                              type="checkbox"
                              checked={selectedPanels.includes(panel.id)}
                              onChange={() => togglePanelSelection(panel.id)}
                              onClick={(e) => e.stopPropagation()}
                              className="panel-checkbox"
                            />
                          )}
                          <div className="panel-number">{index + 1}</div>
                          <div className="panel-image">
                            {panel.url ? (
                              <img src={panel.url} alt={`Panel ${index + 1}`} loading="lazy" />
                            ) : (
                              <div className="panel-placeholder">🖼️</div>
                            )}
                          </div>
                          {issue && (
                            <div className={`issue-badge ${issue.severity}`} title={issue.message}>
                              ⚠️
                            </div>
                          )}
                          <div className="panel-actions">
                            <button 
                              onClick={(e) => { e.stopPropagation(); regeneratePanel(panel.id) }}
                              title="Regenerate"
                            >
                              🔄
                            </button>
                            <button 
                              onClick={(e) => { e.stopPropagation(); deleteGeneratedPanel(panel.id) }}
                              title="Delete"
                              className="danger"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                      )
                    })
                  )}
                </div>
              )}

              {/* Sequential View */}
              {viewerMode === 'sequential' && (
                <div className="panels-sequential">
                  {currentPanels.length === 0 ? (
                    <p className="empty-text">No panels generated yet</p>
                  ) : (
                    <>
                      <div className="reader-progress">
                        <div 
                          className="progress-bar"
                          style={{ width: `${((selectedPanelId ? currentPanels.findIndex(p => p.id === selectedPanelId) + 1 : 1) / currentPanels.length) * 100}%` }}
                        />
                      </div>
                      
                      <div className="reader-view">
                        {selectedPanelId ? (
                          <>
                            <button 
                              className="reader-nav prev"
                              onClick={() => {
                                const idx = currentPanels.findIndex(p => p.id === selectedPanelId)
                                if (idx > 0) selectPanel(currentPanels[idx - 1].id)
                              }}
                              disabled={currentPanels.findIndex(p => p.id === selectedPanelId) === 0 || !selectedPanelId}
                            >
                              ←
                            </button>
                            
                            <div className="reader-panel">
                              {currentPanels.find(p => p.id === selectedPanelId)?.url ? (
                                <img 
                                  src={currentPanels.find(p => p.id === selectedPanelId)?.url || ''} 
                                  alt="Current panel"
                                />
                              ) : (
                                <div className="panel-placeholder large">🖼️</div>
                              )}
                              <div className="reader-info">
                                {currentPanels.findIndex(p => p.id === selectedPanelId) + 1} / {currentPanels.length}
                              </div>
                            </div>
                            
                            <button 
                              className="reader-nav next"
                              onClick={() => {
                                const idx = currentPanels.findIndex(p => p.id === selectedPanelId)
                                if (idx < currentPanels.length - 1) selectPanel(currentPanels[idx + 1].id)
                              }}
                              disabled={currentPanels.findIndex(p => p.id === selectedPanelId) === currentPanels.length - 1 || !selectedPanelId}
                            >
                              →
                            </button>
                          </>
                        ) : (
                          <p>Select a panel to view</p>
                        )}
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Split View */}
              {viewerMode === 'split' && (
                <div className="panels-split">
                  <div className="split-source">
                    <h4>Source Text</h4>
                    <div className="source-text">
                      {selectedNode?.content.text || 'No text available'}
                    </div>
                  </div>
                  <div className="split-panels">
                    <h4>Generated Panels</h4>
                    <div className="split-grid">
                      {currentPanels.map((panel, index) => (
                        <div key={panel.id} className="split-panel-item">
                          <span className="split-number">{index + 1}</span>
                          {panel.url ? (
                            <img src={panel.url} alt={`Panel ${index + 1}`} />
                          ) : (
                            <div className="panel-placeholder">🖼️</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Queue Tab */}
          {activeTab === 'queue' && (
            <div className="tab-content">
              <div className="queue-section">
                <h3>Generation Request</h3>
                
                <div className="gen-params">
                  <div className="param-row">
                    <label>Panel Count</label>
                    <input
                      type="number"
                      min={1}
                      max={16}
                      value={genParams.panelCount}
                      onChange={(e) => setGenParams(prev => ({ ...prev, panelCount: parseInt(e.target.value) || 1 }))}
                    />
                  </div>
                  
                  <div className="param-row">
                    <label>Aspect Ratio</label>
                    <div className="ratio-options">
                      {ASPECT_RATIOS.map(ratio => (
                        <button
                          key={ratio.id}
                          onClick={() => setGenParams(prev => ({ ...prev, aspectRatio: ratio.id }))}
                          className={genParams.aspectRatio === ratio.id ? 'active' : ''}
                        >
                          {ratio.name}
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <div className="param-row">
                    <label>Seed (optional)</label>
                    <input
                      type="text"
                      value={genParams.seed}
                      onChange={(e) => setGenParams(prev => ({ ...prev, seed: e.target.value }))}
                      placeholder="Random"
                    />
                  </div>
                </div>
              </div>

              <details className="advanced-options">
                <summary>Advanced Options</summary>
                
                <div className="param-row">
                  <label>CFG Scale</label>
                  <input
                    type="range"
                    min={1}
                    max={15}
                    step={0.5}
                    value={genParams.cfgScale}
                    onChange={(e) => setGenParams(prev => ({ ...prev, cfgScale: parseFloat(e.target.value) }))}
                  />
                  <span>{genParams.cfgScale}</span>
                </div>
                
                <div className="param-row">
                  <label>Steps</label>
                  <input
                    type="range"
                    min={10}
                    max={50}
                    step={5}
                    value={genParams.steps}
                    onChange={(e) => setGenParams(prev => ({ ...prev, steps: parseInt(e.target.value) }))}
                  />
                  <span>{genParams.steps}</span>
                </div>
                
                <div className="param-row">
                  <label>Sampler</label>
                  <select
                    value={genParams.sampler}
                    onChange={(e) => setGenParams(prev => ({ ...prev, sampler: e.target.value }))}
                  >
                    {SAMPLERS.map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
                
                <div className="param-row">
                  <label>Negative Prompt</label>
                  <textarea
                    value={genParams.negativePrompt}
                    onChange={(e) => setGenParams(prev => ({ ...prev, negativePrompt: e.target.value }))}
                    placeholder="What to avoid..."
                    rows={2}
                  />
                </div>
              </details>

              {/* Queue List */}
              {generationQueue.length > 0 && (
                <div className="queue-list">
                  <h3>Queue ({generationQueue.length})</h3>
                  {generationQueue.map((item, index) => (
                    <div key={item.id} className={`queue-item ${item.status}`}>
                      <span className="queue-index">{index + 1}</span>
                      <span className="queue-info">
                        {item.panelCount} panels - {item.aspectRatio}
                      </span>
                      <span className="queue-status">{item.status}</span>
                      {item.status === 'pending' && (
                        <button onClick={() => cancelPanelGeneration()}>
                          Cancel
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Active Generation */}
              {activeGeneration && (
                <div className="active-generation">
                  <h3>Generating...</h3>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill"
                      style={{ width: `${activeGeneration.progress}%` }}
                    />
                  </div>
                  <p>{activeGeneration.currentStep}</p>
                  <button onClick={() => cancelPanelGeneration()} className="cancel-btn">
                    Cancel
                  </button>
                </div>
              )}

              <button
                onClick={handleGenerate}
                disabled={activeGeneration !== null}
                className="generate-btn"
              >
                {activeGeneration ? 'Generating...' : '🎨 Generate Panels'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
