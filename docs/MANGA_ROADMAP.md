# 🗺️ Manga Workflow - Roadmap

> This document tracks the manga feature roadmap and future enhancements.
> 
> **Last Updated:** 2025-02-11  
> **Current Status:** ✅ Core workflow complete and functional

---

## ✅ Completed Features

### Core Import & Reading
| Feature | Status |
|---------|--------|
| Story Extraction (scenes from OCR) | ✅ Complete |
| Data Model Alignment (node_type field) | ✅ Complete |
| Association & Linking (volume↔node) | ✅ Complete |
| Manga Viewer (image serving, navigation) | ✅ Complete |
| UI Folder Import (no terminal needed) | ✅ Complete |
| CBZ Import via drag & drop | ✅ Complete |
| Reading Progress Tracking | ✅ Complete |
| Resume from Last Page | ✅ Complete |
| Mobile Swipe Gestures | ✅ Complete |
| Thumbnail Generation | ✅ Complete |
| Metadata Editing (titles) | ✅ Complete |
| Batch Operations | ✅ Complete |
| Double-click to Open from Graph | ✅ Complete |

### User Experience
- ✅ Progress bars in library
- ✅ Resume button (▶️) for continued reading
- ✅ Tap-to-toggle controls on mobile
- ✅ Batch selection with checkboxes
- ✅ Inline title editing

---

## 🚧 Future Enhancements

These features are planned but not yet implemented:

### 1. Manga Search (OCR Index)
**Priority:** 🟢 Low  
**Effort:** 8-12 hours

Index OCR text from manga pages for searching:
- Search across manga volumes
- Show search results with page previews
- Find text within specific volumes

### 2. Reading History & Stats
**Priority:** 🟢 Low  
**Effort:** 6-8 hours

Track reading habits:
- "Recently read" section
- Reading time estimation
- Reading streaks/goals
- Volume completion stats

### 3. Advanced Metadata
**Priority:** 🟢 Low  
**Effort:** 4-6 hours

Enhanced metadata support:
- Tags/categories for manga
- Author/artist fields
- Reading status (reading, completed, on-hold)
- Personal notes/ratings
- Custom cover images

### 4. Export Features
**Priority:** 🟡 Medium  
**Effort:** 6-8 hours

Export manga for sharing:
- Generate CBZ from imported manga
- Export reading progress
- Backup/restore manga database

### 5. Performance Optimizations
**Priority:** 🟡 Medium  
**Effort:** 8-12 hours

For large libraries (1000+ volumes):
- Pagination in manga library
- Virtual scrolling for thumbnails
- Background thumbnail pre-generation

---

## 📊 Summary

| Category | Count |
|----------|-------|
| ✅ Completed | 17 features |
| 🚧 Planned | 5 enhancements |
| **Total Effort Remaining** | **28-40 hours** |

---

## 🎯 Success Metrics (Achieved)

- [x] Import manga via UI → see in library
- [x] Import manga via CLI → see in graph
- [x] Click manga in library → view pages
- [x] Double-click manga node → view pages
- [x] Navigate pages smoothly
- [x] Resume reading from last page
- [x] Batch manage volumes
- [x] Mobile-friendly viewer
- [x] Story extraction scaffolding

---

## 🔮 Story Extraction Enhancements

Planned improvements to the story extraction feature:

### Scene Segmentation AI
**Priority:** 🟡 Medium  
**Effort:** 4-6 hours

Implement AI-powered scene detection:
- Send OCR text to LLM for scene boundaries
- Create scene nodes linked to manga volume
- Identify characters, dialogue, mood/tone

### Character Extraction
**Priority:** 🟢 Low  
**Effort:** 3-4 hours

Extract characters as separate graph nodes:
- Detect character names from dialogue
- Create character entity nodes
- Link characters to scenes they appear in

### Interactive Scene Editor
**Priority:** 🟢 Low  
**Effort:** 6-8 hours

Edit extracted scenes in the graph:
- Merge/split scenes
- Add branching choices
- Modify dialogue and descriptions

---

*For user documentation, see [MANGA_WORKFLOW_COMPLETE.md](MANGA_WORKFLOW_COMPLETE.md)*
