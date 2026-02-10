import { useState } from 'react'
import { useAppStore } from '../store'
import './ConsequenceSimulator.css'

interface SimulationResult {
  affectedNodes: Array<{
    id: string
    name: string
    impact: 'high' | 'medium' | 'low'
    description: string
  }>
  consistencyScore: number
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
  estimatedTokens: number
  estimatedTime: number
  suggestedActions: string[]
}

export function ConsequenceSimulator() {
  const {
    simulatorOpen,
    toggleSimulator,
    nodes,
    selectedNodeId,
  } = useAppStore()

  const [changeType, setChangeType] = useState<'edit' | 'delete' | 'reorder'>('edit')
  const [proposedChange, setProposedChange] = useState('')
  const [isSimulating, setIsSimulating] = useState(false)
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [showDiff, setShowDiff] = useState(false)

  const selectedNode = nodes.find(n => n.id === selectedNodeId)

  if (!simulatorOpen) return null

  const handleSimulate = async () => {
    if (!proposedChange.trim() || !selectedNodeId) return
    
    setIsSimulating(true)
    setResult(null)
    
    // Mock simulation
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    const mockResult: SimulationResult = {
      affectedNodes: [
        {
          id: 'node-1',
          name: selectedNode?.label || 'Selected Node',
          impact: 'high',
          description: 'Direct modification - content will be changed',
        },
        {
          id: 'node-2',
          name: 'Chapter 2: The Aftermath',
          impact: 'medium',
          description: 'References this scene - may need updating',
        },
        {
          id: 'node-3',
          name: 'Character Arc: Growth',
          impact: 'low',
          description: 'Thematically related but not directly affected',
        },
      ],
      consistencyScore: 0.72,
      riskLevel: 'medium',
      estimatedTokens: 4500,
      estimatedTime: 45,
      suggestedActions: [
        'Review Chapter 2 for continuity',
        'Update character state tracking',
        'Check dialogue references',
      ],
    }
    
    setResult(mockResult)
    setIsSimulating(false)
  }

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return '#4caf50'
      case 'medium': return '#ff9800'
      case 'high': return '#f44336'
      case 'critical': return '#9c27b0'
      default: return '#888'
    }
  }

  const getImpactIcon = (impact: string) => {
    switch (impact) {
      case 'high': return '🔴'
      case 'medium': return '🟡'
      case 'low': return '🟢'
      default: return '⚪'
    }
  }

  return (
    <div className="simulator-panel" role="region" aria-labelledby="simulator-title">
      <div className="panel-header">
        <h2 id="simulator-title" className="panel-title">🔮 What-If Simulator</h2>
        <button
          onClick={toggleSimulator}
          className="close-button"
          aria-label="Close simulator"
        >
          ×
        </button>
      </div>

      <div className="simulator-content">
        {!selectedNodeId ? (
          <div className="empty-state">
            <p>Select a node to simulate changes</p>
          </div>
        ) : (
          <>
            {/* Target Node */}
            <div className="target-node">
              <label>Target Node</label>
              <div className="node-card">
                <span className="node-name">{selectedNode?.label}</span>
                <span className="node-type">{selectedNode?.type}</span>
              </div>
            </div>

            {/* Change Type */}
            <div className="change-type">
              <label>Change Type</label>
              <div className="type-buttons">
                {(['edit', 'delete', 'reorder'] as const).map(type => (
                  <button
                    key={type}
                    onClick={() => setChangeType(type)}
                    className={changeType === type ? 'active' : ''}
                  >
                    {type === 'edit' && '✏️ Edit Content'}
                    {type === 'delete' && '🗑️ Delete Node'}
                    {type === 'reorder' && '↔️ Reorder/Move'}
                  </button>
                ))}
              </div>
            </div>

            {/* Proposed Change */}
            <div className="proposed-change">
              <label>Proposed Change</label>
              <textarea
                value={proposedChange}
                onChange={(e) => setProposedChange(e.target.value)}
                placeholder={
                  changeType === 'edit' 
                    ? 'Describe your proposed edit...' 
                    : changeType === 'delete'
                    ? 'Reason for deletion (optional)...'
                    : 'Describe the new position/order...'
                }
                rows={4}
              />
            </div>

            {/* Simulate Button */}
            <button
              onClick={handleSimulate}
              disabled={!proposedChange.trim() || isSimulating}
              className="simulate-btn"
            >
              {isSimulating ? (
                <>
                  <span className="spinner" />
                  Simulating...
                </>
              ) : (
                <>🔮 Run Simulation</>
              )}
            </button>

            {/* Results */}
            {result && (
              <div className="simulation-results">
                <h3>Simulation Results</h3>
                
                {/* Risk Level */}
                <div 
                  className="risk-banner"
                  style={{ backgroundColor: getRiskColor(result.riskLevel) }}
                >
                  <span className="risk-label">Risk Level:</span>
                  <span className="risk-value">{result.riskLevel.toUpperCase()}</span>
                </div>

                {/* Consistency Score */}
                <div className="consistency-score">
                  <div className="score-header">
                    <span>Consistency Score</span>
                    <span className="score-value">{(result.consistencyScore * 100).toFixed(0)}%</span>
                  </div>
                  <div className="score-bar">
                    <div 
                      className="score-fill"
                      style={{ 
                        width: `${result.consistencyScore * 100}%`,
                        backgroundColor: result.consistencyScore > 0.8 ? '#4caf50' : 
                                        result.consistencyScore > 0.5 ? '#ff9800' : '#f44336'
                      }}
                    />
                  </div>
                </div>

                {/* Cost Estimation */}
                <div className="cost-estimate">
                  <h4>Estimated Cost</h4>
                  <div className="cost-grid">
                    <div className="cost-item">
                      <span className="cost-value">{result.estimatedTokens.toLocaleString()}</span>
                      <span className="cost-label">tokens</span>
                    </div>
                    <div className="cost-item">
                      <span className="cost-value">~{result.estimatedTime}s</span>
                      <span className="cost-label">processing</span>
                    </div>
                  </div>
                </div>

                {/* Affected Nodes */}
                <div className="affected-nodes">
                  <div className="section-header">
                    <h4>Affected Nodes</h4>
                    <button
                      onClick={() => setShowDiff(!showDiff)}
                      className="toggle-diff"
                    >
                      {showDiff ? 'Hide' : 'Show'} Visual Diff
                    </button>
                  </div>
                  
                  {showDiff && (
                    <div className="diff-preview">
                      <div className="diff-before">
                        <span className="diff-label">Before</span>
                        <div className="diff-content">Original content...</div>
                      </div>
                      <div className="diff-arrow">→</div>
                      <div className="diff-after">
                        <span className="diff-label">After</span>
                        <div className="diff-content">{proposedChange}</div>
                      </div>
                    </div>
                  )}
                  
                  <div className="nodes-list">
                    {result.affectedNodes.map(node => (
                      <div key={node.id} className={`affected-node ${node.impact}`}>
                        <span className="impact-icon">{getImpactIcon(node.impact)}</span>
                        <div className="node-info">
                          <span className="node-name">{node.name}</span>
                          <span className="node-desc">{node.description}</span>
                        </div>
                        <span className={`impact-badge ${node.impact}`}>
                          {node.impact}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Suggested Actions */}
                <div className="suggested-actions">
                  <h4>Suggested Actions</h4>
                  <ul>
                    {result.suggestedActions.map((action, index) => (
                      <li key={index}>{action}</li>
                    ))}
                  </ul>
                </div>

                {/* Action Buttons */}
                <div className="action-buttons">
                  <button className="apply-btn">
                    ✅ Apply Change
                  </button>
                  <button 
                    onClick={() => {
                      setResult(null)
                      setProposedChange('')
                    }}
                    className="cancel-btn"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
