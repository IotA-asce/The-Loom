import { useAppStore } from '../store'
import './StatusBar.css'

export function StatusBar() {
  const { 
    phase8Metrics, 
    graphMetrics, 
    nodes,
    selectedNodeId,
    contradictions,
    loading,
    error,
    clearError,
  } = useAppStore()

  const getStatusIcon = (status: boolean | undefined) => {
    return status ? '✓' : '✗'
  }

  const getStatusClass = (status: boolean | undefined) => {
    return status ? 'good' : 'bad'
  }
  
  // Calculate content stats
  const totalWords = nodes.reduce((sum, n) => sum + n.content.wordCount, 0)
  const nodesWithContent = nodes.filter(n => n.content.wordCount > 0).length
  const selectedNode = nodes.find(n => n.id === selectedNodeId)

  return (
    <footer className="status-bar" role="contentinfo">
      {/* Error notifications */}
      {(error.nodes || error.content) && (
        <div className="error-banner" role="alert">
          {error.nodes && (
            <span className="error-message">
              {error.nodes}
              <button onClick={() => clearError('nodes')} className="error-dismiss">×</button>
            </span>
          )}
          {error.content && (
            <span className="error-message">
              {error.content}
              <button onClick={() => clearError('content')} className="error-dismiss">×</button>
            </span>
          )}
        </div>
      )}
      
      <div className="status-sections">
        <div className="status-section">
          <span className="status-label">Phase 8:</span>
          {phase8Metrics ? (
            <div className="status-indicators">
              <span 
                className={`status-pill ${getStatusClass(phase8Metrics.graphPerformanceUsable)}`}
                title="Graph performance is usable"
              >
                {getStatusIcon(phase8Metrics.graphPerformanceUsable)} Graph
              </span>
              <span 
                className={`status-pill ${getStatusClass(phase8Metrics.keyboardMobileUsable)}`}
                title="Keyboard and mobile ready"
              >
                {getStatusIcon(phase8Metrics.keyboardMobileUsable)} Access
              </span>
              <span 
                className={`status-pill ${getStatusClass(phase8Metrics.dualSyncVisibleAndAccurate)}`}
                title="Dual-view sync is visible and accurate"
              >
                {getStatusIcon(phase8Metrics.dualSyncVisibleAndAccurate)} Sync
              </span>
            </div>
          ) : (
            <span className="status-loading">Loading...</span>
          )}
        </div>

        {graphMetrics && (
          <div className="status-section metrics">
            <span className="metric-item" title="Total nodes">
              Nodes: {graphMetrics.totalNodes}
            </span>
            <span className="metric-item" title="Visible nodes">
              Visible: {graphMetrics.visibleNodes}
            </span>
            <span className="metric-item" title="Virtualization ratio">
              V-Ratio: {(graphMetrics.virtualizationRatio * 100).toFixed(0)}%
            </span>
          </div>
        )}
        
        {/* Content metrics */}
        <div className="status-section content-metrics">
          <span className="metric-item" title="Total words across all nodes">
            Words: {totalWords.toLocaleString()}
          </span>
          <span className="metric-item" title="Nodes with content">
            With Content: {nodesWithContent}/{nodes.length}
          </span>
          {contradictions.length > 0 && (
            <span 
              className="metric-item contradictions-badge"
              title={`${contradictions.length} contradiction(s) detected`}
            >
              ⚠️ {contradictions.length} Issues
            </span>
          )}
          {selectedNode && (
            <span className="metric-item selected" title="Selected node word count">
              Selected: {selectedNode.content.wordCount}w
            </span>
          )}
        </div>

        <div className="status-section shortcuts">
          <span className="shortcut-hint" title="Keyboard shortcuts">
            Ctrl+? Help
          </span>
        </div>
        
        {/* Loading indicators */}
        {(loading.nodes || loading.content || loading.generation) && (
          <div className="status-section loading">
            <span className="loading-indicator">
              <span className="spinner" />
              {loading.nodes && ' Loading nodes...'}
              {loading.content && ' Saving...'}
              {loading.generation && ' Generating...'}
            </span>
          </div>
        )}
      </div>
    </footer>
  )
}
