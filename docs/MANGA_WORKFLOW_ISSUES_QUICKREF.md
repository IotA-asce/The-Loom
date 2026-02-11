# Manga Workflow Issues - Quick Reference

> TL;DR of all disconnects and missing features

---

## 🔴 Critical Issues (Fix Immediately)

### 1. Backend/Frontend Type Mismatch
```
Backend GraphNode:     metadata = {"type": "manga"}  (fragile)
Frontend GraphNode:    type: "manga"  (required field)
```
**Fix:** Add `node_type` field to backend GraphNode

### 2. No Manga Viewer
**Problem:** Can import manga but cannot view pages  
**Fix:** Build MangaViewer component + image serving API

### 3. No Image Serving
**Problem:** API returns metadata but not actual images  
**Fix:** Add `GET /api/manga/{id}/pages/{num}/image`

---

## 🟠 High Priority Issues

### 4. NodeType Inconsistency
```
store.ts:      NodeType = 'chapter' | 'scene' | 'beat' | 'dialogue' | 'manga'
graphStore.ts: NodeType = 'chapter' | 'scene' | 'beat' | 'dialogue'  (missing 'manga'!)
```
**Fix:** Create shared types file

### 5. Broken Volume-Node Link
**Problem:** CLI creates graph node but doesn't update volume.graph_node_id  
**Impact:** "📝 In graph" badge never shows  
**Fix:** Update volume after creating node

### 6. UI Import Doesn't Create Graph Node
**Problem:** Manga imported via UI is invisible in graph  
**Fix:** Add `create_graph_node` param to API + UI

### 7. No Navigation Between Views
**Problem:** Cannot go from library to graph node or vice versa  
**Fix:** Add "Go to Node" and "View Manga" buttons

---

## 🟡 Medium Priority Issues

### 8. Manga Node Shows Empty Preview
**Problem:** Node tooltip shows "No content" for manga  
**Fix:** Show page count instead of text preview

### 9. No Thumbnails
**Problem:** Viewer would load full images for sidebar  
**Fix:** Generate thumbnails during import

### 10. Missing Batch Operations
**Problem:** Can only delete one manga at a time  
**Fix:** Multi-select in library

---

## 🟢 Low Priority (Nice to Have)

### 11. No Reading Progress
Track last read page per volume

### 12. No Manga Search
OCR text not searchable

### 13. Mobile Viewer UX
Touch gestures not implemented

---

## Files to Modify

### Backend
```
core/graph_persistence.py    # Add node_type field
core/manga_storage.py         # Add graph_node_id update
ui/api.py                     # Add image endpoint, update schemas
scripts/import_manga_folder.py # Link volume to node
```

### Frontend
```
ui/src/types/common.ts (new)        # Shared types
ui/src/store.ts                     # Use node_type, loadGraphNodes
ui/src/stores/graphStore.ts         # Import shared types
ui/src/components/MangaViewer.tsx (new)   # Page viewer
ui/src/components/MangaLibrary.tsx         # Add navigation
ui/src/components/SceneMetadata.tsx        # Add "View Manga" button
ui/src/components/GraphCanvas.tsx          # Manga preview
ui/src/App.tsx                      # Integrate viewer
```

---

## Sprint Assignment

| Sprint | Issues | Duration |
|--------|--------|----------|
| Sprint 1 | #1, #4, backend changes | 3-4 days |
| Sprint 2 | #5, #6, #7 | 2-3 days |
| Sprint 3 | #2, #3, viewer | 5-7 days |
| Sprint 4 | #8-13 polish | 2-3 days |

**Total: 2-3 weeks**

---

## Quick Fixes (Can Do Now)

1. **Fix NodeType in graphStore.ts:**
   ```typescript
   export type NodeType = 'chapter' | 'scene' | 'beat' | 'dialogue' | 'manga'
   ```

2. **Update CLI to link volume:**
   ```python
   volume = MangaVolume(..., graph_node_id=node_id)
   ```

3. **Add temp image endpoint:**
   ```python
   @app.get("/api/manga/{vid}/pages/{pn}/image")
   async def get_image(vid: str, pn: int):
       # Return FileResponse
   ```

---

## Success Criteria

- [ ] Import manga via CLI → see in library
- [ ] Import manga via UI → see in graph
- [ ] Click manga in library → view pages
- [ ] Double-click manga node → view pages
- [ ] Navigate pages smoothly
- [ ] All types consistent

---

## Related Docs

- Full plan: `MANGA_WORKFLOW_SPRINT_PLAN.md`
- UI behavior: `MANGA_UI_BEHAVIOR.md`
- Import guide: `MANGA_IMPORT.md`
