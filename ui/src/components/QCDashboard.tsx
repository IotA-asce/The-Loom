import { useState, useMemo } from 'react'
import { useAppStore } from '../store'
import './QCDashboard.css'

interface PanelQC {
  panelId: string
  imageUrl?: string
  status: 'pending' | 'generating' | 'completed' | 'failed' | 'needs_correction'
  overallScore: number
  anatomyScore: number
  compositionScore: number
  colorScore: number
  continuityScore: number
  failureReasons: string[]
  driftDetected: boolean
  driftScore: number
}

type FilterType = 'all' | 'passed' | 'failed' | 'needs_correction' | 'drift'
type SortBy = 'newest' | 'score' | 'drift'

interface QCDashboardProps {
  isOpen: boolean
  onClose: () => void
}

export function QCDashboard({ isOpen, onClose }: QCDashboardProps) {
  const { generatedPanels } = useAppStore()
  const [filter, setFilter] = useState<FilterType>('all')
  const [sortBy, setSortBy] = useState<SortBy>('newest')
  const [selectedPanels, setSelectedPanels] = useState<Set<string>>(new Set())
  const [showCorrectionModal, setShowCorrectionModal] = useState(false)
  const [showDriftAlerts, setShowDriftAlerts] = useState(true)

  // Mock QC data for panels
  const panelsQC: PanelQC[] = useMemo(() => {
    return generatedPanels.map(panel => ({
      panelId: panel.id,
      status: panel.status === 'completed' ? 'completed' : panel.status,
      overallScore: Math.random() * 0.3 + 0.7, // 0.7-1.0
      anatomyScore: Math.random() * 0.3 + 0.7,
      compositionScore: Math.random() * 0.3 + 0.7,
      colorScore: Math.random() * 0.3 + 0.7,
      continuityScore: Math.random() * 0.3 + 0.7,
      failureReasons: Math.random() > 0.8 ? ['anatomy_issue', 'color_inconsistency'] : [],
      driftDetected: Math.random() > 0.9,
      driftScore: Math.random() * 0.3,
    }))
  }, [generatedPanels])

  // Filter and sort panels
  const filteredPanels = useMemo(() => {
    let result = [...panelsQC]

    switch (filter) {
      case 'passed':
        result = result.filter(p => p.overallScore >= 0.8 && !p.driftDetected)
        break
      case 'failed':
        result = result.filter(p => p.status === 'failed' || p.overallScore < 0.6)
        break
      case 'needs_correction':
        result = result.filter(p => p.status === 'needs_correction' || (p.overallScore >= 0.6 && p.overallScore < 0.8))
        break
      case 'drift':
        result = result.filter(p => p.driftDetected)
        break
    }

    switch (sortBy) {
      case 'newest':
        result.sort((a, b) => b.panelId.localeCompare(a.panelId))
        break
      case 'score':
        result.sort((a, b) => a.overallScore - b.overallScore)
        break
      case 'drift':
        result.sort((a, b) => b.driftScore - a.driftScore)
        break
    }

    return result
  }, [panelsQC, filter, sortBy])

  // Calculate stats
  const stats = useMemo(() => {
    const total = panelsQC.length
    const passed = panelsQC.filter(p => p.overallScore >= 0.8).length
    const failed = panelsQC.filter(p => p.status === 'failed' || p.overallScore < 0.6).length
    const needsCorrection = panelsQC.filter(p => p.overallScore >= 0.6 && p.overallScore < 0.8).length
    const driftCount = panelsQC.filter(p => p.driftDetected).length
    const avgScore = panelsQC.length > 0 
      ? panelsQC.reduce((sum, p) => sum + p.overallScore, 0) / panelsQC.length 
      : 0

    return { total, passed, failed, needsCorrection, driftCount, avgScore }
  }, [panelsQC])

  // Failure breakdown
  const failureBreakdown = useMemo(() => {
    const counts: Record<string, number> = {}
    panelsQC.forEach(panel => {
      panel.failureReasons.forEach(reason => {
        counts[reason] = (counts[reason] || 0) + 1
      })
    })
    return Object.entries(counts).sort((a, b) => b[1] - a[1])
  }, [panelsQC])

  const togglePanelSelection = (panelId: string) => {
    setSelectedPanels(prev => {
      const newSet = new Set(prev)
      if (newSet.has(panelId)) {
        newSet.delete(panelId)
      } else {
        newSet.add(panelId)
      }
      return newSet
    })
  }

  const handleBatchCorrect = () => {
    if (selectedPanels.size > 0) {
      setShowCorrectionModal(true)
    }
  }

  if (!isOpen) return null

  return (
    <div className="qc-dashboard-overlay" onClick={onClose}>
      <div className="qc-dashboard" onClick={e => e.stopPropagation()}>
        <header className="qc-header">
          <h2>🔍 Quality Control Dashboard</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </header>

        {/* Quality Meter */}
        <div className="qc-quality-meter">
          <div className="meter-circle">
            <svg viewBox="0 0 100 100">
              <circle className="meter-bg" cx="50" cy="50" r="45" />
              <circle 
                className="meter-fill"
                cx="50" cy="50" r="45"
                style={{ 
                  strokeDasharray: `${stats.avgScore * 283} 283`,
                  stroke: stats.avgScore >= 0.8 ? '#4caf50' : stats.avgScore >= 0.6 ? '#ff9800' : '#f44336'
                }}
              />
            </svg>
            <div className="meter-value">
              <span className="meter-score">{Math.round(stats.avgScore * 100)}%</span>
              <span className="meter-label">Overall</span>
            </div>
          </div>

          <div className="qc-stats">
            <StatCard label="Total" value={stats.total} />
            <StatCard label="Passed" value={stats.passed} color="#4caf50" />
            <StatCard label="Needs Work" value={stats.needsCorrection} color="#ff9800" />
            <StatCard label="Failed" value={stats.failed} color="#f44336" />
            <StatCard label="Drift" value={stats.driftCount} color="#9c27b0" />
          </div>
        </div>

        {/* Drift Alerts */}
        {showDriftAlerts && stats.driftCount > 0 && (
          <div className="drift-alert-banner">
            <span className="alert-icon">⚠️</span>
            <div className="alert-content">
              <strong>Character Drift Detected</strong>
              <span>{stats.driftCount} panels show identity inconsistencies</span>
            </div>
            <button className="alert-action" onClick={() => setFilter('drift')}>
              View Affected
            </button>
            <button className="alert-close" onClick={() => setShowDriftAlerts(false)}>
              ×
            </button>
          </div>
        )}

        {/* Filters */}
        <div className="qc-filters">
          <div className="filter-tabs">
            {(['all', 'passed', 'needs_correction', 'failed', 'drift'] as FilterType[]).map(f => (
              <button
                key={f}
                className={`filter-tab ${filter === f ? 'active' : ''}`}
                onClick={() => setFilter(f)}
              >
                {f.replace('_', ' ')}
                {f === 'all' && <span className="count">{stats.total}</span>}
                {f === 'passed' && stats.passed > 0 && <span className="count">{stats.passed}</span>}
                {f === 'needs_correction' && stats.needsCorrection > 0 && <span className="count">{stats.needsCorrection}</span>}
                {f === 'failed' && stats.failed > 0 && <span className="count">{stats.failed}</span>}
                {f === 'drift' && stats.driftCount > 0 && <span className="count">{stats.driftCount}</span>}
              </button>
            ))}
          </div>

          <select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value as SortBy)}
            className="sort-select"
          >
            <option value="newest">Newest First</option>
            <option value="score">Lowest Score</option>
            <option value="drift">Highest Drift</option>
          </select>
        </div>

        {/* Batch Actions */}
        {selectedPanels.size > 0 && (
          <div className="batch-actions">
            <span>{selectedPanels.size} panels selected</span>
            <button className="batch-correct-btn" onClick={handleBatchCorrect}>
              Request Correction
            </button>
            <button 
              className="batch-clear-btn" 
              onClick={() => setSelectedPanels(new Set())}
            >
              Clear
            </button>
          </div>
        )}

        {/* Panels Grid */}
        <div className="qc-panels-grid">
          {filteredPanels.map(panel => (
            <QCPanelCard
              key={panel.panelId}
              panel={panel}
              isSelected={selectedPanels.has(panel.panelId)}
              onToggleSelect={() => togglePanelSelection(panel.panelId)}
            />
          ))}
        </div>

        {filteredPanels.length === 0 && (
          <div className="qc-empty">
            <p>No panels match the current filter</p>
            <button onClick={() => setFilter('all')}>Show all panels</button>
          </div>
        )}

        {/* Failure Breakdown */}
        {failureBreakdown.length > 0 && (
          <div className="failure-breakdown">
            <h4>Common Issues</h4>
            <div className="breakdown-list">
              {failureBreakdown.map(([reason, count]) => (
                <div key={reason} className="breakdown-item">
                  <span className="reason">{formatFailureReason(reason)}</span>
                  <span className="count">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Correction Modal */}
        {showCorrectionModal && (
          <CorrectionModal
            selectedCount={selectedPanels.size}
            onClose={() => setShowCorrectionModal(false)}
            onSubmit={(priority, reason) => {
              console.log('Requesting correction:', { panels: Array.from(selectedPanels), priority, reason })
              setShowCorrectionModal(false)
              setSelectedPanels(new Set())
            }}
          />
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <div className="stat-card" style={{ borderColor: color }}>
      <span className="stat-value" style={{ color }}>{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  )
}

interface QCPanelCardProps {
  panel: PanelQC
  isSelected: boolean
  onToggleSelect: () => void
}

function QCPanelCard({ panel, isSelected, onToggleSelect }: QCPanelCardProps) {
  const scoreColor = panel.overallScore >= 0.8 ? '#4caf50' : 
                     panel.overallScore >= 0.6 ? '#ff9800' : '#f44336'

  return (
    <div className={`qc-panel-card ${panel.status} ${isSelected ? 'selected' : ''}`}>
      <div className="panel-header">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggleSelect}
          className="panel-checkbox"
        />
        <span className="panel-id">{panel.panelId.slice(-8)}</span>
        {panel.driftDetected && (
          <span className="drift-badge" title="Character drift detected">
            ⚠️ Drift
          </span>
        )}
      </div>

      <div className="panel-preview">
        {panel.imageUrl ? (
          <img src={panel.imageUrl} alt="Panel preview" />
        ) : (
          <div className="preview-placeholder">
            <span>🖼️</span>
          </div>
        )}
      </div>

      <div className="panel-scores">
        <div className="main-score" style={{ color: scoreColor }}>
          {Math.round(panel.overallScore * 100)}%
        </div>
        <div className="score-breakdown">
          <ScoreBar label="Anatomy" score={panel.anatomyScore} />
          <ScoreBar label="Composition" score={panel.compositionScore} />
          <ScoreBar label="Color" score={panel.colorScore} />
          <ScoreBar label="Continuity" score={panel.continuityScore} />
        </div>
      </div>

      {panel.failureReasons.length > 0 && (
        <div className="panel-issues">
          {panel.failureReasons.map(reason => (
            <span key={reason} className="issue-tag">
              {formatFailureReason(reason)}
            </span>
          ))}
        </div>
      )}

      <div className="panel-actions">
        <button className="regenerate-btn">Regenerate</button>
        <button className="correct-btn">Correct</button>
      </div>
    </div>
  )
}

function ScoreBar({ label, score }: { label: string; score: number }) {
  const color = score >= 0.8 ? '#4caf50' : score >= 0.6 ? '#ff9800' : '#f44336'
  return (
    <div className="score-bar">
      <span className="score-label">{label}</span>
      <div className="score-track">
        <div className="score-fill" style={{ width: `${score * 100}%`, background: color }} />
      </div>
      <span className="score-value">{Math.round(score * 100)}</span>
    </div>
  )
}

interface CorrectionModalProps {
  selectedCount: number
  onClose: () => void
  onSubmit: (priority: string, reason: string) => void
}

function CorrectionModal({ selectedCount, onClose, onSubmit }: CorrectionModalProps) {
  const [priority, setPriority] = useState('medium')
  const [reason, setReason] = useState('')

  return (
    <div className="correction-modal-overlay" onClick={onClose}>
      <div className="correction-modal" onClick={e => e.stopPropagation()}>
        <h3>Request Correction</h3>
        <p className="selected-info">{selectedCount} panels selected</p>

        <div className="form-group">
          <label>Priority</label>
          <div className="priority-options">
            {['low', 'medium', 'high'].map(p => (
              <button
                key={p}
                className={`priority-btn ${priority === p ? 'selected' : ''}`}
                onClick={() => setPriority(p)}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label>Correction Reason</label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Describe what needs to be corrected..."
            rows={3}
          />
        </div>

        <div className="modal-actions">
          <button className="secondary-btn" onClick={onClose}>Cancel</button>
          <button 
            className="primary-btn" 
            onClick={() => onSubmit(priority, reason)}
            disabled={!reason.trim()}
          >
            Submit Request
          </button>
        </div>
      </div>
    </div>
  )
}

function formatFailureReason(reason: string): string {
  const map: Record<string, string> = {
    'anatomy_issue': 'Anatomy',
    'color_inconsistency': 'Color',
    'composition_problem': 'Composition',
    'character_drift': 'Drift',
    'lighting_mismatch': 'Lighting',
  }
  return map[reason] || reason.replace('_', ' ')
}
