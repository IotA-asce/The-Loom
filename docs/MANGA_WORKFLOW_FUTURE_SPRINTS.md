# 🗺️ Manga Workflow - Future Sprints

> This document tracks identified gaps and future enhancements for the manga workflow.
> 
> **Last Audit Date:** 2025-02-11  
> **Current Status:** Core workflow complete and functional

---

## ✅ Completed (Sprints 1-3)

| Sprint | Feature | Status |
|--------|---------|--------|
| Sprint 1 | Data Model Alignment (node_type field) | ✅ Complete |
| Sprint 2 | Association & Linking (volume↔node) | ✅ Complete |
| Sprint 3 | Manga Viewer (image serving, navigation) | ✅ Complete |

**Core Workflow Works End-to-End:**
```
CLI Import → Storage → Graph Node → Library List → Viewer → Read Pages
```

---

## 📋 Gap Analysis

### Gap 1: Optional Dependencies for UI Import Components

| | Details |
|--|---------|
| **Severity** | 🟡 Low (CLI import works perfectly) |
| **Status** | Components exist, dependencies missing |
| **Impact** | Cannot import manga via web UI drag-and-drop |
| **Workaround** | Use CLI import (recommended anyway for large volumes) |

**Problem:**
- `MangaFolderImport.tsx` requires `react-dropzone`
- `MangaFolderImportSimple.tsx` requires `lucide-react`
- Neither dependency is in `package.json`

**Solution:**
```bash
cd ui
npm install lucide-react react-dropzone
```

Then integrate into `ImportPanel.tsx`:
```tsx
import { MangaFolderImportSimple } from './MangaFolderImportSimple'

// Add to ImportPanel render:
<MangaFolderImportSimple 
  onImportComplete={() => fetchMangaVolumes()}
/>
```

**Effort:** 1-2 hours

---

### Gap 2: Reading Progress Tracking

| | Details |
|--|---------|
| **Severity** | 🟢 Nice to have |
| **Status** | Not implemented |
| **Impact** | Cannot resume reading from last page |
| **Workaround** | Note page number manually, use page input in viewer |

**Feature Description:**
- Track last read page for each manga volume
- Show progress bar in library (% complete)
- "Resume" button to jump to last page
- Persist progress in localStorage or backend

**Implementation:**
```typescript
// Add to store
interface ReadingProgress {
  volumeId: string
  lastPage: number
  totalPages: number
  lastReadAt: string
}

// Actions
updateReadingProgress(volumeId: string, page: number)
getReadingProgress(volumeId: string): ReadingProgress
```

**Effort:** 4-6 hours

---

### Gap 3: Thumbnail Generation

| | Details |
|--|---------|
| **Severity** | 🟡 Medium (performance) |
| **Status** | Not implemented - uses full images |
| **Impact** | Slower thumbnail loading in viewer sidebar |
| **Workaround** | Current implementation works, just slower |

**Feature Description:**
- Generate small thumbnail versions during import
- Store alongside original images
- Use thumbnails in viewer sidebar for faster loading
- Generate on-demand if missing

**Implementation:**
```python
# In archivist.py or new module
from PIL import Image

def generate_thumbnail(image_path: Path, size: tuple[int, int] = (150, 200)) -> Path:
    """Generate thumbnail for a page."""
    thumb_path = image_path.parent / ".thumbs" / f"{image_path.stem}_thumb.webp"
    thumb_path.parent.mkdir(exist_ok=True)
    
    with Image.open(image_path) as img:
        img.thumbnail(size)
        img.save(thumb_path, "WEBP", quality=80)
    
    return thumb_path
```

**Effort:** 6-8 hours

---

### Gap 4: CBZ Import via UI

| | Details |
|--|---------|
| **Severity** | 🟡 Medium |
| **Status** | API exists, UI integration incomplete |
| **Impact** | Must use CLI for CBZ files |
| **Workaround** | Extract CBZ to folder, then import folder |

**Current State:**
- API endpoint `POST /api/ingest/manga` accepts CBZ files
- `ImportPanel.tsx` handles drag-and-drop but only for single files
- CBZ import not explicitly supported in UI

**Solution:**
Extend `ImportPanel.tsx` to:
1. Detect CBZ file type
2. Use correct endpoint (`/api/ingest/manga` not `/api/ingest/text`)
3. Show progress for large CBZ files

**Effort:** 2-3 hours

---

### Gap 5: Manga Search

| | Details |
|--|---------|
| **Severity** | 🟢 Nice to have |
| **Status** | OCR text stored, not searchable |
| **Impact** | Cannot search content of imported manga |
| **Workaround** | None (not critical for most use cases) |

**Feature Description:**
- Index OCR text from manga pages
- Include manga in semantic search results
- Show page previews in search results
- Search across manga library

**Implementation:**
```python
# Index OCR text during import
for page in report.page_metadata:
    if page.ocr_text:
        vector_store.add_document(
            content=page.ocr_text,
            metadata={
                "type": "manga_page",
                "volume_id": volume_id,
                "page_number": page.page_number,
                "source": "ocr"
            }
        )
```

**Effort:** 8-12 hours

---

### Gap 6: Batch Operations

| | Details |
|--|---------|
| **Severity** | 🟢 Nice to have |
| **Status** | Not implemented |
| **Impact** | Must delete volumes one at a time |
| **Workaround** | Current single-item operations work fine |

**Feature Description:**
- Multi-select volumes in library
- Batch delete selected
- Batch export (create CBZ from stored metadata)

**Effort:** 4-6 hours

---

### Gap 7: Reading History & Stats

| | Details |
|--|---------|
| **Severity** | 🟢 Nice to have |
| **Status** | Not implemented |
| **Impact** | No reading analytics |
| **Workaround** | None needed |

**Feature Description:**
- Track which volumes you've read
- Reading time estimation
- "Recently read" section
- Reading streaks/goals

**Effort:** 6-8 hours

---

### Gap 8: Mobile Viewer Optimization

| | Details |
|--|---------|
| **Severity** | 🟡 Medium |
| **Status** | Viewer works but not optimized |
| **Impact** | Mobile experience could be better |
| **Workaround** | Current viewer works on mobile |

**Improvements:**
- Swipe gestures for page navigation
- Bottom sheet for thumbnails
- Improved touch targets
- Mobile-specific layout

**Effort:** 8-12 hours

---

### Gap 9: Manga Metadata Editing

| | Details |
|--|---------|
| **Severity** | 🟢 Nice to have |
| **Status** | Title fixed at import, not editable |
| **Impact** | Cannot fix typos or update metadata |
| **Workaround** | Delete and re-import with correct info |

**Feature Description:**
- Edit manga title after import
- Add tags/categories
- Mark as "reading", "completed", "on hold"
- Add personal notes

**Effort:** 4-6 hours

---

### Gap 10: Double-Click to Open Viewer from Graph

| | Details |
|--|---------|
| **Severity** | 🟡 Medium |
| **Status** | Not implemented |
| **Impact** | Must use metadata panel button |
| **Workaround** | Click node → Click "View Manga" button |

**Implementation:**
```tsx
// In GraphCanvas.tsx node double-click handler
if (node.type === 'manga') {
  const volumeId = node.metadata?.volume_id
  if (volumeId) {
    openMangaViewer(volumeId)
  }
}
```

**Effort:** 1 hour

---

## 🎯 Priority Recommendations

### Immediate (This Week)
1. **Gap 10** - Double-click to open viewer (1 hour, high UX impact)
2. **Gap 1** - Install optional dependencies (1-2 hours)

### Short Term (Next 2 Weeks)
3. **Gap 4** - CBZ import via UI (2-3 hours)
4. **Gap 2** - Reading progress tracking (4-6 hours)
5. **Gap 3** - Thumbnail generation (6-8 hours, performance)

### Medium Term (Next Month)
6. **Gap 8** - Mobile optimization (8-12 hours)
7. **Gap 9** - Metadata editing (4-6 hours)
8. **Gap 6** - Batch operations (4-6 hours)

### Future (Nice to Have)
9. **Gap 5** - Manga search (8-12 hours)
10. **Gap 7** - Reading history & stats (6-8 hours)

---

## 📊 Effort Summary

| Priority | Total Effort | Features |
|----------|--------------|----------|
| Immediate | 1-3 hours | 2 features |
| Short Term | 12-19 hours | 3 features |
| Medium Term | 16-26 hours | 3 features |
| Future | 14-20 hours | 2 features |
| **Grand Total** | **43-68 hours** | **10 features** |

---

## 🏁 Conclusion

The manga workflow is **production-ready** for the core use case:
- ✅ Import via CLI
- ✅ View in app
- ✅ Navigate pages
- ✅ Link to story graph

The identified gaps are enhancements that improve UX but don't block basic functionality. The CLI import method is actually preferred for large collections as it's more reliable for bulk operations.

**Recommended Next Action:** Implement Gap 10 (double-click to open) for immediate UX improvement.

---

*Document generated from comprehensive workflow audit*
