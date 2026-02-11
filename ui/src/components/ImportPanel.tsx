import { useState, useRef } from 'react'
import { useAppStore } from '../store'
import { MangaLibrary } from './MangaLibrary'
import './ImportPanel.css'

export function ImportPanel() {
  const { ingestFile, supportedFormats } = useAppStore()
  const [isImporting, setIsImporting] = useState(false)
  const [importResult, setImportResult] = useState<{
    success: boolean
    message: string
    details?: Record<string, any>
  } | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (file: File) => {
    if (!file) return

    setIsImporting(true)
    setImportResult(null)

    try {
      const result = await ingestFile(file)
      setImportResult({
        success: result.success,
        message: result.success 
          ? `Successfully imported "${file.name}"`
          : `Failed to import "${file.name}"`,
        details: result,
      })
    } catch (error) {
      setImportResult({
        success: false,
        message: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      })
    } finally {
      setIsImporting(false)
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0])
    }
  }

  const onButtonClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="import-panel">
      <h2 className="panel-title">Import Story</h2>
      
      <div
        className={`import-dropzone ${dragActive ? 'active' : ''} ${isImporting ? 'importing' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={onButtonClick}
        role="button"
        tabIndex={0}
        aria-label="Drop files here or click to browse"
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            onButtonClick()
          }
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleChange}
          accept=".txt,.pdf,.epub,.cbz,.zip,.png,.jpg,.jpeg,.webp"
          className="import-input"
          aria-hidden="true"
        />
        
        {isImporting ? (
          <div className="import-loading">
            <div className="spinner" aria-hidden="true" />
            <p>Importing...</p>
          </div>
        ) : (
          <div className="import-prompt">
            <div className="import-icon" aria-hidden="true">📄</div>
            <p className="import-primary">Drop files here or click to browse</p>
            <p className="import-hint">
              Supports: {supportedFormats.text.join(', ')}, {supportedFormats.manga.join(', ')}
            </p>
          </div>
        )}
      </div>

      {importResult && (
        <div 
          className={`import-result ${importResult.success ? 'success' : 'error'}`}
          role="status"
          aria-live="polite"
        >
          <div className="result-header">
            <span className="result-icon" aria-hidden="true">
              {importResult.success ? '✅' : '❌'}
            </span>
            <span className="result-message">{importResult.message}</span>
          </div>
          
          {importResult.details && importResult.success && (
            <div className="result-details">
              {importResult.details.parser && (
                <div className="detail-row">
                  <span className="detail-label">Parser:</span>
                  <span className="detail-value">{importResult.details.parser}</span>
                </div>
              )}
              {importResult.details.chapters !== undefined && (
                <div className="detail-row">
                  <span className="detail-label">Chapters:</span>
                  <span className="detail-value">{importResult.details.chapters}</span>
                </div>
              )}
              {importResult.details.pages !== undefined && (
                <div className="detail-row">
                  <span className="detail-label">Pages:</span>
                  <span className="detail-value">{importResult.details.pages}</span>
                </div>
              )}
              {importResult.details.confidence !== undefined && (
                <div className="detail-row">
                  <span className="detail-label">Confidence:</span>
                  <span className="detail-value">
                    {(importResult.details.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              )}
              {importResult.details.warnings?.length > 0 && (
                <div className="detail-warnings">
                  <span className="detail-label">Warnings:</span>
                  <ul>
                    {importResult.details.warnings.map((w: string, i: number) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
          
          {importResult.details && importResult.details.errors && importResult.details.errors.length > 0 && (
            <div className="result-errors">
              <span className="detail-label">Errors:</span>
              <ul>
                {importResult.details.errors.map((e: string, i: number) => (
                  <li key={i}>{e}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <section className="import-help" aria-labelledby="import-help-title">
        <h3 id="import-help-title" className="section-title">Supported Formats</h3>
        
        <div className="format-group">
          <h4>Text Documents</h4>
          <ul>
            <li><strong>.txt</strong> - Plain text files</li>
            <li><strong>.pdf</strong> - PDF documents</li>
            <li><strong>.epub</strong> - E-book format</li>
          </ul>
        </div>
        
        <div className="format-group">
          <h4>Manga/Comics</h4>
          <ul>
            <li><strong>.cbz</strong> - Comic book archive</li>
            <li><strong>.zip</strong> - ZIP of images</li>
          </ul>
        </div>
        
        <div className="format-group">
          <h4>Images</h4>
          <ul>
            <li><strong>.png, .jpg, .jpeg, .webp</strong> - Single images</li>
          </ul>
        </div>
      </section>
      
      {/* Manga Library */}
      <MangaLibrary />
    </div>
  )
}
