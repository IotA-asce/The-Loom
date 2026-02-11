import React, { useState, useRef, ChangeEvent } from 'react';
import { Upload, FileImage, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

interface ImportStatus {
  status: 'idle' | 'uploading' | 'success' | 'error';
  message?: string;
  pagesImported?: number;
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
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    processFiles(Array.from(files));
  };

  const processFiles = (files: File[]) => {
    // Filter for supported image formats
    const supportedFiles = files.filter(file => {
      const ext = file.name.toLowerCase().split('.').pop();
      return ['webp', 'png', 'jpg', 'jpeg'].includes(ext || '');
    });

    // Sort files naturally by name
    supportedFiles.sort((a, b) => {
      const aMatch = a.name.match(/(\d+)/);
      const bMatch = b.name.match(/(\d+)/);
      const aNum = aMatch ? parseInt(aMatch[1]) : 0;
      const bNum = bMatch ? parseInt(bMatch[1]) : 0;
      return aNum - bNum;
    });

    setSelectedFiles(supportedFiles);

    // Auto-extract title from folder if not set
    if (!title && supportedFiles.length > 0) {
      const pathParts = supportedFiles[0].webkitRelativePath?.split('/') || [];
      if (pathParts.length > 1) {
        setTitle(pathParts[pathParts.length - 2]);
      }
    }
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

    // Collect all files from dropped items
    const collectFiles = (item: DataTransferItem, path = '') => {
      if (item.kind === 'file') {
        const entry = item.webkitGetAsEntry?.();
        if (entry) {
          traverseFileTree(entry, files);
        }
      }
    };

    for (let i = 0; i < items.length; i++) {
      collectFiles(items[i]);
    }

    // Wait a bit for files to be collected
    setTimeout(() => {
      processFiles(files);
    }, 100);
  };

  const traverseFileTree = (item: any, files: File[]) => {
    if (item.isFile) {
      item.file((file: File) => {
        files.push(file);
      });
    } else if (item.isDirectory) {
      const dirReader = item.createReader();
      dirReader.readEntries((entries: any[]) => {
        entries.forEach(entry => traverseFileTree(entry, files));
      });
    }
  };

  const handleImport = async () => {
    if (selectedFiles.length === 0) {
      setImportStatus({ status: 'error', message: 'No files selected' });
      return;
    }

    if (!title.trim()) {
      setImportStatus({ status: 'error', message: 'Please enter a title' });
      return;
    }

    setImportStatus({ status: 'uploading' });

    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await fetch(
        `/api/ingest/manga/pages?title=${encodeURIComponent(title)}`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Import failed');
      }

      const result = await response.json();

      setImportStatus({
        status: 'success',
        pagesImported: result.pages_imported,
        message: `Successfully imported ${result.pages_imported} pages`,
      });

      onImportComplete?.({
        title: result.title,
        pages: result.pages_imported,
        hash: result.source_hash,
      });

      // Reset after success
      setTimeout(() => {
        setSelectedFiles([]);
        setTitle('');
        setImportStatus({ status: 'idle' });
      }, 3000);

    } catch (error) {
      setImportStatus({
        status: 'error',
        message: error instanceof Error ? error.message : 'Import failed',
      });
    }
  };

  return (
    <div className="space-y-4 p-4 bg-white rounded-lg shadow max-w-md">
      <h3 className="text-lg font-semibold flex items-center gap-2">
        <FileImage className="w-5 h-5" />
        Import Manga Folder
      </h3>

      {/* Title Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Manga Title
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Enter manga title"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Hidden file input with webkitdirectory */}
      <input
        ref={fileInputRef}
        type="file"
        // @ts-ignore
        webkitdirectory=""
        directory=""
        multiple
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Drop Zone / Click Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        {isDragging ? (
          <p className="text-blue-600 font-medium">Drop the folder here...</p>
        ) : (
          <div>
            <p className="text-gray-600 font-medium">
              Click to select manga folder
            </p>
            <p className="text-sm text-gray-500 mt-2">
              or drag & drop folder here
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Supports: .webp, .png, .jpg
            </p>
          </div>
        )}
      </div>

      {/* File List */}
      {selectedFiles.length > 0 && (
        <div className="bg-gray-50 rounded-md p-3">
          <p className="text-sm font-medium text-gray-700 mb-2">
            Selected: {selectedFiles.length} pages
          </p>
          <div className="max-h-32 overflow-y-auto text-xs text-gray-600 space-y-1">
            {selectedFiles.slice(0, 5).map((file, i) => (
              <div key={i} className="truncate">{file.name}</div>
            ))}
            {selectedFiles.length > 5 && (
              <div className="text-gray-400">
                ... and {selectedFiles.length - 5} more
              </div>
            )}
          </div>
        </div>
      )}

      {/* Import Button */}
      <button
        onClick={handleImport}
        disabled={importStatus.status === 'uploading' || selectedFiles.length === 0}
        className={`w-full py-2 px-4 rounded-md font-medium transition-colors flex items-center justify-center gap-2 ${
          importStatus.status === 'uploading'
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 text-white'
        }`}
      >
        {importStatus.status === 'uploading' ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Importing... ({selectedFiles.length} pages)
          </>
        ) : (
          <>
            <Upload className="w-4 h-4" />
            Import {selectedFiles.length > 0 ? `${selectedFiles.length} pages` : 'Pages'}
          </>
        )}
      </button>

      {/* Status Messages */}
      {importStatus.status === 'success' && (
        <div className="flex items-center gap-2 text-green-600 bg-green-50 p-3 rounded-md">
          <CheckCircle className="w-5 h-5" />
          <span>{importStatus.message}</span>
        </div>
      )}

      {importStatus.status === 'error' && (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-md">
          <AlertCircle className="w-5 h-5" />
          <span>{importStatus.message}</span>
        </div>
      )}

      {/* Note */}
      <p className="text-xs text-gray-500 text-center">
        Large volumes (500+ pages) may take a few minutes to process.
      </p>
    </div>
  );
};

export default MangaFolderImportSimple;
