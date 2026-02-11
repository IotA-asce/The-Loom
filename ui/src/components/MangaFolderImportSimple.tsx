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

  const getStatusColor = () => {
    switch (importStatus.status) {
      case 'success': return 'border-green-500 bg-green-50';
      case 'error': return 'border-red-500 bg-red-50';
      case 'uploading': return 'border-blue-500 bg-blue-50';
      default: return isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400';
    }
  };

  return (
    <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 shadow-xl">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center">
          <FileImage className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Import Manga</h3>
          <p className="text-sm text-slate-400">Import a folder of manga images</p>
        </div>
      </div>

      {/* Title Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Manga Title
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g., Dragon Ball Volume 1"
          disabled={importStatus.status === 'uploading'}
          className="w-full px-4 py-2.5 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-pink-500 focus:border-transparent transition-all disabled:opacity-50"
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
        className="hidden"
      />

      {/* Drop Zone */}
      {!selectedFiles.length ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${getStatusColor()}`}
        >
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-800 flex items-center justify-center">
            {importStatus.status === 'uploading' ? (
              <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            ) : (
              <FolderOpen className="w-8 h-8 text-slate-400" />
            )}
          </div>
          
          {importStatus.status === 'uploading' ? (
            <div className="space-y-2">
              <p className="text-blue-400 font-medium">Uploading...</p>
              <div className="w-full max-w-xs mx-auto bg-slate-700 rounded-full h-2 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-pink-500 to-purple-500 transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-sm text-slate-400">{uploadProgress}%</p>
            </div>
          ) : isDragging ? (
            <p className="text-blue-400 font-medium text-lg">Drop folder here!</p>
          ) : (
            <>
              <p className="text-white font-medium text-lg mb-1">
                Click to select folder
              </p>
              <p className="text-slate-400 text-sm">
                or drag & drop here
              </p>
            </>
          )}
          
          <div className="mt-4 flex items-center justify-center gap-4 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <Image className="w-3 h-3" /> .webp
            </span>
            <span className="flex items-center gap-1">
              <Image className="w-3 h-3" /> .png
            </span>
            <span className="flex items-center gap-1">
              <Image className="w-3 h-3" /> .jpg
            </span>
          </div>
        </div>
      ) : (
        /* Selected Files Preview */
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span className="text-white font-medium">
                {selectedFiles.length} pages selected
              </span>
            </div>
            {importStatus.status !== 'uploading' && (
              <button
                onClick={clearSelection}
                className="p-1 hover:bg-slate-700 rounded-full transition-colors"
              >
                <X className="w-4 h-4 text-slate-400" />
              </button>
            )}
          </div>

          {/* File stats */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="bg-slate-900 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-white">{selectedFiles.length}</p>
              <p className="text-xs text-slate-400">Pages</p>
            </div>
            <div className="bg-slate-900 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-pink-500">{formatFileSize(totalSize)}</p>
              <p className="text-xs text-slate-400">Total Size</p>
            </div>
            <div className="bg-slate-900 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-purple-500">
                {selectedFiles[0]?.name.split('.').pop()?.toUpperCase() || 'IMG'}
              </p>
              <p className="text-xs text-slate-400">Format</p>
            </div>
          </div>

          {/* File list */}
          <div className="max-h-32 overflow-y-auto space-y-1 bg-slate-900 rounded-lg p-2">
            {selectedFiles.slice(0, 10).map((file, i) => (
              <div key={i} className="flex items-center justify-between text-sm py-1 px-2 rounded hover:bg-slate-800">
                <span className="text-slate-300 truncate flex-1">{file.name}</span>
                <span className="text-slate-500 text-xs ml-2">{formatFileSize(file.size)}</span>
              </div>
            ))}
            {selectedFiles.length > 10 && (
              <p className="text-center text-slate-500 text-sm py-1">
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
          className="w-full mt-4 py-3 px-4 rounded-xl font-semibold transition-all flex items-center justify-center gap-2 bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-500 hover:to-purple-500 text-white shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
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

      {/* Upload Progress Bar */}
      {importStatus.status === 'uploading' && (
        <div className="mt-4 bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-300">Uploading {selectedFiles.length} pages...</span>
            <span className="text-sm font-medium text-pink-500">{uploadProgress}%</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-2.5 overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-pink-500 to-purple-500 transition-all duration-300 rounded-full"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Processing OCR and generating thumbnails...
          </p>
        </div>
      )}

      {/* Status Messages */}
      {importStatus.status === 'success' && (
        <div className="mt-4 flex items-center gap-3 p-4 bg-green-500/10 border border-green-500/30 rounded-xl">
          <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center">
            <CheckCircle className="w-5 h-5 text-green-500" />
          </div>
          <div>
            <p className="text-green-400 font-medium">{importStatus.message}</p>
            <p className="text-sm text-green-500/70">{importStatus.pagesImported} pages imported</p>
          </div>
        </div>
      )}

      {importStatus.status === 'error' && (
        <div className="mt-4 flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-xl">
          <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
            <AlertCircle className="w-5 h-5 text-red-500" />
          </div>
          <div className="flex-1">
            <p className="text-red-400 font-medium">Import Failed</p>
            <p className="text-sm text-red-500/70">{importStatus.message}</p>
          </div>
        </div>
      )}

      {/* Tips */}
      <div className="mt-4 p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
        <p className="text-xs text-slate-400">
          <span className="text-pink-400 font-medium">Tip:</span> Use zero-padded filenames (001.webp, 002.webp) for correct page order
        </p>
      </div>
    </div>
  );
};

export default MangaFolderImportSimple;
