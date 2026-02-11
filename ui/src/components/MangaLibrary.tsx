import { useEffect, useState } from 'react'
import { useAppStore } from '../store'
import './MangaLibrary.css'

export function MangaLibrary() {
  const { mangaVolumes, fetchMangaVolumes, deleteMangaVolume, addToast } = useAppStore()
  const [loading, setLoading] = useState(false)
  const [selectedVolume, setSelectedVolume] = useState<string | null>(null)

  useEffect(() => {
    loadVolumes()
  }, [])

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
        <button 
          className="manga-refresh-btn"
          onClick={loadVolumes}
          title="Refresh list"
        >
          🔄
        </button>
      </div>

      {mangaVolumes.length === 0 ? (
        <div className="manga-empty">
          <p>No manga imported yet.</p>
          <p className="manga-hint">
            Use the CLI to import:{' '}
            <code>python scripts/import_manga_folder.py /path/to/manga "Title"</code>
          </p>
        </div>
      ) : (
        <ul className="manga-list">
          {mangaVolumes.map((volume) => (
            <li 
              key={volume.volume_id}
              className={`manga-item ${selectedVolume === volume.volume_id ? 'selected' : ''}`}
              onClick={() => setSelectedVolume(volume.volume_id)}
            >
              <div className="manga-item-info">
                <span className="manga-item-title">{volume.title}</span>
                <span className="manga-item-meta">
                  {volume.page_count} pages • Imported {formatDate(volume.created_at)}
                </span>
                {volume.graph_node_id && (
                  <span className="manga-item-node" title="Has graph node">
                    📝 In graph
                  </span>
                )}
              </div>
              <div className="manga-item-actions">
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
            </li>
          ))}
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
