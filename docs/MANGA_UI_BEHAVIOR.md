# Manga Import UI Behavior

This document describes what you should see in the UI after importing manga via CLI.

## Overview

After running the CLI import command:
```bash
python scripts/import_manga_folder.py "/path/to/manga" "Title"
```

The following happens:
1. ✅ Images are processed (OCR, hashing)
2. ✅ Manga is saved to `.loom/manga.db`
3. ✅ A graph node is created in `.loom/graph.db`
4. ✅ UI can display the manga in the Import tab

## What You Should See

### 1. In the Import Tab (Left Sidebar)

Click the **📥 Import** tab in the left sidebar. You should see:

```
┌─────────────────────────────┐
│ 📥 Import                   │
├─────────────────────────────┤
│ [Drop files here...]        │
│                             │
│ Supported Formats           │
│ • Text: .txt, .pdf, .epub   │
│ • Manga: .cbz, .zip         │
│ • Images: .png, .jpg...     │
├─────────────────────────────┤
│ 📚 Imported Manga      🔄   │
├─────────────────────────────┤
│ 📖 Title                    │
│    529 pages • Imported     │
│    2/10/2025, 10:30:00 AM   │
│    📝 In graph          🗑️  │
├─────────────────────────────┤
│ 1 volume                    │
└─────────────────────────────┘
```

**Key elements:**
- **📚 Imported Manga** section shows all imported manga
- Each manga displays:
  - Title (e.g., "Boindo")
  - Page count (e.g., "529 pages")
  - Import timestamp
  - 📝 **In graph** badge (if graph node was created)
  - 🗑️ Delete button

### 2. In the Graph Canvas

**Current limitation:** The manga node is created in the database but the UI doesn't automatically load existing nodes on startup. 

To see the manga in the graph, you would need to either:
- Reload/refresh the page after implementing a "load existing nodes" feature
- Or manually create a node with the same metadata

When visible, the manga node will appear as:
- **Icon:** 📖
- **Color:** Pink (#e91e63)
- **Shape:** Book-shaped
- **Label:** The manga title

## Troubleshooting

### "No manga imported yet" message

If you see this in the Import tab after importing:

1. **Check the backend is running:**
   ```bash
   curl http://localhost:8000/api/manga
   ```
   Should return: `{"success": true, "volumes": [...]}`

2. **Check the database exists:**
   ```bash
   ls -la .loom/
   # Should show: manga.db, graph.db
   ```

3. **Re-import with verbose output:**
   ```bash
   python scripts/import_manga_folder.py "/path/to/manga" "Title"
   # Look for: "✅ Saved manga volume" and "✅ Created graph node"
   ```

### Manga appears in list but not in graph

This is expected current behavior. The graph node is created in the database but the UI doesn't load existing nodes on startup. The manga metadata includes:
```json
{
  "type": "manga",
  "volume_id": "manga_...",
  "page_count": 529,
  "source_hash": "..."
}
```

## API Endpoints

The following endpoints are available:

```bash
# List all manga
GET /api/manga

# Get specific manga
GET /api/manga/{volume_id}

# Delete manga
DELETE /api/manga/{volume_id}
```

## File Locations

| File | Location | Purpose |
|------|----------|---------|
| Manga DB | `.loom/manga.db` | Stores manga volumes and pages |
| Graph DB | `.loom/graph.db` | Stores graph nodes including manga nodes |
| Images | Original location | Not moved, only referenced |

## Future Improvements

1. **Auto-load nodes:** On startup, load existing graph nodes from the database
2. **Manga viewer:** Click a manga in the library to view pages
3. **Graph integration:** Double-click manga node to open viewer
4. **Search:** Include manga content in semantic search
