import { useEffect, useState, useRef } from 'react'
import { useAppStore } from '../store'
import './WriterPanel.css'

export function WriterPanel() {
  const {
    writerPanelOpen,
    selectedNodeId,
    nodes,
    tunerSettings,
    generationParams,
    contextChunks,
    styleExemplars,
    generationResults,
    currentGeneration,
    contradictions,
    loading,
    toggleWriterPanel,
    retrieveContext,
    toggleContextChunk,
    retrieveStyleExemplars,
    toggleStyleExemplar,
    generateText,
    acceptGeneration,
    rejectGeneration,
    updateGenerationParams,
  } = useAppStore()

  const [activeTab, setActiveTab] = useState<'generate' | 'context' | 'style'>('generate')
  const [localPrompt, setLocalPrompt] = useState('')
  const [estimatedTime, setEstimatedTime] = useState<number | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const selectedNode = nodes.find(n => n.id === selectedNodeId)
  
  // Calculate token budget (rough estimate: 1 token ≈ 0.75 words)
  const calculateTokens = (text: string) => Math.ceil(text.split(/\s+/).filter(w => w.length > 0).length / 0.75)
  const promptTokens = calculateTokens(localPrompt)
  const contextTokens = contextChunks
    .filter(c => c.pinned)
    .reduce((sum, c) => sum + calculateTokens(c.text), 0)
  const totalTokens = promptTokens + contextTokens
  const maxTokens = generationParams.maxTokens
  const tokenPercentage = Math.min(100, (totalTokens / maxTokens) * 100)

  // Load node content as initial prompt
  useEffect(() => {
    if (selectedNode) {
      setLocalPrompt(selectedNode.content.text.slice(0, 200) + (selectedNode.content.text.length > 200 ? '...' : ''))
    }
  }, [selectedNodeId])

  // Auto-retrieve context when panel opens
  useEffect(() => {
    if (writerPanelOpen && selectedNodeId && contextChunks.length === 0) {
      retrieveContext(selectedNode?.content.text.slice(0, 100) || '', selectedNode?.branchId || 'main')
    }
  }, [writerPanelOpen, selectedNodeId])

  if (!writerPanelOpen) return null

  const handleGenerate = async () => {
    if (!selectedNodeId) return
    
    // Estimate time based on token count (rough: 100 tokens/sec)
    const estimatedSeconds = Math.ceil(maxTokens / 100)
    setEstimatedTime(estimatedSeconds)
    
    // Create abort controller for cancellation
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
    setEstimatedTime(null)
  }

  const getSelectedContextCount = () => contextChunks.filter(c => c.pinned).length
  const getSelectedExemplarCount = () => styleExemplars.filter(e => e.selected).length
  
  // Reorder context chunks
  const moveChunk = (index: number, direction: 'up' | 'down') => {
    const newChunks = [...contextChunks]
    const newIndex = direction === 'up' ? index - 1 : index + 1
    if (newIndex >= 0 && newIndex < newChunks.length) {
      const [moved] = newChunks.splice(index, 1)
      newChunks.splice(newIndex, 0, moved)
      // Note: This would need to be persisted to the store
      // For now, we'll just log it
      console.log('Reordered chunks:', newChunks.map(c => c.id))
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

              {/* Parameters */}
              <div className="params-section">
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
              </div>

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
                  <div 
                    className={`token-progress-fill ${tokenPercentage > 100 ? 'exceeded' : tokenPercentage > 80 ? 'warning' : ''}`}
                    style={{ width: `${Math.min(100, tokenPercentage)}%` }}
                  />
                </div>
                <div className="token-breakdown">
                  <span>Prompt: {promptTokens}</span>
                  <span>Context: {contextTokens}</span>
                  <span>Generation: {maxTokens}</span>
                </div>
              </div>

              {/* Generate button */}
              {loading.generation ? (
                <div className="generation-progress">
                  <button
                    onClick={handleCancel}
                    className="cancel-button"
                  >
                    <span className="spinner" />
                    Cancel Generation
                    {estimatedTime && (
                      <span className="eta">~{estimatedTime}s</span>
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
                    <textarea
                      value={currentGeneration.generatedText}
                      readOnly
                      className="result-textarea"
                      rows={8}
                    />
                  </div>

                  {/* Contradiction warnings */}
                  {contradictions.length > 0 && (
                    <div className="contradictions-alert">
                      <strong>⚠️ Contradictions detected:</strong>
                      <ul>
                        {contradictions.map((c, i) => (
                          <li key={i} className={`severity-${c.severity}`}>
                            {c.description}
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

              <div className="context-list">
                {contextChunks.length === 0 ? (
                  <p className="empty-text">No context retrieved yet</p>
                ) : (
                  contextChunks.map((chunk, index) => (
                    <div
                      key={chunk.id}
                      className={`context-chunk ${chunk.pinned ? 'pinned' : ''}`}
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
                        <div className="chunk-actions">
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
                            onClick={() => {
                              // Filter out this chunk - would need store update
                              console.log('Removed chunk:', chunk.id)
                            }}
                            className="chunk-remove-btn"
                            title="Remove"
                          >
                            ×
                          </button>
                        </div>
                      </div>
                      <p className="chunk-text">{chunk.text}</p>
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

              <div className="exemplar-list">
                {styleExemplars.length === 0 ? (
                  <p className="empty-text">No style exemplars retrieved yet</p>
                ) : (
                  styleExemplars.map(exemplar => (
                    <div
                      key={exemplar.id}
                      className={`exemplar-item ${exemplar.selected ? 'selected' : ''}`}
                      onClick={() => toggleStyleExemplar(exemplar.id)}
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
        </>
      )}
    </div>
  )
}
