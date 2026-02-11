# Manga Import Workflow - Sprint Plan

> Comprehensive analysis of disconnects and missing features in the manga import workflow, organized into actionable sprints.

---

## Executive Summary

The manga import workflow has **critical disconnects** between backend data models and frontend expectations, plus **missing UI components** for viewing manga. This plan organizes fixes into 4 sprints.

| Metric | Count |
|--------|-------|
| 🔴 Critical Issues | 3 |
| 🟠 High Priority | 4 |
| 🟡 Medium Priority | 5 |
| 🟢 Low Priority | 3 |
| **Total Items** | **15** |

---

## Current State Analysis

### Data Flow Diagram

```
CLI Import → Process Images → Save to manga.db → Create graph node → UI Display
     │              │                │                  │              │
     ▼              ▼                ▼                  ▼              ▼
  Scans       OCR/Hashing       Volume + Pages    metadata.type    List only
  folder      (archivist)       (manga_storage)   (graph.db)       (no viewer)
```

### Critical Issues Found

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 1 | Backend GraphNode has no `type` field | `core/graph_persistence.py` | Type stored in metadata (fragile) |
| 2 | Frontend expects `type` as top-level | `ui/src/store.ts` | Mismatch causes type detection issues |
| 3 | NodeType defined in multiple places | `store.ts`, `graphStore.ts` | Inconsistency, 'manga' missing in one |
| 4 | No manga viewer component | UI | Cannot view imported pages |
| 5 | No image serving endpoint | `ui/api.py` | Cannot display page images |
| 6 | CLI doesn't update `graph_node_id` | `scripts/import_manga_folder.py` | Broken volume-node association |
| 7 | UI import doesn't create graph node | `MangaFolderImport*.tsx` | UI imports invisible in graph |
| 8 | No navigation between volume and node | UI | Disconnected user experience |

---

## Sprint 1: Data Model Alignment 🔧

**Duration:** 3-4 days  
**Goal:** Fix backend/frontend data model disconnects

### 1.1 Add `node_type` to Backend GraphNode
**Priority:** 🔴 Critical

```python
# core/graph_persistence.py
@dataclass(frozen=True)
class GraphNode:
    node_id: str
    label: str
    branch_id: str
    scene_id: str
    x: float
    y: float
    importance: float
    node_type: str  # NEW FIELD
    metadata: dict[str, Any]
```

Tasks:
- [ ] Add `node_type` field to GraphNode dataclass
- [ ] Update `to_dict()` and `from_dict()` methods
- [ ] Update SQLite schema in `_ensure_db()`
- [ ] Create migration for existing nodes
- [ ] Backfill `node_type` from `metadata.type`

**Acceptance:** All nodes have explicit `node_type` field

---

### 1.2 Unify NodeType Definitions
**Priority:** 🔴 Critical

Tasks:
- [ ] Create shared types file: `ui/src/types/common.ts`
- [ ] Move `NodeType` definition there
- [ ] Update `store.ts` to import from common
- [ ] Update `graphStore.ts` to import from common
- [ ] Ensure 'manga' is in all type unions

**Acceptance:** Single source of truth, no TypeScript errors

---

### 1.3 Update API for Explicit Type
**Priority:** 🟠 High

Tasks:
- [ ] Update `GraphNodeCreate` Pydantic model
- [ ] Update `save_graph_node()` endpoint
- [ ] Update all node response schemas

**Acceptance:** API accepts/returns `node_type` consistently

---

### 1.4 Update Frontend Node Loading
**Priority:** 🟠 High

Tasks:
- [ ] Update `loadGraphNodes()` to use `node.node_type`
- [ ] Add fallback to `metadata.type` for backward compat

**Acceptance:** Nodes load with correct type from backend

---

## Sprint 2: Association & Linking 🔗

**Duration:** 2-3 days  
**Goal:** Fix broken volume-node associations

### 2.1 CLI Import - Update Volume with Graph Node ID
**Priority:** 🟠 High

Tasks:
- [ ] After creating graph node, get `node_id`
- [ ] Update volume with `graph_node_id`
- [ ] Save updated volume to storage

**Acceptance:** Imported volumes show "📝 In graph" badge

---

### 2.2 UI Import - Create Graph Node
**Priority:** 🟠 High

Tasks:
- [ ] Add `create_graph_node` param to API endpoint
- [ ] Create graph node after saving volume
- [ ] Update UI to pass `create_graph_node=true`

**Acceptance:** UI-imported manga appears in graph

---

### 2.3 Add Volume-to-Node Navigation
**Priority:** 🟡 Medium

Tasks:
- [ ] Add "Go to Node" button in MangaLibrary
- [ ] Implement node selection/navigation
- [ ] Highlight node in graph

**Acceptance:** Can click from library to graph node

---

### 2.4 Add Node-to-Volume Navigation
**Priority:** 🟡 Medium

Tasks:
- [ ] Show "View Manga" button for manga nodes
- [ ] Button opens manga viewer

**Acceptance:** Can click from node to manga viewer

---

## Sprint 3: Manga Viewer 🖼️

**Duration:** 5-7 days  
**Goal:** Build complete viewing experience

### 3.1 Image Serving API
**Priority:** 🔴 Critical

```python
@app.get("/api/manga/{volume_id}/pages/{page_number}/image")
async def get_manga_page_image(volume_id: str, page_number: int):
    # Serve actual image file
```

Tasks:
- [ ] Add endpoint to serve page images
- [ ] Handle format conversion
- [ ] Add caching headers
- [ ] Error handling for missing images

**Acceptance:** Can retrieve page images via API

---

### 3.2 MangaViewer Component
**Priority:** 🔴 Critical

Features:
- [ ] Display current page
- [ ] Previous/next navigation
- [ ] Page counter
- [ ] Thumbnail sidebar
- [ ] Zoom controls
- [ ] Keyboard shortcuts (←/→)
- [ ] Fullscreen mode

```tsx
interface MangaViewerProps {
  volumeId: string
  initialPage?: number
  onClose: () => void
}
```

**Acceptance:** Can view all pages, navigation works

---

### 3.3 Integrate MangaViewer
**Priority:** 🟠 High

Tasks:
- [ ] Add viewer to App.tsx
- [ ] Open from MangaLibrary
- [ ] Open from graph node (double-click)
- [ ] Open from metadata panel

**Acceptance:** Multiple entry points to viewer

---

### 3.4 Thumbnail Generation (Optional)
**Priority:** 🟡 Medium

Tasks:
- [ ] Generate thumbnails during import
- [ ] Store thumbnail paths
- [ ] Use in viewer sidebar

**Acceptance:** Fast thumbnail loading

---

## Sprint 4: Polish & Enhancements ✨

**Duration:** 2-3 days  
**Goal:** UX improvements and edge cases

### 4.1 Manga-Specific Node Preview
**Priority:** 🟡 Medium

Tasks:
- [ ] Show page count in node tooltip
- [ ] Show thumbnail preview on hover
- [ ] Different styling for manga nodes

**Acceptance:** Visual distinction for manga nodes

---

### 4.2 Batch Operations
**Priority:** 🟡 Medium

Tasks:
- [ ] Multi-select in MangaLibrary
- [ ] Bulk delete
- [ ] Bulk export

**Acceptance:** Can manage multiple volumes

---

### 4.3 Reading Progress
**Priority:** 🟢 Low

Tasks:
- [ ] Track last read page per volume
- [ ] Show progress bar in library
- [ ] Resume from last page

**Acceptance:** Reading progress persisted

---

### 4.4 Search Manga Content
**Priority:** 🟢 Low

Tasks:
- [ ] Include OCR text in search index
- [ ] Search across manga volumes
- [ ] Show search results with page previews

**Acceptance:** Can search manga content

---

## Implementation Checklist

### Backend
- [ ] Add `node_type` to GraphNode
- [ ] Create database migration
- [ ] Update API endpoints
- [ ] Add image serving endpoint
- [ ] Update CLI to link volume-node

### Frontend Types
- [ ] Create shared types file
- [ ] Unify NodeType definitions
- [ ] Update GraphNode interface

### Frontend Components
- [ ] Update MangaLibrary
- [ ] Create MangaViewer
- [ ] Update SceneMetadata for manga
- [ ] Update GraphCanvas node rendering
- [ ] Add manga-specific tooltips

### Integration
- [ ] Connect UI import to graph node creation
- [ ] Add navigation between volume and node
- [ ] Implement all viewer entry points

---

## Testing Strategy

### Unit Tests
- [ ] GraphNode serialization with type
- [ ] MangaStorage CRUD operations
- [ ] API endpoint responses

### Integration Tests
- [ ] CLI import → storage → graph node
- [ ] UI import → API → storage → graph
- [ ] Viewer loading pages

### E2E Tests
- [ ] Complete import workflow
- [ ] View manga pages
- [ ] Navigate between library and graph

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing nodes | Medium | High | Migration script, backward compat |
| Performance with large volumes | Medium | Medium | Pagination, lazy loading |
| Image storage bloat | Low | Medium | Don't duplicate, serve from source |
| Mobile viewer UX | Medium | Medium | Touch gestures, responsive design |

---

## Success Metrics

- [ ] All 15 items completed
- [ ] Zero TypeScript errors
- [ ] Manga import works end-to-end
- [ ] Can view all pages smoothly
- [ ] Navigation between views works
- [ ] Tests pass

---

## Notes

- **Estimated Total Duration:** 2-3 weeks
- **Dependencies:** Sprint 1 must complete before Sprint 2
- **Sprint 3** can start in parallel after Sprint 1 backend work
- **Sprint 4** is optional enhancements

**Document Version:** 1.0  
**Last Updated:** 2025-02-10
