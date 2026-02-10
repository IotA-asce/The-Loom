import { useEffect, useState, useRef, useCallback } from 'react'
import { useAppStore } from '../store'
import './WriterPanel.css'

// Available models
const MODELS = [
  { id: 'default', name: 'Default', description: 'Balanced quality and speed' },
  { id: 'fast', name: 'Fast', description: 'Quick generation, lower quality' },
  { id: 'quality', name: 'Quality', description: 'Higher quality, slower' },
  { id: 'creative', name: 'Creative', description: 'More creative outputs' },
]

// Context window options
const CONTEXT_WINDOWS = [
  { value: 2048, label: '2K', description: 'Fast' },
  { value: 4096, label: '4K', description: 'Standard' },
  { value: 8192, label: '8K', description: 'Extended' },
  { value: 16384, label: '16K', description: 'Maximum' },
]

export function WriterPanel() {
  const {
    writerPanelOpen,
    selectedNodeId,
    nodes,
    characters,
    tunerSettings,
    generationParams,
    contextChunks,
    styleExemplars,
    contextPresets,
    activePresetId,
    generationResults,
    currentGeneration,
    contradictions,
    expandedContradictions,
    loading,
    toggleWriterPanel,
    retrieveContext,
    toggleContextChunk,
    expandContextChunk,
    removeContextChunk,
    retrieveStyleExemplars,
    toggleStyleExemplar,
    setStyleGuide,
    generateText,
    cancelGeneration,
    acceptGeneration,
    rejectGeneration,
    updateGenerationParams,
    saveContextPreset,
    loadContextPreset,
    deleteContextPreset,
    toggleVoiceEnforcement,
    toggleCharacterFocus,
    expandContradiction,
    editGenerationInline,
  } = useAppStore()

  const [activeTab, setActiveTab] = useState<'generate' | 'context' | 'style' | 'characters'>('generate')
  const [localPrompt, setLocalPrompt] = useState('')
  const [estimatedTime, setEstimatedTime] = useState<number | null>(null)
  const [progress, setProgress] = useState(0)
  const abortControllerRef = useRef<AbortController | null>(null)
  const progressIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  
  // Character filtering
  const [characterQuery, setCharacterQuery] = useState('')
  const [characterSort, setCharacterSort] = useState<'name' | 'importance' | 'appearance'>('name')
  
  // Context search
  const [contextSearchQuery, setContextSearchQuery] = useState('')
  
  // Inline editing
  const [editingGenerationId, setEditingGenerationId] = useState<string | null>(null)
  const [editText, setEditText] = useState('')
  
  // Preset name input
  const [presetName, setPresetName] = useState('')
  const [showPresetInput, setShowPresetInput] = useState(false)

  const selectedNode = nodes.find(n => n.id === selectedNodeId)
  
  // Calculate token budget
  const calculateTokens = useCallback((text: string) => Math.ceil(text.split(/\s+/).filter(w => w.length > 0).length / 0.75), [])
  
  const promptTokens = calculateTokens(localPrompt)
  const contextTokens = contextChunks
    .filter(c => c.pinned)
    .reduce((sum, c) => sum + (c.tokenCount || calculateTokens(c.text)), 0)
  const generationTokens = generationParams.maxTokens
  const totalTokens = promptTokens + contextTokens + generationTokens
  const maxTokens = generationParams.contextWindow
  const tokenPercentage = Math.min(100, (totalTokens / maxTokens) * 100)

  // Filter and sort characters
  const filteredCharacters = characters
    .filter(c => {
      if (!characterQuery.trim()) return true
      const lower = characterQuery.toLowerCase()
      return c.name.toLowerCase().includes(lower) ||
        c.aliases.some(a => a.toLowerCase().includes(lower))
    })
    .sort((a, b) => {
      switch (characterSort) {
        case 'name':
          return a.name.localeCompare(b.name)
        case 'importance':
          return (b.importance || 0) - (a.importance || 0)
        case 'appearance':
          return (b.appearanceCount || 0) - (a.appearanceCount || 0)
        default:
          return 0
      }
    })

  // Load node content as initial prompt
  useEffect(() => {
    if (selectedNode) {
      setLocalPrompt(selectedNode.content.text.slice(0, 200) + (selectedNode.content.text.length > 200 ? '...' : ''))
    }
  }, [selectedNodeId, selectedNode])

  // Auto-retrieve context when panel opens
  useEffect(() => {
    if (writerPanelOpen && selectedNodeId && contextChunks.length === 0) {
      retrieveContext(selectedNode?.content.text.slice(0, 100) || '', selectedNode?.branchId || 'main')
    }
  }, [writerPanelOpen, selectedNodeId, contextChunks.length, selectedNode, retrieveContext])

  // Simulate progress during generation
  useEffect(() => {
    if (loading.generation) {
      setProgress(0)
      progressIntervalRef.current = setInterval(() => {
        setProgress(p => {
          if (p >= 90) return p
          return p + Math.random() * 15
        })
      }, 500)
    } else {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
      }
      setProgress(100)
    }
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
      }
    }
  }, [loading.generation])

  if (!writerPanelOpen) return null

  const handleGenerate = async () => {
    if (!selectedNodeId) return
    
    const estimatedSeconds = Math.ceil(generationParams.maxTokens / 100)
    setEstimatedTime(estimatedSeconds)
    
    abortControllerRef.current = new AbortController()
    
    updateGenerationParams({ userPrompt: localPrompt })
    await generateText({ nodeId: selectedNodeId })
    
    setEstimatedTime(null)
  }
  
  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    cancelGeneration()
    setEstimatedTime(null)
  }

  const getSelectedContextCount = () => contextChunks.filter(c => c.pinned).length
  const getSelectedExemplarCount = () => styleExemplars.filter(e => e.selected).length
  const getEnforcedVoiceCount = () => characters.filter(c => c.voiceEnforced).length
  
  // Reorder context chunks
  const moveChunk = (index: number, direction: 'up' | 'down') => {
    const newChunks = [...contextChunks]
    const newIndex = direction === 'up' ? index - 1 : index + 1
    if (newIndex >= 0 && newIndex < newChunks.length) {
      const [moved] = newChunks.splice(index, 1)
      newChunks.splice(newIndex, 0, moved)
    }
  }
  
  // Start inline editing
  const startInlineEdit = (generationId: string, text: string) => {
    setEditingGenerationId(generationId)
    setEditText(text)
  }
  
  // Save inline edit
  const saveInlineEdit = () => {
    if (editingGenerationId) {
      editGenerationInline(editingGenerationId, editText)
      setEditingGenerationId(null)
      setEditText('')
    }
  }
  
  // Cancel inline edit
  const cancelInlineEdit = () => {
    setEditingGenerationId(null)
    setEditText('')
  }
  
  // Handle preset save
  const handleSavePreset = () => {
    if (presetName.trim()) {
      saveContextPreset(presetName.trim())
      setPresetName('')
      setShowPresetInput(false)
    }
  }
  
  return (
    <div className="writer-panel" role="region" aria-labelledby="writer-title">
      <div className="panel-header">
        <h2 id="writer-title" className="panel-title">✍️ Writer</h2>
        <button
          onClick={toggleWriterPanel}
          className="close-button"
          aria-label="Close writer panel"
        >
          ×
        </button>
      </div>

      {!selectedNodeId ? (
        <div className="empty-state">
          <p>Select a node to generate content</p>
        </div>
      ) : (
        <>
          {/* Node info */}
          <div className="node-info">
            <span className="node-label">{selectedNode?.label}</span>
            <span className="node-words">{selectedNode?.content.wordCount} words</span>
          </div>

          {/* Tabs */}
          <div className="writer-tabs" role="tablist">
            <button
              role="tab"
              aria-selected={activeTab === 'generate'}
              onClick={() => setActiveTab('generate')}
              className={activeTab === 'generate' ? 'active' : ''}
            >
              Generate
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'context'}
              onClick={() => setActiveTab('context')}
              className={activeTab === 'context' ? 'active' : ''}
            >
              Context ({getSelectedContextCount()})
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'style'}
              onClick={() => setActiveTab('style')}
              className={activeTab === 'style' ? 'active' : ''}
            >
              Style ({getSelectedExemplarCount()})
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'characters'}
              onClick={() => setActiveTab('characters')}
              className={activeTab === 'characters' ? 'active' : ''}
            >
              Voices ({getEnforcedVoiceCount()})
            </button>
          </div>

          {/* Generate Tab */}
          {activeTab === 'generate' && (
            <div className="tab-content">
              {/* Prompt input */}
              <div className="prompt-section">
                <label className="section-label">
                  Prompt / Starting Text
                  <span className="hint">What should happen next?</span>
                </label>
                <textarea
                  value={localPrompt}
                  onChange={(e) => setLocalPrompt(e.target.value)}
                  placeholder="Describe what you want to generate..."
                  className="prompt-input"
                  rows={4}
                />
              </div>

              {/* Advanced Parameters */}
              <details className="advanced-params">
                <summary>Advanced Settings</summary>
                
                {/* Model Selector */}
                <div className="param-row">
                  <label className="param-label">Model</label>
                  <select
                    value={generationParams.model}
                    onChange={(e) => updateGenerationParams({ model: e.target.value })}
                    className="param-select"
                  >
                    {MODELS.map(m => (
                      <option key={m.id} value={m.id}>{m.name} - {m.description}</option>
                    ))}
                  </select>
                </div>
                
                {/* Context Window Selector */}
                <div className="param-row">
                  <label className="param-label">Context Window</label>
                  <div className="context-window-options">
                    {CONTEXT_WINDOWS.map(opt => (
                      <button
                        key={opt.value}
                        onClick={() => updateGenerationParams({ contextWindow: opt.value })}
                        className={`window-option ${generationParams.contextWindow === opt.value ? 'active' : ''}`}
                        title={opt.description}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
                
                <div className="param-row">
                  <label className="param-label">Temperature</label>
                  <input
                    type="range"
                    min={0}
                    max={2}
                    step={0.1}
                    value={generationParams.temperature}
                    onChange={(e) => updateGenerationParams({ temperature: parseFloat(e.target.value) })}
                    className="param-slider"
                  />
                  <span className="param-value">{generationParams.temperature.toFixed(1)}</span>
                </div>
                <div className="param-row">
                  <label className="param-label">Max Tokens</label>
                  <input
                    type="range"
                    min={100}
                    max={2000}
                    step={100}
                    value={generationParams.maxTokens}
                    onChange={(e) => updateGenerationParams({ maxTokens: parseInt(e.target.value) })}
                    className="param-slider"
                  />
                  <span className="param-value">{generationParams.maxTokens}</span>
                </div>
              </details>

              {/* Tuner preview */}
              <div className="tuner-preview-bar">
                <span className="tuner-tag violence" style={{ opacity: tunerSettings.violence }}>
                  Violence: {(tunerSettings.violence * 100).toFixed(0)}%
                </span>
                <span className="tuner-tag humor" style={{ opacity: tunerSettings.humor }}>
                  Humor: {(tunerSettings.humor * 100).toFixed(0)}%
                </span>
                <span className="tuner-tag romance" style={{ opacity: tunerSettings.romance }}>
                  Romance: {(tunerSettings.romance * 100).toFixed(0)}%
                </span>
              </div>

              {/* Token Budget Visualization */}
              <div className="token-budget">
                <div className="token-budget-header">
                  <span className="token-label">Token Budget</span>
                  <span className={`token-count ${tokenPercentage > 100 ? 'exceeded' : tokenPercentage > 80 ? 'warning' : ''}`}>
                    {totalTokens.toLocaleString()} / {maxTokens.toLocaleString()}
                  </span>
                </div>
                <div className="token-progress-bar">
                  {/* Prompt segment */}
                  <div 
                    className="token-segment prompt-segment"
                    style={{ width: `${(promptTokens / maxTokens) * 100}%` }}
                    title={`Prompt: ${promptTokens} tokens`}
                  />
                  {/* Context segment */}
                  <div 
                    className="token-segment context-segment"
                    style={{ width: `${(contextTokens / maxTokens) * 100}%` }}
                    title={`Context: ${contextTokens} tokens`}
                  />
                  {/* Generation segment */}
                  <div 
                    className={`token-segment generation-segment ${tokenPercentage > 100 ? 'exceeded' : tokenPercentage > 80 ? 'warning' : ''}`}
                    style={{ width: `${(generationTokens / maxTokens) * 100}%` }}
                    title={`Generation: ${generationTokens} tokens`}
                  />
                </div>
                <div className="token-legend">
                  <span className="legend-item"><span className="legend-color prompt-color"/> Prompt: {promptTokens}</span>
                  <span className="legend-item"><span className="legend-color context-color"/> Context: {contextTokens}</span>
                  <span className="legend-item"><span className="legend-color generation-color"/> Generation: {generationTokens}</span>
                </div>
              </div>

              {/* Generate/Cancel button */}
              {loading.generation ? (
                <div className="generation-progress">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill"
                      style={{ width: `${Math.min(100, progress)}%` }}
                    />
                  </div>
                  <button
                    onClick={handleCancel}
                    className="cancel-button"
                  >
                    <span className="spinner" />
                    Cancel Generation
                    {estimatedTime && (
                      <span className="eta">~{estimatedTime}s remaining</span>
                    )}
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleGenerate}
                  disabled={!localPrompt.trim() || totalTokens > maxTokens * 2}
                  className="generate-button"
                >
                  📝 Generate Text
                </button>
              )}

              {/* Generation result */}
              {currentGeneration && (
                <div className="generation-result">
                  <div className="result-header">
                    <span className="result-title">Generated ({currentGeneration.wordCount} words)</span>
                    <span className="result-time">
                      {new Date(currentGeneration.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  
                  <div className="result-content">
                    {editingGenerationId === currentGeneration.id ? (
                      <div className="inline-edit">
                        <textarea
                          value={editText}
                          onChange={(e) => setEditText(e.target.value)}
                          className="edit-textarea"
                          rows={8}
                        />
                        <div className="edit-actions">
                          <button onClick={saveInlineEdit} className="save-btn">Save</button>
                          <button onClick={cancelInlineEdit} className="cancel-btn">Cancel</button>
                        </div>
                      </div>
                    ) : (
                      <textarea
                        value={currentGeneration.generatedText}
                        readOnly
                        className="result-textarea numbered"
                        rows={8}
                        style={{ 
                          backgroundImage: `repeating-linear-gradient(
                            transparent,
                            transparent 1.5em,
                            rgba(255,255,255,0.05) 1.5em,
                            rgba(255,255,255,0.05) 3em
                          )` 
                        }}
                      />
                    )}
                  </div>

                  {/* Contradiction warnings */}
                  {contradictions.length > 0 && (
                    <div className="contradictions-alert">
                      <div className="contradiction-header">
                        <strong>⚠️ {contradictions.length} Contradiction(s) detected</strong>
                      </div>
                      <ul>
                        {contradictions.map((c, i) => (
                          <li 
                            key={i} 
                            className={`severity-${c.severity} ${expandedContradictions.includes(`c-${i}`) ? 'expanded' : ''}`}
                          >
                            <button 
                              className="contradiction-toggle"
                              onClick={() => expandContradiction(`c-${i}`, !expandedContradictions.includes(`c-${i}`))}
                            >
                              {expandedContradictions.includes(`c-${i}`) ? '▼' : '▶'}
                              <span className={`severity-badge ${c.severity}`}>{c.severity}</span>
                              {c.description}
                            </button>
                            {expandedContradictions.includes(`c-${i}`) && (
                              <div className="contradiction-details">
                                <p><strong>Type:</strong> {c.type}</p>
                                <p><strong>Suggested Fix:</strong> {c.suggestedFix}</p>
                                <div className="contradiction-actions">
                                  <button className="fix-btn">Apply Fix</button>
                                  <button className="ignore-btn">Ignore</button>
                                </div>
                              </div>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Action buttons */}
                  <div className="result-actions">
                    <button
                      onClick={() => acceptGeneration(currentGeneration.id)}
                      className="accept-button"
                    >
                      ✅ Accept & Apply
                    </button>
                    <button
                      onClick={() => rejectGeneration(currentGeneration.id)}
                      className="reject-button"
                    >
                      ❌ Reject
                    </button>
                    <button
                      onClick={() => startInlineEdit(currentGeneration.id, currentGeneration.generatedText)}
                      className="edit-button"
                      disabled={editingGenerationId !== null}
                    >
                      ✏️ Edit
                    </button>
                    <button
                      onClick={handleGenerate}
                      disabled={loading.generation}
                      className="regenerate-button"
                    >
                      🔄 Regenerate
                    </button>
                  </div>
                </div>
              )}

              {/* Generation history */}
              {generationResults.length > 1 && (
                <div className="generation-history">
                  <h4>Previous Generations</h4>
                  {generationResults.slice(1).map(gen => (
                    <div key={gen.id} className="history-item">
                      <span>{gen.wordCount} words</span>
                      <span>{new Date(gen.timestamp).toLocaleTimeString()}</span>
                      <button onClick={() => acceptGeneration(gen.id)}>Use</button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Context Tab */}
          {activeTab === 'context' && (
            <div className="tab-content">
              <div className="context-header">
                <p className="context-hint">
                  Select relevant context chunks to ground the generation
                </p>
                <button
                  onClick={() => retrieveContext(localPrompt.slice(0, 100), selectedNode?.branchId || 'main')}
                  className="refresh-button"
                >
                  🔄 Refresh
                </button>
              </div>
              
              {/* Context Presets */}
              <div className="context-presets">
                <div className="preset-header">
                  <span>Presets</span>
                  <button 
                    onClick={() => setShowPresetInput(!showPresetInput)}
                    className="preset-add-btn"
                  >
                    + Save Current
                  </button>
                </div>
                {showPresetInput && (
                  <div className="preset-input">
                    <input
                      type="text"
                      value={presetName}
                      onChange={(e) => setPresetName(e.target.value)}
                      placeholder="Preset name..."
                      onKeyDown={(e) => e.key === 'Enter' && handleSavePreset()}
                    />
                    <button onClick={handleSavePreset}>Save</button>
                    <button onClick={() => setShowPresetInput(false)}>Cancel</button>
                  </div>
                )}
                {contextPresets.length > 0 && (
                  <div className="preset-list">
                    {contextPresets.map(preset => (
                      <div 
                        key={preset.id} 
                        className={`preset-item ${activePresetId === preset.id ? 'active' : ''}`}
                      >
                        <button 
                          onClick={() => loadContextPreset(preset.id)}
                          className="preset-name"
                        >
                          {preset.name}
                        </button>
                        <button 
                          onClick={() => deleteContextPreset(preset.id)}
                          className="preset-delete"
                          title="Delete preset"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Context Search */}
              <div className="context-search">
                <input
                  type="text"
                  value={contextSearchQuery}
                  onChange={(e) => setContextSearchQuery(e.target.value)}
                  placeholder="Search context..."
                  className="search-input"
                />
              </div>

              <div className="context-list">
                {contextChunks.length === 0 ? (
                  <p className="empty-text">No context retrieved yet</p>
                ) : (
                  contextChunks
                    .filter(c => !contextSearchQuery || 
                      c.text.toLowerCase().includes(contextSearchQuery.toLowerCase()) ||
                      c.source.toLowerCase().includes(contextSearchQuery.toLowerCase())
                    )
                    .map((chunk, index) => (
                    <div
                      key={chunk.id}
                      className={`context-chunk ${chunk.pinned ? 'pinned' : ''} ${chunk.expanded ? 'expanded' : ''}`}
                    >
                      <div className="chunk-header">
                        <input
                          type="checkbox"
                          checked={chunk.pinned || false}
                          onChange={() => toggleContextChunk(chunk.id)}
                        />
                        <span className="chunk-source">{chunk.source}</span>
                        <span className="chunk-score">
                          {(chunk.relevanceScore * 100).toFixed(0)}%
                        </span>
                        <span className="chunk-tokens">
                          {chunk.tokenCount || calculateTokens(chunk.text)} tokens
                        </span>
                        <div className="chunk-actions">
                          <button
                            onClick={() => expandContextChunk(chunk.id, !chunk.expanded)}
                            className="chunk-expand-btn"
                            title={chunk.expanded ? 'Collapse' : 'Expand'}
                          >
                            {chunk.expanded ? '▼' : '▶'}
                          </button>
                          <button
                            onClick={() => moveChunk(index, 'up')}
                            disabled={index === 0}
                            className="chunk-move-btn"
                            title="Move up"
                          >
                            ↑
                          </button>
                          <button
                            onClick={() => moveChunk(index, 'down')}
                            disabled={index === contextChunks.length - 1}
                            className="chunk-move-btn"
                            title="Move down"
                          >
                            ↓
                          </button>
                          <button
                            onClick={() => removeContextChunk(chunk.id)}
                            className="chunk-remove-btn"
                            title="Remove"
                          >
                            ×
                          </button>
                        </div>
                      </div>
                      <p className={`chunk-text ${chunk.expanded ? 'expanded' : ''}`}>
                        {chunk.expanded 
                          ? chunk.text 
                          : chunk.text.slice(0, 150) + (chunk.text.length > 150 ? '...' : '')
                        }
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Style Tab */}
          {activeTab === 'style' && (
            <div className="tab-content">
              <div className="style-header">
                <p className="style-hint">
                  Select style exemplars to match the writing style
                </p>
                <button
                  onClick={() => retrieveStyleExemplars(localPrompt.slice(0, 200))}
                  className="refresh-button"
                >
                  🔄 Refresh
                </button>
              </div>
              
              {/* Style Profile Indicator */}
              {styleExemplars.filter(e => e.selected).length > 0 && (
                <div className="style-profile-indicator">
                  <h4>Active Style Profile</h4>
                  <div className="style-stats">
                    <div className="style-stat">
                      <span className="stat-label">Exemplars</span>
                      <span className="stat-value">{styleExemplars.filter(e => e.selected).length}</span>
                    </div>
                    <div className="style-stat">
                      <span className="stat-label">Avg Similarity</span>
                      <span className="stat-value">
                        {(styleExemplars
                          .filter(e => e.selected)
                          .reduce((sum, e) => sum + e.similarityScore, 0) / 
                          styleExemplars.filter(e => e.selected).length * 100
                        ).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              )}

              <div className="exemplar-list">
                {styleExemplars.length === 0 ? (
                  <p className="empty-text">No style exemplars retrieved yet</p>
                ) : (
                  styleExemplars.map(exemplar => (
                    <div
                      key={exemplar.id}
                      className={`exemplar-item ${exemplar.selected ? 'selected' : ''} ${exemplar.isStyleGuide ? 'style-guide' : ''}`}
                    >
                      <div className="exemplar-header">
                        <input
                          type="checkbox"
                          checked={exemplar.selected || false}
                          onChange={() => toggleStyleExemplar(exemplar.id)}
                        />
                        <span className="exemplar-score">
                          {(exemplar.similarityScore * 100).toFixed(0)}% match
                        </span>
                        <button
                          onClick={() => setStyleGuide(exemplar.id)}
                          className={`style-guide-btn ${exemplar.isStyleGuide ? 'active' : ''}`}
                          title={exemplar.isStyleGuide ? 'Remove as style guide' : 'Use as style guide'}
                        >
                          {exemplar.isStyleGuide ? '★ Style Guide' : '☆ Set as Guide'}
                        </button>
                      </div>
                      <p className="exemplar-text">{exemplar.text}</p>
                      <div className="exemplar-features">
                        {exemplar.features.map(f => (
                          <span key={f} className="feature-tag">{f}</span>
                        ))}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
          
          {/* Characters Tab */}
          {activeTab === 'characters' && (
            <div className="tab-content">
              <div className="characters-header">
                <p className="characters-hint">
                  Manage character voices for generation
                </p>
              </div>
              
              {/* Search and Sort */}
              <div className="character-controls">
                <input
                  type="text"
                  value={characterQuery}
                  onChange={(e) => setCharacterQuery(e.target.value)}
                  placeholder="Search characters..."
                  className="search-input"
                />
                <select
                  value={characterSort}
                  onChange={(e) => setCharacterSort(e.target.value as typeof characterSort)}
                  className="sort-select"
                >
                  <option value="name">Sort by Name</option>
                  <option value="importance">Sort by Importance</option>
                  <option value="appearance">Sort by Appearances</option>
                </select>
              </div>
              
              {/* Active Voices Summary */}
              {characters.filter(c => c.voiceEnforced).length > 0 && (
                <div className="active-voices">
                  <h4>Active Voices ({characters.filter(c => c.voiceEnforced).length})</h4>
                  <div className="voice-chips">
                    {characters.filter(c => c.voiceEnforced).map(c => (
                      <span key={c.id} className="voice-chip">
                        {c.name}
                        {c.focusMode && <span className="focus-badge">★ Focus</span>}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="character-list">
                {filteredCharacters.length === 0 ? (
                  <p className="empty-text">No characters found</p>
                ) : (
                  filteredCharacters.map(character => (
                    <div
                      key={character.id}
                      className={`character-voice-card ${character.voiceEnforced ? 'enforced' : ''} ${character.focusMode ? 'focused' : ''}`}
                    >
                      <div className="voice-card-header">
                        <h4 className="character-name">{character.name}</h4>
                        <div className="voice-toggles">
                          <label className="toggle-label">
                            <input
                              type="checkbox"
                              checked={character.voiceEnforced || false}
                              onChange={() => toggleVoiceEnforcement(character.id)}
                            />
                            <span>Enforce Voice</span>
                          </label>
                          <label className="toggle-label">
                            <input
                              type="checkbox"
                              checked={character.focusMode || false}
                              onChange={() => toggleCharacterFocus(character.id)}
                              disabled={!character.voiceEnforced}
                            />
                            <span>Focus</span>
                          </label>
                        </div>
                      </div>
                      
                      {character.aliases.length > 0 && (
                        <p className="character-aliases">
                          Also known as: {character.aliases.join(', ')}
                        </p>
                      )}
                      
                      {character.voiceProfile && (
                        <div className="voice-profile">
                          {character.voiceProfile.sampleQuotes.length > 0 && (
                            <blockquote className="voice-quote">
                              "{character.voiceProfile.sampleQuotes[0]}"
                            </blockquote>
                          )}
                          <div className="voice-traits">
                            {character.voiceProfile.speechPatterns.slice(0, 3).map((pattern, i) => (
                              <span key={i} className="trait-tag">{pattern}</span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      <div className="character-meta">
                        <span>Importance: {character.importance || 0}/10</span>
                        <span>Appearances: {character.appearanceCount || 0}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
