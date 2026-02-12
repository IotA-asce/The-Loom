import React, { useState, useRef, ChangeEvent, useEffect, useCallback } from 'react';
import { Upload, AlertCircle, CheckCircle, Loader2, FolderOpen, X, Image, FileText, Database } from 'lucide-react';

interface ImportStatus {
  status: 'idle' | 'uploading' | 'processing' | 'success' | 'error';
  message?: string;
  pagesImported?: number;
  progress?: number;
}

interface ImportPhase {
  id: string;
  label: string;
  icon: React.ReactNode;
  progress: number;
  status: 'pending' | 'active' | 'complete' | 'error';
}

interface MangaFolderImportSimpleProps {
  onImportComplete?: (result: { title: string; pages: number; hash: string }) => void;
}

const WS_URL = `ws://${window.location.host}/api/ws`;

export const MangaFolderImportSimple: React.FC<MangaFolderImportSimpleProps> = ({ 
  onImportComplete 
}) => {
  const [title, setTitle] = useState('');
  const [importStatus, setImportStatus] = useState<ImportStatus>({ status: 'idle' });
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [phases, setPhases] = useState<ImportPhase[]>([
    { id: 'upload', label: 'Upload', icon: <Upload className="w-4 h-4" />, progress: 0, status: 'pending' },
    { id: 'analysis', label: 'Thumbnails', icon: <Image className="w-4 h-4" />, progress: 0, status: 'pending' },
    { id: 'ocr', label: 'OCR', icon: <FileText className="w-4 h-4" />, progress: 0, status: 'pending' },
    { id: 'finalize', label: 'Save', icon: <Database className="w-4 h-4" />, progress: 0, status: 'pending' },
  ]);
  const [, setCurrentPhase] = useState<string>('');
  const [processingMessage, setProcessingMessage] = useState('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const clientIdRef = useRef<string>(`client-${Math.random().toString(36).substr(2, 9)}`);

  // Initialize WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket(`${WS_URL}/${clientIdRef.current}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected for import progress');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };
      
      wsRef.current = ws;
    };
    
    connectWebSocket();
    
    return () => {
      wsRef.current?.close();
    };
  }, []);

  const handleWebSocketMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'job_progress':
        updatePhaseProgress(data.data);
        break;
      case 'job_complete':
        handleImportSuccess(data.data);
        break;
      case 'error':
        setImportStatus({
          status: 'error',
          message: data.message || 'Import failed',
        });
        break;
    }
  }, []);

  const updatePhaseProgress = (data: any) => {
    const { phase, message, progress } = data;
    
    setCurrentPhase(phase);
    setProcessingMessage(message);
    setUploadProgress(progress);
    
    setPhases(prev => prev.map(p => {
      if (p.id === phase) {
        return { ...p, status: 'active', progress };
      }
      if (prev.findIndex(ph => ph.id === phase) > prev.findIndex(ph => ph.id === p.id)) {
        return { ...p, status: 'complete', progress: 100 };
      }
      return p;
    }));
  };

  const handleImportSuccess = (data: any) => {
    setPhases(prev => prev.map(p => ({ ...p, status: 'complete', progress: 100 })));
    setImportStatus({
      status: 'success',
      pagesImported: data.pages_imported,
      message: `Successfully imported "${data.title}"`,
    });
    
    onImportComplete?.({
      title: data.title,
      pages: data.pages_imported,
      hash: data.source_hash,
    });
    
    setTimeout(() => {
      clearSelection();
      setImportStatus({ status: 'idle' });
      resetPhases();
    }, 3000);
  };

  const resetPhases = () => {
    setPhases([
      { id: 'upload', label: 'Upload', icon: <Upload className="w-4 h-4" />, progress: 0, status: 'pending' },
      { id: 'analysis', label: 'Thumbnails', icon: <Image className="w-4 h-4" />, progress: 0, status: 'pending' },
      { id: 'ocr', label: 'OCR', icon: <FileText className="w-4 h-4" />, progress: 0, status: 'pending' },
      { id: 'finalize', label: 'Save', icon: <Database className="w-4 h-4" />, progress: 0, status: 'pending' },
    ]);
    setCurrentPhase('');
    setProcessingMessage('');
  };

  const processFiles = (files: File[]) => {
    const supportedFiles = files.filter(file => {
      const ext = file.name.toLowerCase().split('.').pop();
      return ['webp', 'png', 'jpg', 'jpeg'].includes(ext || '');
    });

    supportedFiles.sort((a, b) => {
      const aMatch = a.name.match(/(\d+)/);
      const bMatch = b.name.match(/(\d+)/);
      const aNum = aMatch ? parseInt(aMatch[1]) : 0;
      const bNum = bMatch ? parseInt(bMatch[1]) : 0;
      return aNum - bNum;
    });

    setSelectedFiles(supportedFiles);

    if (!title && supportedFiles.length > 0) {
      const pathParts = supportedFiles[0].webkitRelativePath?.split('/') || [];
      if (pathParts.length > 1) {
        setTitle(pathParts[pathParts.length - 2]);
      }
    }
  };

  const handleFileSelect = (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;
    processFiles(Array.from(files));
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const items = e.dataTransfer.items;
    const files: File[] = [];

    const traverseFileTree = (item: any, fileList: File[]) => {
      if (item.isFile) {
        item.file((file: File) => fileList.push(file));
      } else if (item.isDirectory) {
        const dirReader = item.createReader();
        dirReader.readEntries((entries: any[]) => {
          entries.forEach(entry => traverseFileTree(entry, fileList));
        });
      }
    };

    for (let i = 0; i < items.length; i++) {
      const entry = items[i].webkitGetAsEntry?.();
      if (entry) traverseFileTree(entry, files);
    }

    setTimeout(() => processFiles(files), 100);
  };

  const clearSelection = () => {
    setSelectedFiles([]);
    setTitle('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const totalSize = selectedFiles.reduce((acc, file) => acc + file.size, 0);

  const handleImport = async () => {
    if (selectedFiles.length === 0) {
      setImportStatus({ status: 'error', message: 'No files selected' });
      return;
    }

    if (!title.trim()) {
      setImportStatus({ status: 'error', message: 'Please enter a title' });
      return;
    }

    setImportStatus({ status: 'uploading', progress: 0 });
    setUploadProgress(0);
    resetPhases();
    
    // Mark upload phase as active
    setPhases(prev => prev.map(p => 
      p.id === 'upload' ? { ...p, status: 'active' } : p
    ));

    const formData = new FormData();
    selectedFiles.forEach(file => formData.append('files', file));

    try {
      const xhr = new XMLHttpRequest();
      
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded / e.total) * 100);
          setUploadProgress(percent);
          setPhases(prev => prev.map(p => 
            p.id === 'upload' ? { ...p, progress: percent * 0.25 } : p
          ));
        }
      });

      const response = await new Promise<{ 
        success: boolean; 
        pages_imported: number; 
        title: string; 
        source_hash: string;
        job_id?: string;
      }>((resolve, reject) => {
        xhr.addEventListener('load', () => {
          if (xhr.status === 200) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            const error = JSON.parse(xhr.responseText);
            reject(new Error(error.detail || 'Import failed'));
          }
        });
        
        xhr.addEventListener('error', () => reject(new Error('Network error')));
        xhr.addEventListener('abort', () => reject(new Error('Upload aborted')));
        
        // Include client_id for WebSocket progress tracking
        xhr.open('POST', `/api/ingest/manga/pages?title=${encodeURIComponent(title)}&client_id=${clientIdRef.current}`);
        xhr.send(formData);
      });

      // If we have a job_id, switch to processing state and wait for WebSocket updates
      if (response.job_id) {
        setImportStatus({ status: 'processing', progress: 25 });
        // Subscribe to job updates via WebSocket
        wsRef.current?.send(JSON.stringify({
          action: 'subscribe',
          jobId: response.job_id,
        }));
      } else {
        // Fallback: treat as complete immediately
        handleImportSuccess(response);
      }

    } catch (error) {
      setImportStatus({
        status: 'error',
        message: error instanceof Error ? error.message : 'Import failed',
      });
      setPhases(prev => prev.map(p => 
        p.status === 'active' ? { ...p, status: 'error' } : p
      ));
    }
  };

  const getDropzoneClass = () => {
    const baseClass = 'import-dropzone';
    if (importStatus.status === 'uploading' || importStatus.status === 'processing') return `${baseClass} importing`;
    if (isDragging) return `${baseClass} active`;
    return baseClass;
  };

  const getPhaseIconClass = (status: ImportPhase['status']) => {
    switch (status) {
      case 'complete':
        return 'phase-icon complete';
      case 'active':
        return 'phase-icon active';
      case 'error':
        return 'phase-icon error';
      default:
        return 'phase-icon';
    }
  };

  return (
    <div className="manga-folder-import">
      {/* Title Input */}
      <div className="form-group">
        <label className="form-label">
          Manga Title
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g., Dragon Ball Volume 1"
          disabled={importStatus.status === 'uploading' || importStatus.status === 'processing'}
          className="form-input"
        />
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        {...{ webkitdirectory: '', directory: '' }}
        multiple
        onChange={handleFileSelect}
        className="import-input"
        disabled={importStatus.status === 'uploading' || importStatus.status === 'processing'}
      />

      {/* Drop Zone */}
      {!selectedFiles.length ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={getDropzoneClass()}
        >
          <input
            type="file"
            className="import-input"
            aria-hidden="true"
          />
          
          {importStatus.status === 'uploading' || importStatus.status === 'processing' ? (
            <div className="import-loading">
              <div className="spinner" />
              <div className="upload-progress">
                <p className="upload-text">{processingMessage || 'Processing...'}</p>
                <div className="progress-bar-container">
                  <div 
                    className="progress-bar"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="progress-percent">{Math.round(uploadProgress)}%</p>
              </div>
            </div>
          ) : (
            <div className="import-prompt">
              <div className="import-icon" aria-hidden="true">
                <FolderOpen className="w-8 h-8" />
              </div>
              <p className="import-primary">
                {isDragging ? 'Drop folder here!' : 'Click to select folder'}
              </p>
              <p className="import-hint">
                or drag & drop here
              </p>
              <div className="format-badges">
                <span className="format-badge">.webp</span>
                <span className="format-badge">.png</span>
                <span className="format-badge">.jpg</span>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Selected Files Preview */
        <div className="files-preview">
          <div className="files-header">
            <div className="files-count">
              <CheckCircle className="w-5 h-5" />
              <span>{selectedFiles.length} pages selected</span>
            </div>
            {importStatus.status !== 'uploading' && importStatus.status !== 'processing' && (
              <button
                onClick={clearSelection}
                className="clear-btn"
                aria-label="Clear selection"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* File stats */}
          <div className="files-stats">
            <div className="stat-box">
              <p className="stat-value">{selectedFiles.length}</p>
              <p className="stat-label">Pages</p>
            </div>
            <div className="stat-box">
              <p className="stat-value highlight">{formatFileSize(totalSize)}</p>
              <p className="stat-label">Total Size</p>
            </div>
            <div className="stat-box">
              <p className="stat-value accent">
                {selectedFiles[0]?.name.split('.').pop()?.toUpperCase() || 'IMG'}
              </p>
              <p className="stat-label">Format</p>
            </div>
          </div>

          {/* File list */}
          <div className="files-list">
            {selectedFiles.slice(0, 10).map((file, i) => (
              <div key={i} className="file-item">
                <span className="file-name">{file.name}</span>
                <span className="file-size">{formatFileSize(file.size)}</span>
              </div>
            ))}
            {selectedFiles.length > 10 && (
              <p className="more-files">
                ... and {selectedFiles.length - 10} more
              </p>
            )}
          </div>
        </div>
      )}

      {/* Import Button */}
      {selectedFiles.length > 0 && (
        <button
          onClick={handleImport}
          disabled={importStatus.status === 'uploading' || importStatus.status === 'processing'}
          className="import-btn"
        >
          {importStatus.status === 'uploading' || importStatus.status === 'processing' ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              {importStatus.status === 'uploading' ? 'Uploading...' : 'Processing...'}
              {uploadProgress > 0 && ` ${Math.round(uploadProgress)}%`}
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" />
              Import {selectedFiles.length} Pages
            </>
          )}
        </button>
      )}

      {/* Detailed Progress Panel */}
      {(importStatus.status === 'uploading' || importStatus.status === 'processing') && (
        <div className="import-progress-panel">
          <div className="progress-header">
            <span className="progress-title">{processingMessage || 'Processing...'}</span>
            <span className="progress-percent">{Math.round(uploadProgress)}%</span>
          </div>
          
          <div className="progress-bar-container">
            <div 
              className="progress-bar"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>

          {/* Phase indicators */}
          <div className="import-phases">
            {phases.map((phase, index) => (
              <div key={phase.id} className="phase-item">
                <div className={getPhaseIconClass(phase.status)}>
                  {phase.status === 'complete' ? (
                    <CheckCircle className="w-4 h-4" />
                  ) : phase.status === 'active' ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    phase.icon
                  )}
                </div>
                <span className={`phase-label ${phase.status}`}>{phase.label}</span>
                {index < phases.length - 1 && (
                  <div className={`phase-connector ${phase.status === 'complete' ? 'complete' : ''}`} />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Status Messages */}
      {importStatus.status === 'success' && (
        <div className="status-message success">
          <div className="status-icon">
            <CheckCircle className="w-5 h-5" />
          </div>
          <div className="status-content">
            <p className="status-title">{importStatus.message}</p>
            <p className="status-detail">{importStatus.pagesImported} pages imported</p>
          </div>
        </div>
      )}

      {importStatus.status === 'error' && (
        <div className="status-message error">
          <div className="status-icon">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div className="status-content">
            <p className="status-title">Import Failed</p>
            <p className="status-detail">{importStatus.message}</p>
          </div>
        </div>
      )}

      {/* Tips */}
      <div className="import-tip">
        <p>
          <span className="tip-highlight">Tip:</span> Use zero-padded filenames (001.webp, 002.webp) for correct page order
        </p>
      </div>
    </div>
  );
};

export default MangaFolderImportSimple;
