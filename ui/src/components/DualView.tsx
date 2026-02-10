import { useState } from 'react'
import { useAppStore } from '../store'
import './DualView.css'

export function DualView() {
  const {
    dualViewOpen,
    syncState,
    toggleDualView,
    reconcile,
  } = useAppStore()

  const [activeTab, setActiveTab] = useState<'text' | 'image'>('text')

  if (!dualViewOpen) return null

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'synced':
        return '[OK]'
      case 'text_stale':
        return '[TXT]'
      case 'image_stale':
        return '[IMG]'
      case 'both_stale':
        return '[!!]'
      case 'reconciling':
        return '[~]'
      default:
        return '[?]'
    }
  }

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'synced':
        return 'synced'
      case 'text_stale':
      case 'image_stale':
        return 'stale'
      case 'both_stale':
        return 'error'
      case 'reconciling':
        return 'reconciling'
      default:
        return ''
    }
  }

  return (
    <div className="dual-view" role="region" aria-labelledby="dual-view-title">
      <div className="panel-header">
        <h2 id="dual-view-title" className="panel-title">Dual View</h2>
        <button
          onClick={toggleDualView}
          className="close-button"
          aria-label="Close dual view"
        >
          ×
        </button>
      </div>

      {/* Sync badges */}
      {syncState && syncState.badges.length > 0 && (
        <div className="sync-badges" role="status" aria-label="Synchronization status">
          {syncState.badges.map((badge, index) => (
            <span
              key={index}
              className={`sync-badge ${getStatusClass(badge.label.toLowerCase().replace(' ', '_'))}`}
              title={badge.label}
            >
              {badge.icon} {badge.label}
            </span>
          ))}
        </div>
      )}

      {/* Tab navigation */}
      <div className="dual-tabs" role="tablist" aria-label="View tabs">
        <button
          role="tab"
          aria-selected={activeTab === 'text'}
          aria-controls="text-panel"
          onClick={() => setActiveTab('text')}
          className={`tab ${activeTab === 'text' ? 'active' : ''}`}
        >
          Text
          {syncState && (
            <span className={`tab-indicator ${getStatusClass(syncState.textStatus)}`}>
              {getStatusIcon(syncState.textStatus)}
            </span>
          )}
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'image'}
          aria-controls="image-panel"
          onClick={() => setActiveTab('image')}
          className={`tab ${activeTab === 'image' ? 'active' : ''}`}
        >
          Images
          {syncState && (
            <span className={`tab-indicator ${getStatusClass(syncState.imageStatus)}`}>
              {getStatusIcon(syncState.imageStatus)}
            </span>
          )}
        </button>
      </div>

      {/* Tab panels */}
      <div className="dual-panels">
        <div
          id="text-panel"
          role="tabpanel"
          aria-labelledby="text-tab"
          className={`panel ${activeTab === 'text' ? 'active' : ''}`}
        >
          <div className="panel-placeholder">
            <span className="placeholder-icon">📝</span>
            <p>Text Editor</p>
            <p className="placeholder-hint">
              Edit text to trigger image sync
            </p>
          </div>
        </div>

        <div
          id="image-panel"
          role="tabpanel"
          aria-labelledby="image-tab"
          className={`panel ${activeTab === 'image' ? 'active' : ''}`}
        >
          <div className="panel-placeholder">
            <span className="placeholder-icon">🖼️</span>
            <p>Image Preview</p>
            <p className="placeholder-hint">
              Request redraws to trigger text sync
            </p>
          </div>
        </div>
      </div>

      {/* Reconcile actions */}
      {syncState && (
        <div className="reconcile-actions">
          <button
            onClick={() => reconcile(syncState.sceneId, 'v2', 'v2')}
            className="reconcile-button"
            aria-label="Reconcile text and image versions"
          >
            Reconcile Now
          </button>
        </div>
      )}

      {/* Version info */}
      {syncState && (
        <div className="version-info">
          <div className="version-row">
            <span className="version-label">Text:</span>
            <code className="version-value">{syncState.textVersion}</code>
          </div>
          <div className="version-row">
            <span className="version-label">Image:</span>
            <code className="version-value">{syncState.imageVersion}</code>
          </div>
        </div>
      )}
    </div>
  )
}
