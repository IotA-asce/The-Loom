import { useEffect, useState } from 'react'
import { useAppStore } from '../store'
import './MangaLibrary.css'

export function MangaLibrary() {
  const { mangaVolumes, fetchMangaVolumes, deleteMangaVolume, updateMangaVolume, addToast, selectNode, nodes, openMangaViewer, getMangaReadingProgress } = useAppStore()
  const [loading, setLoading] = useState(false)
  const [selectedVolume, setSelectedVolume] = useState<string | null>(null)
  const [progressMap, setProgressMap] = useState<Record<string, { lastPage: number; totalPages: number; percentComplete: number }>>({})
  const [editingVolume, setEditingVolume] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [selectedVolumes, setSelectedVolumes] = useState<Set<string>>(new Set())
  const [batchMode, setBatchMode] = useState(false)

  useEffect(() => {
    loadVolumes()
  }, [])
  
  // Load reading progress for all volumes
  useEffect(() => {
    const progress: Record<string, { lastPage: number; totalPages: number; percentComplete: number }> = {}
    mangaVolumes.forEach(volume => {
      const p = getMangaReadingProgress(volume.volume_id)
      if (p) {
        progress[volume.volume_id] = p
      }
    })
    setProgressMap(progress)
  }, [mangaVolumes])

  const loadVolumes = async () => {
    setLoading(true)
    await fetchMangaVolumes()
    setLoading(false)
  }

  const handleDelete = async (volumeId: string, title: string) => {
    if (!confirm(`Delete manga "${title}"? This cannot be undone.`)) {
      return
    }

    const success = await deleteMangaVolume(volumeId)
    if (success) {
      addToast({ message: `Deleted "${title}"`, type: 'success' })
    } else {
      addToast({ message: 'Failed to delete manga', type: 'error' })
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
  }

  const handleGoToNode = (graphNodeId: string) => {
    // Find the node in the graph
    const node = nodes.find(n => n.id === graphNodeId)
    if (node) {
      selectNode(graphNodeId)
      addToast({ message: `Navigated to "${node.label}" in graph`, type: 'success' })
    } else {
      addToast({ message: 'Node not found in graph. Try refreshing.', type: 'error' })
    }
  }
  
  const handleStartEdit = (volume: typeof mangaVolumes[0]) => {
    setEditingVolume(volume.volume_id)
    setEditTitle(volume.title)
  }
  
  const handleCancelEdit = () => {
    setEditingVolume(null)
    setEditTitle('')
  }
  
  const handleSaveEdit = async (volumeId: string) => {
    if (!editTitle.trim()) {
      addToast({ message: 'Title cannot be empty', type: 'error' })
      return
    }
    
    const success = await updateMangaVolume(volumeId, { title: editTitle.trim() })
    if (success) {
      addToast({ message: 'Title updated successfully', type: 'success' })
      setEditingVolume(null)
    } else {
      addToast({ message: 'Failed to update title', type: 'error' })
    }
  }
  
  // Batch operations
  const toggleVolumeSelection = (volumeId: string) => {
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
  
  const selectAllVolumes = () => {
    if (selectedVolumes.size === mangaVolumes.length) {
      setSelectedVolumes(new Set())
    } else {
      setSelectedVolumes(new Set(mangaVolumes.map(v => v.volume_id)))
    }
  }
  
  const handleBatchDelete = async () => {
    if (selectedVolumes.size === 0) return
    
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
    setBatchMode(false)
  }
  
  const exitBatchMode = () => {
    setBatchMode(false)
    setSelectedVolumes(new Set())
  }
  
  // Story extraction
  const [extractingVolume, setExtractingVolume] = useState<string | null>(null)
  
  const handleExtractStory = async (volume: typeof mangaVolumes[0]) => {
    if (!confirm(`Extract story from "${volume.title}"?\n\nThis will use AI to analyze the manga text and create scene nodes in your story graph.`)) {
      return
    }
    
    setExtractingVolume(volume.volume_id)
    addToast({ message: `Extracting story from "${volume.title}"... This may take a minute.`, type: 'info' })
    
    try {
      const response = await fetch(`/api/manga/${volume.volume_id}/extract-story`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ volume_id: volume.volume_id }),
      })
      
      if (!response.ok) {
        throw new Error('Extraction failed')
      }
      
      const result = await response.json()
      
      if (result.success) {
        addToast({ 
          message: `Extracted ${result.scenes.length} scenes! Reload the graph to see them.`, 
          type: 'success' 
        })
      } else {
        addToast({ message: result.message || 'No text found to extract', type: 'warning' })
      }
    } catch (error) {
      addToast({ message: 'Failed to extract story', type: 'error' })
    } finally {
      setExtractingVolume(null)
    }
  }

  if (loading) {
    return (
      <div className="manga-library">
        <div className="manga-loading">
          <div className="spinner" />
          <p>Loading manga library...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="manga-library">
      <div className="manga-header">
        <h3 className="manga-title">📚 Imported Manga</h3>
        <div className="manga-header-actions">
          {batchMode ? (
            <>
              <button 
                className="manga-batch-btn"
                onClick={selectAllVolumes}
                title={selectedVolumes.size === mangaVolumes.length ? "Deselect all" : "Select all"}
              >
                {selectedVolumes.size === mangaVolumes.length ? '☐' : '☑'} Select All
              </button>
              <button 
                className="manga-batch-btn delete"
                onClick={handleBatchDelete}
                disabled={selectedVolumes.size === 0}
                title="Delete selected"
              >
                🗑️ ({selectedVolumes.size})
              </button>
              <button 
                className="manga-batch-btn cancel"
                onClick={exitBatchMode}
                title="Exit batch mode"
              >
                ✕
              </button>
            </>
          ) : (
            <>
              <button 
                className="manga-batch-btn"
                onClick={() => setBatchMode(true)}
                title="Batch operations"
              >
                ☑️
              </button>
              <button 
                className="manga-refresh-btn"
                onClick={loadVolumes}
                title="Refresh list"
              >
                🔄
              </button>
            </>
          )}
        </div>
      </div>

      {mangaVolumes.length === 0 ? (
        <div className="manga-empty">
          <p>No manga imported yet.</p>
          <p className="manga-hint">
            Use the Import Manga Folder section above, or the CLI:{' '}
            <code>python scripts/import_manga_folder.py /path/to/manga "Title"</code>
          </p>
        </div>
      ) : (
        <ul className="manga-list">
          {mangaVolumes.map((volume) => {
            const progress = progressMap[volume.volume_id]
            const hasProgress = progress && progress.lastPage > 1
            const isEditing = editingVolume === volume.volume_id
            
            return (
              <li 
                key={volume.volume_id}
                className={`manga-item ${selectedVolume === volume.volume_id ? 'selected' : ''} ${isEditing ? 'editing' : ''} ${batchMode ? 'batch-mode' : ''}`}
                onClick={() => {
                  if (batchMode) {
                    toggleVolumeSelection(volume.volume_id)
                  } else {
                    setSelectedVolume(volume.volume_id)
                  }
                }}
              >
                {batchMode && (
                  <input
                    type="checkbox"
                    checked={selectedVolumes.has(volume.volume_id)}
                    onChange={() => toggleVolumeSelection(volume.volume_id)}
                    onClick={(e) => e.stopPropagation()}
                    className="manga-checkbox"
                  />
                )}
                <div className="manga-item-info">
                  {isEditing ? (
                    <div className="manga-edit-form" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSaveEdit(volume.volume_id)
                          if (e.key === 'Escape') handleCancelEdit()
                        }}
                        autoFocus
                        className="manga-edit-input"
                      />
                      <div className="manga-edit-actions">
                        <button 
                          onClick={() => handleSaveEdit(volume.volume_id)}
                          className="manga-edit-btn save"
                          title="Save"
                        >
                          ✓
                        </button>
                        <button 
                          onClick={handleCancelEdit}
                          className="manga-edit-btn cancel"
                          title="Cancel"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <span className="manga-item-title">{volume.title}</span>
                      <span className="manga-item-meta">
                        {volume.page_count} pages • Imported {formatDate(volume.created_at)}
                      </span>
                      {hasProgress && (
                        <div className="manga-progress">
                          <div className="manga-progress-bar">
                            <div 
                              className="manga-progress-fill" 
                              style={{ width: `${progress.percentComplete}%` }}
                            />
                          </div>
                          <span className="manga-progress-text">
                            {progress.percentComplete}% • Page {progress.lastPage}
                          </span>
                        </div>
                      )}
                      {volume.graph_node_id && (
                        <span className="manga-item-node" title="Has graph node">
                          📝 In graph
                        </span>
                      )}
                    </>
                  )}
                </div>
                {!isEditing && (
                  <div className="manga-item-actions">
                    {hasProgress ? (
                      <button
                        className="manga-action-btn resume"
                        onClick={(e) => {
                          e.stopPropagation()
                          openMangaViewer(volume.volume_id)
                        }}
                        title={`Resume from page ${progress.lastPage}`}
                      >
                        ▶️
                      </button>
                    ) : (
                      <button
                        className="manga-action-btn view"
                        onClick={(e) => {
                          e.stopPropagation()
                          openMangaViewer(volume.volume_id)
                        }}
                        title="View manga"
                      >
                        👁️
                      </button>
                    )}
                    <button
                      className="manga-action-btn edit"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleStartEdit(volume)
                      }}
                      title="Edit title"
                    >
                      ✏️
                    </button>
                    <button
                      className="manga-action-btn extract"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleExtractStory(volume)
                      }}
                      disabled={extractingVolume === volume.volume_id}
                      title="Extract story from manga"
                    >
                      {extractingVolume === volume.volume_id ? '⏳' : '📖'}
                    </button>
                    {volume.graph_node_id && (
                      <button
                        className="manga-action-btn goto"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleGoToNode(volume.graph_node_id!)
                        }}
                        title="Go to node in graph"
                      >
                        📝
                      </button>
                    )}
                    <button
                      className="manga-action-btn delete"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDelete(volume.volume_id, volume.title)
                      }}
                      title="Delete"
                    >
                      🗑️
                    </button>
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      )}

      <div className="manga-footer">
        <span className="manga-count">
          {mangaVolumes.length} volume{mangaVolumes.length !== 1 ? 's' : ''}
        </span>
      </div>
    </div>
  )
}
