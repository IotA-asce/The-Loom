import React, { useState, useRef, ChangeEvent } from 'react';
import { Upload, FileImage, AlertCircle, CheckCircle, Loader2, FolderOpen, X, Image } from 'lucide-react';

interface ImportStatus {
  status: 'idle' | 'uploading' | 'success' | 'error';
  message?: string;
  pagesImported?: number;
  progress?: number;
}

interface MangaFolderImportSimpleProps {
  onImportComplete?: (result: { title: string; pages: number; hash: string }) => void;
}

export const MangaFolderImportSimple: React.FC<MangaFolderImportSimpleProps> = ({ 
  onImportComplete 
}) => {
  const [title, setTitle] = useState('');
  const [importStatus, setImportStatus] = useState<ImportStatus>({ status: 'idle' });
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

    const formData = new FormData();
    selectedFiles.forEach(file => formData.append('files', file));

    try {
      const xhr = new XMLHttpRequest();
      
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded / e.total) * 100);
          setUploadProgress(percent);
        }
      });

      const response = await new Promise<{ success: boolean; pages_imported: number; title: string; source_hash: string }>((resolve, reject) => {
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
        
        xhr.open('POST', `/api/ingest/manga/pages?title=${encodeURIComponent(title)}`);
        xhr.send(formData);
      });

      setImportStatus({
        status: 'success',
        pagesImported: response.pages_imported,
        message: `Successfully imported "${response.title}"`,
      });

      onImportComplete?.({
        title: response.title,
        pages: response.pages_imported,
        hash: response.source_hash,
      });

      setTimeout(() => {
        clearSelection();
        setImportStatus({ status: 'idle' });
      }, 3000);

    } catch (error) {
      setImportStatus({
        status: 'error',
        message: error instanceof Error ? error.message : 'Import failed',
      });
    }
  };

  const getDropzoneClass = () => {
    const baseClass = 'import-dropzone';
    if (importStatus.status === 'uploading') return `${baseClass} importing`;
    if (isDragging) return `${baseClass} active`;
    return baseClass;
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
          disabled={importStatus.status === 'uploading'}
          className="form-input"
        />
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        webkitdirectory=""
        directory=""
        multiple
        onChange={handleFileSelect}
        className="import-input"
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
          
          {importStatus.status === 'uploading' ? (
            <div className="import-loading">
              <div className="spinner" />
              <div className="upload-progress">
                <p className="upload-text">Uploading...</p>
                <div className="progress-bar-container">
                  <div 
                    className="progress-bar"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="progress-percent">{uploadProgress}%</p>
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
            {importStatus.status !== 'uploading' && (
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
          disabled={importStatus.status === 'uploading'}
          className="import-btn"
        >
          {importStatus.status === 'uploading' ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Importing... {uploadProgress > 0 && `${uploadProgress}%`}
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" />
              Import {selectedFiles.length} Pages
            </>
          )}
        </button>
      )}

      {/* Upload Progress */}
      {importStatus.status === 'uploading' && (
        <div className="upload-status-panel">
          <div className="upload-status-header">
            <span>Uploading {selectedFiles.length} pages...</span>
            <span className="upload-percent">{uploadProgress}%</span>
          </div>
          <div className="progress-bar-container">
            <div 
              className="progress-bar"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <p className="upload-note">
            Processing OCR and generating thumbnails...
          </p>
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
