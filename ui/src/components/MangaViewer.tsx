import { useEffect, useState, useCallback, useRef } from 'react'
import { useAppStore } from '../store'
import './MangaViewer.css'

interface MangaViewerProps {
  volumeId: string
  initialPage?: number
  onClose: () => void
}

interface PageInfo {
  page_number: number
  format: string
  width: number
  height: number
  hash: string
}

interface VolumeInfo {
  volume_id: string
  title: string
  page_count: number
  pages: PageInfo[]
}

export function MangaViewer({ volumeId, initialPage = 1, onClose }: MangaViewerProps) {
  const { addToast, updateMangaReadingProgress, getMangaReadingProgress } = useAppStore()
  const [volume, setVolume] = useState<VolumeInfo | null>(null)
  const [currentPage, setCurrentPage] = useState(initialPage)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [zoom, setZoom] = useState(1)
  const [showThumbnails, setShowThumbnails] = useState(true)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [fitMode, setFitMode] = useState<'width' | 'height' | 'original'>('height')
  const imageRef = useRef<HTMLImageElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const progressSaveTimeout = useRef<NodeJS.Timeout | null>(null)

  const API_BASE = 'http://localhost:8000'
  
  // Load saved progress when volume loads
  useEffect(() => {
    if (volume && volumeId) {
      const saved = getMangaReadingProgress(volumeId)
      if (saved && saved.lastPage > 0 && saved.lastPage <= volume.page_count) {
        // Only use saved page if initialPage is 1 (default), otherwise respect the prop
        if (initialPage === 1) {
          setCurrentPage(saved.lastPage)
          addToast({ 
            message: `Resumed from page ${saved.lastPage} (${saved.percentComplete}% complete)`, 
            type: 'info' 
          })
        }
      }
    }
  }, [volume, volumeId])

  // Fetch volume info
  useEffect(() => {
    const fetchVolume = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/manga/${volumeId}`)
        if (!response.ok) {
          throw new Error('Failed to fetch volume')
        }
        const data = await response.json()
        if (data.success) {
          setVolume(data.volume)
          // Validate initial page
          if (initialPage < 1 || initialPage > data.volume.page_count) {
            setCurrentPage(1)
          }
        } else {
          throw new Error(data.message || 'Unknown error')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load manga')
        addToast({ message: 'Failed to load manga volume', type: 'error' })
      } finally {
        setLoading(false)
      }
    }

    fetchVolume()
  }, [volumeId, initialPage, addToast])

  // Keyboard navigation
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
      e.preventDefault()
      goToPrevious()
    } else if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {
      e.preventDefault()
      goToNext()
    } else if (e.key === 'Escape') {
      onClose()
    } else if (e.key === 'f' || e.key === 'F') {
      toggleFullscreen()
    } else if (e.key === '+' || e.key === '=') {
      zoomIn()
    } else if (e.key === '-' || e.key === '_') {
      zoomOut()
    } else if (e.key === '0') {
      resetZoom()
    } else if (e.key === 't' || e.key === 'T') {
      setShowThumbnails(prev => !prev)
    }
  }, [currentPage, volume, zoom])

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  const goToPage = (page: number) => {
    if (!volume) return
    if (page >= 1 && page <= volume.page_count) {
      setCurrentPage(page)
      setZoom(1) // Reset zoom on page change
      
      // Save progress (debounced to avoid excessive writes)
      if (progressSaveTimeout.current) {
        clearTimeout(progressSaveTimeout.current)
      }
      progressSaveTimeout.current = setTimeout(() => {
        updateMangaReadingProgress(volumeId, page, volume.page_count)
      }, 500)
    }
  }
  
  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (progressSaveTimeout.current) {
        clearTimeout(progressSaveTimeout.current)
      }
    }
  }, [])

  const goToNext = () => {
    if (volume && currentPage < volume.page_count) {
      goToPage(currentPage + 1)
    }
  }

  const goToPrevious = () => {
    if (currentPage > 1) {
      goToPage(currentPage - 1)
    }
  }

  const zoomIn = () => setZoom(prev => Math.min(prev + 0.25, 3))
  const zoomOut = () => setZoom(prev => Math.max(prev - 0.25, 0.5))
  const resetZoom = () => setZoom(1)

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  // Handle fullscreen change events
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])

  const getImageUrl = (pageNum: number) => {
    return `${API_BASE}/api/manga/${volumeId}/pages/${pageNum}/image`
  }

  if (loading) {
    return (
      <div className="manga-viewer-overlay" ref={containerRef}>
        <div className="manga-viewer-loading">
          <div className="spinner" />
          <p>Loading manga...</p>
        </div>
      </div>
    )
  }

  if (error || !volume) {
    return (
      <div className="manga-viewer-overlay" ref={containerRef}>
        <div className="manga-viewer-error">
          <p>❌ {error || 'Failed to load manga'}</p>
          <button onClick={onClose} className="close-btn">Close</button>
        </div>
      </div>
    )
  }

  return (
    <div className={`manga-viewer-overlay ${isFullscreen ? 'fullscreen' : ''}`} ref={containerRef}>
      {/* Header */}
      <div className="manga-viewer-header">
        <div className="manga-viewer-title">
          <span className="manga-icon">📖</span>
          <span className="manga-title-text">{volume.title}</span>
        </div>
        <div className="manga-viewer-page-info">
          Page {currentPage} of {volume.page_count}
        </div>
        <div className="manga-viewer-controls">
          <button 
            className="control-btn" 
            onClick={() => setShowThumbnails(!showThumbnails)}
            title="Toggle thumbnails (T)"
          >
            {showThumbnails ? '📑' : '📄'}
          </button>
          <button 
            className="control-btn" 
            onClick={toggleFullscreen}
            title="Fullscreen (F)"
          >
            {isFullscreen ? '⛶' : '⛶'}
          </button>
          <button 
            className="control-btn close" 
            onClick={onClose}
            title="Close (Esc)"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Main content area */}
      <div className="manga-viewer-content">
        {/* Thumbnail sidebar */}
        {showThumbnails && (
          <div className="manga-thumbnails">
            <div className="thumbnails-header">
              Pages
            </div>
            <div className="thumbnails-list">
              {volume.pages.map((page) => (
                <div
                  key={page.page_number}
                  className={`thumbnail-item ${currentPage === page.page_number ? 'active' : ''}`}
                  onClick={() => goToPage(page.page_number)}
                >
                  <div className="thumbnail-number">{page.page_number}</div>
                  <img
                    src={getImageUrl(page.page_number)}
                    alt={`Page ${page.page_number}`}
                    loading="lazy"
                    className="thumbnail-image"
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Image viewer */}
        <div className="manga-image-container">
          {/* Navigation arrows */}
          <button
            className="nav-arrow prev"
            onClick={goToPrevious}
            disabled={currentPage === 1}
            title="Previous page (←)"
          >
            ‹
          </button>

          {/* Image */}
          <div 
            className="manga-image-wrapper"
            style={{
              transform: `scale(${zoom})`,
              transformOrigin: 'center center',
            }}
          >
            <img
              ref={imageRef}
              src={getImageUrl(currentPage)}
              alt={`Page ${currentPage}`}
              className={`manga-image fit-${fitMode}`}
              onDoubleClick={() => setZoom(zoom === 1 ? 2 : 1)}
            />
          </div>

          <button
            className="nav-arrow next"
            onClick={goToNext}
            disabled={currentPage === volume.page_count}
            title="Next page (→)"
          >
            ›
          </button>
        </div>
      </div>

      {/* Footer controls */}
      <div className="manga-viewer-footer">
        <div className="zoom-controls">
          <button onClick={zoomOut} title="Zoom out (-)">−</button>
          <span className="zoom-level">{Math.round(zoom * 100)}%</span>
          <button onClick={zoomIn} title="Zoom in (+)">+</button>
          <button onClick={resetZoom} title="Reset zoom (0)">⟲</button>
        </div>

        <div className="page-controls">
          <button 
            onClick={goToPrevious}
            disabled={currentPage === 1}
            title="Previous"
          >
            ← Prev
          </button>
          
          <input
            type="number"
            min={1}
            max={volume.page_count}
            value={currentPage}
            onChange={(e) => goToPage(parseInt(e.target.value) || 1)}
            className="page-input"
          />
          <span>/ {volume.page_count}</span>
          
          <button 
            onClick={goToNext}
            disabled={currentPage === volume.page_count}
            title="Next"
          >
            Next →
          </button>
        </div>

        <div className="fit-controls">
          <button 
            className={fitMode === 'height' ? 'active' : ''}
            onClick={() => setFitMode('height')}
            title="Fit to height"
          >
            ↕
          </button>
          <button 
            className={fitMode === 'width' ? 'active' : ''}
            onClick={() => setFitMode('width')}
            title="Fit to width"
          >
            ↔
          </button>
          <button 
            className={fitMode === 'original' ? 'active' : ''}
            onClick={() => setFitMode('original')}
            title="Original size"
          >
            1:1
          </button>
        </div>
      </div>

      {/* Keyboard shortcuts help */}
      <div className="manga-shortcuts-help">
        <span>← → Navigate</span>
        <span>+ − Zoom</span>
        <span>F Fullscreen</span>
        <span>T Thumbnails</span>
        <span>Esc Close</span>
      </div>
    </div>
  )
}
