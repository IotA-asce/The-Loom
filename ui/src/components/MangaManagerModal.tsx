import { useState, useEffect, useCallback } from 'react'
import { useAppStore } from '../store'
import './MangaManagerModal.css'

interface MangaVolume {
  volume_id: string
  title: string
  page_count: number
  source_hash: string
  graph_node_id?: string
  created_at: string
}

interface MangaManagerModalProps {
  isOpen: boolean
  onClose: () => void
}

export function MangaManagerModal({ isOpen, onClose }: MangaManagerModalProps) {
  const { addToast, openMangaViewer, selectNode, deleteMangaVolume } = useAppStore()
  const [volumes, setVolumes] = useState<MangaVolume[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'date' | 'title' | 'pages'>('date')
  const [selectedVolumes, setSelectedVolumes] = useState<Set<string>>(new Set())
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list')
  const [showConfirmDelete, setShowConfirmDelete] = useState<string | null>(null)

  const fetchVolumes = useCallback(async () => {
    try {
      const response = await fetch('/api/manga')
      if (response.ok) {
        const data = await response.json()
        setVolumes(data.volumes || [])
      }
    } catch (error) {
      console.error('Failed to fetch volumes:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (isOpen) {
      fetchVolumes()
    }
  }, [isOpen, fetchVolumes])

  // Filter and sort volumes
  const filteredVolumes = volumes
    .filter(v => 
      v.title.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a, b) => {
      switch (sortBy) {
        case 'date':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        case 'title':
          return a.title.localeCompare(b.title)
        case 'pages':
          return b.page_count - a.page_count
        default:
          return 0
      }
    })

  const toggleSelection = (volumeId: string) => {
    setSelectedVolumes(prev => {
      const newSet = new Set(prev)
      if (newSet.has(volumeId)) {
        newSet.delete(volumeId)
      } else {
        newSet.add(volumeId)
      }
      return newSet
    })
  }

  const selectAll = () => {
    if (selectedVolumes.size === filteredVolumes.length) {
      setSelectedVolumes(new Set())
    } else {
      setSelectedVolumes(new Set(filteredVolumes.map(v => v.volume_id)))
    }
  }

  const handleDelete = async (volumeId: string) => {
    const success = await deleteMangaVolume(volumeId)
    if (success) {
      addToast({ message: 'Manga deleted successfully', type: 'success' })
      fetchVolumes()
    } else {
      addToast({ message: 'Failed to delete manga', type: 'error' })
    }
    setShowConfirmDelete(null)
  }

  const handleBatchDelete = async () => {
    if (!confirm(`Delete ${selectedVolumes.size} manga volumes? This cannot be undone.`)) {
      return
    }

    let deleted = 0
    for (const volumeId of selectedVolumes) {
      const success = await deleteMangaVolume(volumeId)
      if (success) deleted++
    }

    addToast({ 
      message: `Deleted ${deleted} of ${selectedVolumes.size} volumes`, 
      type: deleted > 0 ? 'success' : 'error'
    })
    
    setSelectedVolumes(new Set())
    fetchVolumes()
  }

  const handleView = (volume: MangaVolume) => {
    openMangaViewer(volume.volume_id)
    onClose()
  }

  const handleGoToNode = (volume: MangaVolume) => {
    if (volume.graph_node_id) {
      selectNode(volume.graph_node_id)
      onClose()
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const formatFileSize = (pages: number) => {
    // Rough estimate: ~500KB per page
    const bytes = pages * 500 * 1024
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  if (!isOpen) return null

  return (
    <div className="manga-manager-overlay" onClick={onClose}>
      <div className="manga-manager-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="manager-header">
          <h2>📚 Manga Library</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {/* Toolbar */}
        <div className="manager-toolbar">
          <div className="toolbar-left">
            <input
              type="text"
              placeholder="Search manga..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value as any)}
              className="sort-select"
            >
              <option value="date">Sort by Date</option>
              <option value="title">Sort by Title</option>
              <option value="pages">Sort by Pages</option>
            </select>
          </div>

          <div className="toolbar-right">
            <div className="view-toggle">
              <button 
                className={viewMode === 'list' ? 'active' : ''}
                onClick={() => setViewMode('list')}
                title="List view"
              >
                ☰
              </button>
              <button 
                className={viewMode === 'grid' ? 'active' : ''}
                onClick={() => setViewMode('grid')}
                title="Grid view"
              >
                ⊞
              </button>
            </div>
            
            {selectedVolumes.size > 0 && (
              <button 
                className="batch-delete-btn"
                onClick={handleBatchDelete}
              >
                🗑️ Delete ({selectedVolumes.size})
              </button>
            )}
          </div>
        </div>

        {/* Stats Bar */}
        <div className="manager-stats">
          <span>{filteredVolumes.length} manga</span>
          <span>{filteredVolumes.reduce((sum, v) => sum + v.page_count, 0)} total pages</span>
          <span>{formatFileSize(filteredVolumes.reduce((sum, v) => sum + v.page_count, 0))} estimated</span>
        </div>

        {/* Content */}
        <div className={`manager-content ${viewMode}`}>
          {loading ? (
            <div className="manager-loading">
              <div className="spinner" />
              <p>Loading manga library...</p>
            </div>
          ) : filteredVolumes.length === 0 ? (
            <div className="manager-empty">
              <p>{searchQuery ? 'No manga match your search' : 'No manga imported yet'}</p>
              {!searchQuery && (
                <p className="hint">Import manga using the Import tab in the left sidebar</p>
              )}
            </div>
          ) : (
            <>
              {/* Select All Header */}
              <div className="select-all-bar">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={selectedVolumes.size === filteredVolumes.length && filteredVolumes.length > 0}
                    onChange={selectAll}
                  />
                  <span>Select All</span>
                </label>
              </div>

              {/* Volume List */}
              {filteredVolumes.map((volume) => (
                <div 
                  key={volume.volume_id}
                  className={`volume-item ${selectedVolumes.has(volume.volume_id) ? 'selected' : ''}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedVolumes.has(volume.volume_id)}
                    onChange={() => toggleSelection(volume.volume_id)}
                    className="volume-checkbox"
                  />

                  <div className="volume-info">
                    <h4 className="volume-title">{volume.title}</h4>
                    <div className="volume-meta">
                      <span>{volume.page_count} pages</span>
                      <span>•</span>
                      <span>{formatDate(volume.created_at)}</span>
                      <span>•</span>
                      <span>{formatFileSize(volume.page_count)}</span>
                    </div>
                    {volume.graph_node_id && (
                      <span className="in-graph-badge">📝 In Graph</span>
                    )}
                  </div>

                  <div className="volume-actions">
                    <button
                      className="action-btn view"
                      onClick={() => handleView(volume)}
                      title="Read manga"
                    >
                      👁️ Read
                    </button>
                    {volume.graph_node_id && (
                      <button
                        className="action-btn graph"
                        onClick={() => handleGoToNode(volume)}
                        title="Go to graph node"
                      >
                        🕸️ Graph
                      </button>
                    )}
                    <button
                      className="action-btn delete"
                      onClick={() => setShowConfirmDelete(volume.volume_id)}
                      title="Delete manga"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="manager-footer">
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
          <button 
            className="btn-primary"
            onClick={() => {
              onClose()
              // Focus the import panel
              document.getElementById('import-tab')?.click()
            }}
          >
            📥 Import New Manga
          </button>
        </div>
      </div>

      {/* Confirm Delete Modal */}
      {showConfirmDelete && (
        <div className="confirm-overlay">
          <div className="confirm-modal">
            <h3>Delete Manga?</h3>
            <p>This action cannot be undone. The manga will be permanently removed.</p>
            <div className="confirm-actions">
              <button 
                className="btn-secondary"
                onClick={() => setShowConfirmDelete(null)}
              >
                Cancel
              </button>
              <button 
                className="btn-danger"
                onClick={() => handleDelete(showConfirmDelete)}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MangaManagerModal
