import { useAppStore } from '../store'
import './StatusBar.css'

export function StatusBar() {
  const { phase8Metrics, graphMetrics } = useAppStore()

  const getStatusIcon = (status: boolean | undefined) => {
    return status ? '✓' : '✗'
  }

  const getStatusClass = (status: boolean | undefined) => {
    return status ? 'good' : 'bad'
  }

  return (
    <footer className="status-bar" role="contentinfo">
      <div className="status-section">
        <span className="status-label">Phase 8 Status:</span>
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

      <div className="status-section shortcuts">
        <span className="shortcut-hint" title="Keyboard shortcuts">
          Ctrl+Z: Undo | Ctrl+T: Tuner | Ctrl+D: Dual | Ctrl+S: Save
        </span>
      </div>
    </footer>
  )
}
