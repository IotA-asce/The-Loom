import { useState } from 'react'
import { useRecommendationsStore } from '../stores/recommendationsStore'
import { useAppStore } from '../store'
import './RecommendationsPanel.css'

interface RecommendationsPanelProps {
  isOpen: boolean
  onClose: () => void
}

export function RecommendationsPanel({ isOpen, onClose }: RecommendationsPanelProps) {
  const {
    suggestions,
    constraints,
    violations,
    isLoadingSuggestions,
    activeTab,
    setActiveTab,
    dismissSuggestion,
    createBranchFromSuggestion,
    previewImpact,
    previewSuggestionId,
    previewData,
    clearPreview,
    acknowledgeViolation,
    getViolationCount,
  } = useRecommendationsStore()
  
  const { addToast } = useAppStore()
  const [creatingBranch, setCreatingBranch] = useState<string | null>(null)
  
  if (!isOpen) return null
  
  const activeSuggestions = suggestions.filter(s => !s.dismissed)
  const violationCount = getViolationCount()
  
  const getDivergenceColor = (score: number) => {
    if (score >= 80) return '#ef4444'
    if (score >= 60) return '#ff9800'
    if (score >= 40) return '#eab308'
    return '#4caf50'
  }
  
  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return '#ef4444'
      case 'medium': return '#ff9800'
      case 'low': return '#4caf50'
      default: return '#888'
    }
  }
  
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return '🔴'
      case 'warning': return '🟡'
      case 'info': return '🔵'
      default: return '⚪'
    }
  }
  
  const handleCreateBranch = async (suggestionId: string) => {
    setCreatingBranch(suggestionId)
    const branchId = await createBranchFromSuggestion(suggestionId, 'Suggested Branch')
    setCreatingBranch(null)
    
    if (branchId) {
      addToast({ message: 'Branch created from suggestion', type: 'success' })
      onClose()
    }
  }
  
  return (
    <div className="recommendations-overlay" onClick={onClose}>
      <div className="recommendations-panel" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="recommendations-header">
          <h2>💡 Recommendations</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        {/* Tabs */}
        <div className="recommendations-tabs">
          <button
            className={`tab-btn ${activeTab === 'suggestions' ? 'active' : ''}`}
            onClick={() => setActiveTab('suggestions')}
          >
            <span>💡</span>
            <span>Suggestions</span>
            {activeSuggestions.length > 0 && (
              <span className="tab-badge">{activeSuggestions.length}</span>
            )}
          </button>
          <button
            className={`tab-btn ${activeTab === 'constraints' ? 'active' : ''}`}
            onClick={() => setActiveTab('constraints')}
          >
            <span>📋</span>
            <span>Constraints</span>
            {violationCount > 0 && (
              <span className="tab-badge error">{violationCount}</span>
            )}
          </button>
        </div>
        
        {/* Content */}
        <div className="recommendations-content">
          {/* Suggestions Tab */}
          {activeTab === 'suggestions' && (
            <div className="suggestions-tab">
              {isLoadingSuggestions ? (
                <div className="loading-state">Loading suggestions...</div>
              ) : activeSuggestions.length > 0 ? (
                <>
                  {/* Impact Preview Modal */}
                  {previewData && previewSuggestionId && (
                    <div className="impact-preview">
                      <div className="preview-header">
                        <h4>🔮 Impact Preview</h4>
                        <button className="preview-close" onClick={clearPreview}>×</button>
                      </div>
                      
                      <div className="preview-stats">
                        <div className="preview-stat">
                          <span className="stat-label">Consistency Score</span>
                          <span className="stat-value">{previewData.consistencyScore.toFixed(1)}%</span>
                        </div>
                        <div className="preview-stat">
                          <span className="stat-label">Risk Level</span>
                          <span
                            className="stat-value"
                            style={{ color: getImpactColor(previewData.riskLevel) }}
                          >
                            {previewData.riskLevel.toUpperCase()}
                          </span>
                        </div>
                      </div>
                      
                      <div className="affected-nodes">
                        <h5>Affected Nodes</h5>
                        <div className="nodes-list">
                          {previewData.affectedNodes.map(node => (
                            <div
                              key={node.id}
                              className="affected-node"
                              style={{ borderColor: getImpactColor(node.impact) }}
                            >
                              <span className="node-label">{node.label}</span>
                              <span
                                className="impact-badge"
                                style={{ backgroundColor: getImpactColor(node.impact) }}
                              >
                                {node.impact}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Suggestions List */}
                  <div className="suggestions-list">
                    {activeSuggestions
                      .sort((a, b) => b.divergenceScore - a.divergenceScore)
                      .map(suggestion => (
                        <div
                          key={suggestion.id}
                          className={`suggestion-card ${previewSuggestionId === suggestion.id ? 'previewing' : ''}`}
                        >
                          <div className="suggestion-header">
                            <div className="suggestion-title">
                              <span className="node-ref">📍 {suggestion.nodeLabel}</span>
                              <h4>{suggestion.description}</h4>
                            </div>
                            <div
                              className="divergence-score"
                              style={{ backgroundColor: getDivergenceColor(suggestion.divergenceScore) }}
                            >
                              <span className="score-value">{suggestion.divergenceScore}</span>
                              <span className="score-label">divergence</span>
                            </div>
                          </div>
                          
                          <p className="suggestion-reason">{suggestion.reason}</p>
                          
                          <div className="impact-summary">
                            <span className="impact-item">
                              📊 {suggestion.impactSummary.affectedNodes} nodes affected
                            </span>
                            <span
                              className="impact-item"
                              style={{ color: getImpactColor(suggestion.impactSummary.consistencyImpact) }}
                            >
                              ⚡ {suggestion.impactSummary.consistencyImpact} impact
                            </span>
                            <span className="impact-item">
                              📝 ~{suggestion.impactSummary.estimatedTokens} tokens
                            </span>
                          </div>
                          
                          <div className="suggestion-actions">
                            <button
                              className="action-btn primary"
                              onClick={() => handleCreateBranch(suggestion.id)}
                              disabled={creatingBranch === suggestion.id}
                            >
                              {creatingBranch === suggestion.id ? (
                                <>
                                  <span className="spinner-small" />
                                  Creating...
                                </>
                              ) : (
                                <>
                                  <span>🌿</span>
                                  Create Branch Here
                                </>
                              )}
                            </button>
                            <button
                              className="action-btn secondary"
                              onClick={() => previewImpact(suggestion.id)}
                              disabled={previewSuggestionId === suggestion.id}
                            >
                              <span>🔮</span>
                              Preview Impact
                            </button>
                            <button
                              className="action-btn dismiss"
                              onClick={() => dismissSuggestion(suggestion.id)}
                            >
                              <span>🗑️</span>
                              Dismiss
                            </button>
                          </div>
                        </div>
                      ))}
                  </div>
                </>
              ) : (
                <div className="empty-state">
                  <span className="empty-icon">✨</span>
                  <p>No active suggestions</p>
                  <span className="empty-hint">High-impact branch points will appear here</span>
                </div>
              )}
            </div>
          )}
          
          {/* Constraints Tab */}
          {activeTab === 'constraints' && (
            <div className="constraints-tab">
              {/* Violations Section */}
              {violations.filter(v => !v.acknowledged).length > 0 && (
                <div className="violations-section">
                  <h3>🚨 Active Violations</h3>
                  <div className="violations-list">
                    {violations
                      .filter(v => !v.acknowledged)
                      .map(violation => {
                        const constraint = constraints.find(c => c.id === violation.constraintId)
                        return (
                          <div
                            key={violation.id}
                            className={`violation-card ${violation.severity}`}
                          >
                            <div className="violation-header">
                              <span className="severity-icon">
                                {violation.severity === 'critical' ? '🔴' : '🟡'}
                              </span>
                              <span className="violation-message">{violation.message}</span>
                            </div>
                            {constraint && (
                              <div className="violation-constraint">
                                Constraint: {constraint.description}
                              </div>
                            )}
                            {violation.suggestedFix && (
                              <div className="suggested-fix">
                                <span>💡 Suggested fix:</span>
                                {violation.suggestedFix}
                              </div>
                            )}
                            <div className="viocation-actions">
                              <button
                                className="ack-btn"
                                onClick={() => acknowledgeViolation(violation.id)}
                              >
                                Acknowledge
                              </button>
                            </div>
                          </div>
                        )
                      })}
                  </div>
                </div>
              )}
              
              {/* Constraints List */}
              <div className="constraints-section">
                <h3>📋 Active Constraints</h3>
                {constraints.length > 0 ? (
                  <div className="constraints-list">
                    {constraints.map(constraint => {
                      const violationCount = violations.filter(
                        v => v.constraintId === constraint.id && !v.acknowledged
                      ).length
                      
                      return (
                        <div
                          key={constraint.id}
                          className={`constraint-card ${constraint.severity}`}
                        >
                          <div className="constraint-header">
                            <span className="severity-icon">
                              {getSeverityIcon(constraint.severity)}
                            </span>
                            <span className="constraint-type">{constraint.type}</span>
                            {violationCount > 0 && (
                              <span className="violation-badge">{violationCount}</span>
                            )}
                          </div>
                          <p className="constraint-description">{constraint.description}</p>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <div className="empty-state">
                    <span className="empty-icon">📋</span>
                    <p>No active constraints</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Compact violation badge for header
export function ViolationBadge() {
  const violationCount = useRecommendationsStore(state => state.getViolationCount())
  
  if (violationCount === 0) return null
  
  return (
    <span className="violation-badge-compact">
      {violationCount}
    </span>
  )
}
