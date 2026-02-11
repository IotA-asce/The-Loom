import React, { useCallback, useState } from 'react';
import { Upload, FileImage, AlertCircle, CheckCircle } from 'lucide-react';
import { useDropzone } from 'react-dropzone';

interface ImportStatus {
  status: 'idle' | 'uploading' | 'success' | 'error';
  message?: string;
  pagesImported?: number;
  errors?: string[];
}

interface MangaFolderImportProps {
  onImportComplete?: (result: { title: string; pages: number; hash: string }) => void;
}

export const MangaFolderImport: React.FC<MangaFolderImportProps> = ({ onImportComplete }) => {
  const [title, setTitle] = useState('');
  const [importStatus, setImportStatus] = useState<ImportStatus>({ status: 'idle' });
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    // Filter for supported image formats
    const supportedFiles = acceptedFiles.filter(file => {
      const ext = file.name.toLowerCase().split('.').pop();
      return ['webp', 'png', 'jpg', 'jpeg'].includes(ext || '');
    });

    // Sort files naturally by name
    supportedFiles.sort((a, b) => {
      const aNum = a.name.match(/\d+/)?.[0] || '0';
      const bNum = b.name.match(/\d+/)?.[0] || '0';
      return parseInt(aNum) - parseInt(bNum);
    });

    setSelectedFiles(supportedFiles);
    
    // Auto-extract title from folder if not set
    if (!title && supportedFiles.length > 0) {
      const pathParts = supportedFiles[0].webkitRelativePath?.split('/') || [];
      if (pathParts.length > 1) {
        setTitle(pathParts[pathParts.length - 2]);
      }
    }
  }, [title]);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: {
      'image/webp': ['.webp'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
    },
    // @ts-ignore - webkitdirectory is a valid attribute for folder selection
    webkitdirectory: '',
    directory: '',
  });

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
    <div className="space-y-4 p-4 bg-white rounded-lg shadow">
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

      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        {isDragActive ? (
          <p className="text-blue-600 font-medium">Drop the files here...</p>
        ) : (
          <div>
            <p className="text-gray-600 font-medium">
              Drag & drop manga folder here, or click to select
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Supports: .webp, .png, .jpg, .jpeg
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
            {selectedFiles.slice(0, 10).map((file, i) => (
              <div key={i} className="truncate">{file.name}</div>
            ))}
            {selectedFiles.length > 10 && (
              <div className="text-gray-400">
                ... and {selectedFiles.length - 10} more
              </div>
            )}
          </div>
        </div>
      )}

      {/* File Rejections */}
      {fileRejections.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
          <div className="flex items-center gap-2 text-yellow-700">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm font-medium">
              {fileRejections.length} unsupported files skipped
            </span>
          </div>
        </div>
      )}

      {/* Import Button */}
      <button
        onClick={handleImport}
        disabled={importStatus.status === 'uploading' || selectedFiles.length === 0}
        className={`w-full py-2 px-4 rounded-md font-medium transition-colors ${
          importStatus.status === 'uploading'
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 text-white'
        }`}
      >
        {importStatus.status === 'uploading'
          ? 'Importing...'
          : `Import ${selectedFiles.length > 0 ? `${selectedFiles.length} pages` : 'Pages'}`}
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
    </div>
  );
};

export default MangaFolderImport;
