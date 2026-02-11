# Manga Import Guide

This guide covers importing manga/comic volumes into The Loom.

## Supported Formats

### Image Files (Bulk Import)
- **.webp** - Modern efficient format
- **.png** - Lossless format
- **.jpg/.jpeg** - Compressed format

### Archive Files
- **.cbz** - Comic book ZIP archive
- **.zip** - Generic ZIP archive

## Import Methods

### Method 1: CLI Script (Recommended for Local Folders)

```bash
# Import a folder of webp images
python scripts/import_manga_folder.py "/path/to/manga/volume1" "My Manga Title"

# Dry run to preview what will be imported
python scripts/import_manga_folder.py "/path/to/manga/volume1" --dry-run
```

The script will:
1. Scan the folder for supported image files
2. Sort pages naturally by filename (handles `page_1.webp`, `page_2.webp`, etc.)
3. Import all pages as a single manga volume
4. Display a summary report

**Note:** Large volumes (500+ pages) may take several minutes to process due to OCR analysis.

### Method 2: React UI Components

For web application integration, use the provided React components:

#### Option A: Simple Folder Import (Recommended)

```tsx
import { MangaFolderImportSimple } from './components/MangaFolderImportSimple';

function ImportPage() {
  return (
    <MangaFolderImportSimple 
      onImportComplete={({ title, pages, hash }) => {
        console.log(`Imported ${pages} pages of "${title}"`);
        // Redirect to manga viewer, show success message, etc.
      }}
    />
  );
}
```

**Features:**
- Click to select folder (uses native folder picker)
- Drag & drop folder support
- Auto-extracts title from folder name
- Shows file count and preview
- Progress indication during upload

#### Option B: Full Drag & Drop Component

```tsx
import { MangaFolderImport } from './components/MangaFolderImport';

function ImportPage() {
  return (
    <MangaFolderImport 
      onImportComplete={(result) => {
        // Handle successful import
      }}
    />
  );
}
```

**Features:**
- Advanced drag & drop UI
- Visual feedback during drag operations
- File rejection handling
- Requires `react-dropzone` dependency

#### UI Component Props

Both components accept the same props:

| Prop | Type | Description |
|------|------|-------------|
| `onImportComplete` | `(result: {title, pages, hash}) => void` | Callback when import finishes |

#### Adding to Your App

1. Copy the component file to your project:
   ```bash
   cp ui/src/components/MangaFolderImportSimple.tsx your-app/components/
   ```

2. Ensure you have Lucide icons installed:
   ```bash
   npm install lucide-react
   ```

3. Import and use the component in your page.

### Method 3: API Endpoint

**POST /api/ingest/manga/pages**

Upload multiple image files directly:

```bash
# Upload webp pages via curl
curl -X POST "http://localhost:8000/api/ingest/manga/pages?title=My%20Manga" \
  -F "files=@page_001.webp" \
  -F "files=@page_002.webp" \
  -F "files=@page_003.webp"
```

Or use any HTTP client that supports multipart file uploads.

**Response:**
```json
{
  "success": true,
  "title": "My Manga",
  "pages_imported": 3,
  "pages": [
    {"page_number": 1, "format": "webp", "width": 1200, "height": 1800},
    {"page_number": 2, "format": "webp", "width": 1200, "height": 1800},
    {"page_number": 3, "format": "webp", "width": 1200, "height": 1800}
  ],
  "skipped_files": [],
  "warnings": [],
  "source_hash": "abc123..."
}
```

### Method 4: CBZ Upload

**POST /api/ingest/manga**

Upload a CBZ archive:

```bash
curl -X POST "http://localhost:8000/api/ingest/manga" \
  -F "file=@manga_volume.cbz"
```

## File Naming Best Practices

For best results, name your files with zero-padded numbers:

```
✅ Recommended:
  page_001.webp
  page_002.webp
  page_003.webp
  ...

✅ Also works:
  001.webp
  002.webp
  003.webp
  ...

✅ Works with chapter prefixes:
  ch01_p001.webp
  ch01_p002.webp
  ...

❌ Avoid (may sort incorrectly):
  page1.webp
  page2.webp
  page10.webp  # Would sort before page2!
```

## Large Volume Imports

For manga volumes with 500+ pages:

### CLI
- Extended timeout (5 minutes) is automatically applied
- Progress is shown during import
- OCR processing happens in the background

### UI
- Upload progress is shown
- Large imports may take several minutes
- UI remains responsive during upload

### API
- Same extended timeout applies
- Consider chunking if you hit timeouts with extremely large volumes

## Troubleshooting

### "No supported image files found"
- Check file extensions are lowercase (`.webp` not `.WEBP`)
- Verify files are in the specified folder
- Supported: `.webp`, `.png`, `.jpg`, `.jpeg`

### Pages in wrong order
- Use zero-padded numbers in filenames
- Ensure consistent naming pattern

### Import times out (CLI)
- The CLI now uses extended timeouts for large folders
- If it still times out, consider splitting into smaller volumes

### UI upload fails
- Check browser console for error details
- Verify backend is running at correct URL
- Large files may hit browser/sever limits

### Import fails with large folders
- Check `max_page_count` limit (default: 10,000 pages)
- Check individual file size (default: 100MB per file)

## Security Notes

- Files are validated for correct format signatures
- Size limits prevent resource exhaustion
- Temporary files are cleaned up after import
- Source hashing prevents duplicate imports

## Implementation Details

### Components Location
- `ui/src/components/MangaFolderImport.tsx` - Full drag & drop
- `ui/src/components/MangaFolderImportSimple.tsx` - Simple folder picker

### API Endpoint Location
- `ui/api.py` - `POST /api/ingest/manga/pages`

### Backend Processing
- `agents/archivist.py` - `ingest_image_folder_pages()` function
- Supports OCR text extraction from images
- Generates perceptual hashes for deduplication

## See Also

- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Archivist Agent](../agents/archivist.py) - Implementation details
