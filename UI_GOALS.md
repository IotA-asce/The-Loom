# UI Goals & Gap Analysis

**Document Version:** 1.0  
**Last Updated:** 2026-02-10  
**Status:** Comprehensive gap analysis for The Loom frontend

---

## 1. Executive Summary

This document identifies the functional gaps between the **current UI implementation** and the **full backend capabilities** of The Loom. While the backend (Phases 0-10) is feature-complete with 160 tests passing, the React frontend only exposes a subset of capabilities.

### Current UI State
- **Implemented:** Basic graph visualization, branch management, tuner controls, dual-view shell, file import
- **Missing:** Text generation, image generation, retrieval interface, character management, event editing, and many workflow features

---

## 2. What's Currently Implemented

### 2.1 UI Components (8 files)
| Component | Purpose | Status |
|-----------|---------|--------|
| `App.tsx` | Main layout, keyboard shortcuts | ✅ Basic |
| `GraphCanvas.tsx` | Node visualization, zoom | ⚠️ Visual-only (no content) |
| `BranchPanel.tsx` | Branch CRUD operations | ✅ Functional |
| `TunerPanel.tsx` | Violence/humor/romance sliders | ✅ Functional |
| `DualView.tsx` | Text/image split view | ⚠️ Placeholder UI |
| `ImportPanel.tsx` | File upload for ingestion | ✅ Functional |
| `StatusBar.tsx` | Metrics display | ✅ Functional |

### 2.2 API Endpoints Exposed (25 endpoints)
```
Graph:        GET/POST /api/graph/* (6 endpoints)
Branches:     GET/POST /api/branches/* (5 endpoints)
Tuner:        POST /api/tuner/resolve
DualView:     POST /api/dualview/* (4 endpoints)
Accessibility: GET/POST /api/accessibility/* (2 endpoints)
Ingestion:    POST /api/ingest/* (3 endpoints)
Metrics:      GET /api/phase8/metrics, /api/health
```

---

## 3. Major Feature Gaps

### 3.1 🔴 CRITICAL: Text Generation (Phase 5) - 90% Missing

**Backend Capabilities:**
- `WriterEngine` class with full generation pipeline
- Style embedding and exemplar retrieval
- Character voice cards and enforcement
- Long-range coherence with memory summaries
- Contradiction detection and repair
- Tuner mapping for text generation

**UI Gap:**
- ❌ No text generation interface
- ❌ No prompt editor
- ❌ No style exemplar selection
- ❌ No character voice management
- ❌ No generated text display/editing
- ❌ No contradiction warnings display

**Subproblems:**
1. **Generation Request UI**
   - Create interface to select context window
   - Input prompt composition area
   - Parameter controls (temperature, max tokens)
   - Submit and cancel generation

2. **Style Fidelity Controls**
   - Display style similarity scores
   - Allow style exemplar selection from retrieved chunks
   - Visual comparison between source and generated text

3. **Character Voice Management**
   - Character list view with voice cards
   - Voice consistency checker display
   - Character selector in generation context

4. **Generated Content Display**
   - Rich text display with syntax highlighting for dialogue
   - Inline editing with track changes
   - Accept/reject/regenerate workflow

5. **Contradiction Detection Display**
   - Visual warning when contradictions detected
   - Side-by-side comparison of conflicting facts
   - Suggested resolution actions

---

### 3.2 🔴 CRITICAL: Image Generation (Phase 6) - 95% Missing

**Backend Capabilities:**
- `ArtistEngine` with diffusion backend integration
- Scene blueprint generation from text
- ControlNet-compatible flow
- Continuity anchors (camera, pose, environment)
- Atmosphere presets (light/dark ranges)
- Character identity packs with LoRA
- Panel continuity validation
- Quality checks with correction loops

**UI Gap:**
- ❌ No image generation interface
- ❌ No scene blueprint editor
- ❌ No atmosphere preset selector
- ❌ No character identity management
- ❌ No panel sequence viewer
- ❌ No quality check results display
- ❌ No redraw/correction workflow

**Subproblems:**
1. **Scene Blueprint Editor**
   - Structured form for scene elements
   - Character positioning controls
   - Camera angle selection
   - Environment/prop specification

2. **Atmosphere Controls**
   - Preset selector (Light/Neutral/Dark/Horror)
   - Lighting constraint sliders
   - Texture constraint controls
   - Live preview of atmosphere settings

3. **Panel Sequence Viewer**
   - Grid view of generated panels
   - Sequential reader mode
   - Comparison with source text
   - Continuity violation indicators

4. **Character Identity Management**
   - Character gallery with reference images
   - Identity pack builder (face/silhouette/costume)
   - LoRA training trigger interface
   - Drift detection alerts

5. **Quality Control Dashboard**
   - QC scores display per panel
   - Failure reason categorization
   - Batch correction request interface
   - Pass/retry queue management

---

### 3.3 🔴 CRITICAL: Story Content Management - 85% Missing

**Current State:** The graph shows empty nodes with only IDs and labels. No actual story content.

**Missing Features:**

#### 3.3.1 Node Content Editing
**Subproblems:**
1. **Rich Text Editor Integration**
   - Inline editing for node content
   - Markdown/richtext support
   - Auto-save drafts
   - Version history per node

2. **Scene Metadata Editor**
   - Title, location, time-of-day fields
   - Character presence checklist
   - Mood/tone tags
   - Estimated reading time

3. **Node Type System**
   - Chapter, scene, beat, dialogue types
   - Visual differentiation in graph
   - Type-specific fields and validations

#### 3.3.2 Event Timeline Visualization
**Subproblems:**
1. **Chronological View**
   - Timeline display alongside graph
   - Temporal ordering indicators
   - Flashback/flashforward markers

2. **Event Detail Panel**
   - Event metadata display
   - Actor and action breakdown
   - Confidence scores visualization
   - Event merging tools

#### 3.3.3 Entity Management
**Subproblems:**
1. **Character Database UI**
   - Character list with search/filter
   - Profile editor (name, aliases, traits)
   - Relationship graph visualization
   - State tracking across timeline

2. **Location Management**
   - Location hierarchy browser
   - Map/blueprint upload
   - Scene-location association

3. **Entity Conflict Resolution**
   - Contradiction detection display
   - Merge/split entity workflow
   - Alias management interface

---

### 3.4 🟡 HIGH: Retrieval & Memory Interface (Phase 3) - 80% Missing

**Backend Capabilities:**
- Hierarchical chunking and memory model
- Vector index with branch-aware namespaces
- Hybrid retrieval (BM25 + embedding)
- Reranking for canon relevance
- Freshness tracking and stale suppression

**UI Gap:**
- ❌ No search interface
- ❌ No retrieval results viewer
- ❌ No chunk/embedding visualization
- ❌ No branch namespace selector
- ❌ No relevance scoring display

**Subproblems:**
1. **Semantic Search Interface**
   - Natural language query input
   - Filter controls (branch, time range, entity)
   - Search results with relevance scores
   - Preview snippets with highlighting

2. **Context Assembly Viewer**
   - Show retrieved chunks for generation
   - Reorder/remove chunks manually
   - View token budget usage
   - Save custom context presets

3. **Memory Browser**
   - Navigate hierarchical memory structure
   - View arc/chapter/scene summaries
   - Thread tracking for unresolved plots
   - Memory freshness indicators

---

### 3.5 🟡 HIGH: Consequence Simulation (Phase 4) - 75% Missing

**Backend Capabilities:**
- Affected-subgraph recompute pipeline
- Canon constraint enforcement
- Downstream consistency tracking
- Branch recommendation engine

**UI Gap:**
- ❌ No consequence preview before committing changes
- ❌ No affected nodes visualization
- ❌ No consistency score display
- ❌ No recommendation interface

**Subproblems:**
1. **What-If Simulator**
   - Preview changes before applying
   - Visual diff of affected subgraph
   - Consistency impact score
   - Cost estimate (tokens/time)

2. **Recommendation Panel**
   - Display high-impact branch suggestions
   - Divergence score visualization
   - One-click branch creation from recommendations

3. **Constraint Violation Display**
   - Canon constraint checker UI
   - Violation severity indicators
   - Suggested fixes

---

### 3.6 🟡 HIGH: Profile & Analysis Dashboard (Phase 2) - 70% Missing

**Backend Capabilities:**
- Scene-level sentiment/intensity tagging
- Visual tonal classification
- Maturity/rating score bands
- Profile correction and versioning

**UI Gap:**
- ❌ No tone/intensity visualization
- ❌ No maturity rating display
- ❌ No profile editing interface
- ❌ No comparative analysis tools

**Subproblems:**
1. **Tone Analysis Visualization**
   - Heatmap of story tone over time
   - Intensity peaks marking
   - Genre classification display

2. **Maturity Rating Display**
   - Overall rating badge
   - Breakdown by category (violence, language, etc.)
   - Comparison with target audience

3. **Profile Editor**
   - Manual correction interface
   - Version history
   - Override logging and justification

---

### 3.7 🟡 MEDIUM: Operations & Governance (Phase 9) - 60% Missing

**Backend Capabilities:**
- Structured logging with correlation IDs
- SLO definitions and tracking
- Budget controls per job/branch
- Privacy controls and data retention
- Content governance workflows

**UI Gap:**
- ❌ No system status dashboard
- ❌ No budget/cost tracking display
- ❌ No job queue viewer
- ❌ No privacy settings panel

**Subproblems:**
1. **System Dashboard**
   - Real-time SLO metrics
   - Job queue status
   - Recent errors and alerts
   - Resource usage graphs

2. **Budget Controls**
   - Per-branch token usage display
   - Cost estimates before generation
   - Budget limit warnings
   - Usage history

3. **Privacy Settings**
   - Local/remote provider toggles
   - Data retention preferences
   - Export/delete data controls

---

### 3.8 🟢 LOW: Enhanced Graph Features - 50% Missing

**Subproblems:**
1. **Edge Management**
   - Visual edge creation (drag between nodes)
   - Edge type selector (causal, temporal, etc.)
   - Edge labels and annotations

2. **Advanced Navigation**
   - Minimap for large graphs
   - Search and jump to node
   - Bookmark/favorite nodes
   - Recent nodes history

3. **Graph Layout Algorithms**
   - Auto-layout options (hierarchical, force-directed)
   - Branch clustering
   - Timeline-based layout

4. **Collaboration Features**
   - Multi-user cursor indicators
   - Comment threads on nodes
   - Change notifications

---

## 4. UX Workflow Gaps

### 4.1 Onboarding Experience
**Current:** User opens app to empty graph with no guidance
**Needed:**
- Welcome/tutorial modal
- Sample story templates
- Guided first import workflow
- Tooltips and contextual help

### 4.2 Content-First Workflow
**Current:** Graph is structural (nodes with IDs only)
**Needed:**
- Create node → immediately add content flow
- Inline editing without mode switching
- Quick preview of node content on hover
- Reading mode (hide graph, show story)

### 4.3 Generation Workflow
**Current:** No generation capability in UI
**Ideal Flow:**
```
1. Select node with source content
2. Click "Generate Continuation"
3. Configure parameters in sidebar
4. Review retrieved context
5. Submit generation job
6. Watch progress indicator
7. Review generated output
8. Accept/edit/reject/regenerate
9. Auto-create next node if accepted
```

### 4.4 Image-Text Sync Workflow
**Current:** Dual view shows placeholder text
**Ideal Flow:**
```
1. Generate or edit text
2. Click "Generate Panels" (auto-creates scene blueprint)
3. Review/adjust scene blueprint
4. Generate panel sequence
5. View side-by-side comparison
6. Edit text → see image staleness indicator
7. Request specific panel redraw
8. Reconcile when both versions ready
```

---

## 5. Priority Roadmap

### Phase A: Content Foundation (Weeks 1-2)
1. Node content editor with rich text
2. Scene metadata fields
3. Story reading view (content-focused)
4. Character/entity list view

### Phase B: Text Generation (Weeks 3-4)
1. Writer interface with prompt editor
2. Context assembly viewer
3. Generated text display with accept/reject
4. Style exemplar selection

### Phase C: Image Generation (Weeks 5-6)
1. Scene blueprint editor
2. Atmosphere preset selector
3. Panel sequence viewer
4. Quality check dashboard

### Phase D: Advanced Features (Weeks 7-8)
1. Semantic search interface
2. Consequence simulator
3. Profile analysis dashboard
4. System operations panel

---

## 6. Technical Debt & Architecture

### 6.1 State Management
- **Current:** Zustand store with basic actions
- **Need:** Separate stores for different domains (graph, generation, retrieval)
- **Need:** Better async state handling (loading, error states)

### 6.2 API Layer
- **Current:** Inline fetch calls in store
- **Need:** Dedicated API client with request/response interceptors
- **Need:** Request deduplication and caching
- **Need:** Retry logic with exponential backoff

### 6.3 Component Architecture
- **Current:** Monolithic components
- **Need:** Compound component patterns for complex UIs
- **Need:** Virtual scrolling for large lists (characters, search results)

### 6.4 Real-Time Updates
- **Current:** Polling for metrics only
- **Need:** WebSocket/SSE for generation progress
- **Need:** Live collaboration indicators

---

## 7. Accessibility & UX Quality

### 7.1 Current Gaps
- No keyboard navigation for graph (arrow keys to move between nodes)
- No focus management for modal workflows
- Missing loading states for async operations
- No error boundaries for crash recovery

### 7.2 Needed Improvements
1. **Keyboard Navigation**
   - Arrow keys for node selection
   - Tab order optimization
   - Shortcut help overlay (Ctrl+?)

2. **Loading States**
   - Skeleton screens for content
   - Progress indicators for generation
   - Optimistic UI updates

3. **Error Handling**
   - Toast notifications for errors
   - Retry mechanisms
   - Offline detection and queueing

4. **Responsive Design**
   - Mobile-optimized graph view
   - Collapsible panels
   - Touch gesture support

---

## 8. Backend Features Without UI Mapping

| Backend Feature | UI Status | Priority |
|----------------|-----------|----------|
| `WriterEngine.generate()` | ❌ Not exposed | 🔴 Critical |
| `ArtistEngine.generate_panels()` | ❌ Not exposed | 🔴 Critical |
| `retrieve_style_exemplars()` | ❌ Not exposed | 🔴 Critical |
| `ingest_text_document()` | ✅ ImportPanel | ✅ Done |
| `ConsequenceSimulator.simulate()` | ❌ Not exposed | 🟡 High |
| `extract_events_hybrid()` | ❌ Not exposed | 🟡 High |
| `detect_entity_state_conflicts()` | ❌ Not exposed | 🟡 High |
| `build_scene_blueprint()` | ❌ Not exposed | 🔴 Critical |
| `validate_panel_continuity()` | ❌ Not exposed | 🟡 High |
| `atmosphere_preset()` | ❌ Not exposed | 🟡 High |
| `CharacterIdentityPack` management | ❌ Not exposed | 🟡 High |
| `VectorIndex` search | ❌ Not exposed | 🟡 High |
| `HierarchicalMemoryModel` browser | ❌ Not exposed | 🟡 High |
| `check_contradictions()` | ❌ Not exposed | 🟡 High |
| `tuner_impact_preview()` | ⚠️ Basic in TunerPanel | 🟢 Low |
| `BranchLifecycleManager` | ✅ BranchPanel | ✅ Done |
| `GraphWorkspace` | ⚠️ Partial (GraphCanvas) | 🟢 Low |
| `DualViewManager` | ⚠️ Shell only | 🟡 High |
| `AccessibilityManager` | ❌ Not exposed | 🟢 Low |

---

## 9. Success Metrics

### 9.1 Feature Completeness
- [ ] Text generation UI: 0% → 100%
- [ ] Image generation UI: 0% → 100%
- [ ] Content editing: 10% → 100%
- [ ] Search/retrieval: 0% → 100%
- [ ] Character management: 0% → 100%

### 9.2 UX Quality
- [ ] Complete workflow without CLI: 20% → 100%
- [ ] First-time user completion rate: Target 80%
- [ ] Average task completion time: < 5 minutes per generation
- [ ] Error recovery rate: > 95%

---

## 10. Appendix: File Inventory

### Current UI Files
```
ui/src/
├── App.tsx                 # Main layout
├── main.tsx               # Entry point
├── store.ts               # Zustand state
├── types/index.ts         # Type definitions
└── components/
    ├── GraphCanvas.tsx    # Graph visualization
    ├── BranchPanel.tsx    # Branch management
    ├── TunerPanel.tsx     # Tone controls
    ├── DualView.tsx       # Text/image split
    ├── ImportPanel.tsx    # File upload
    └── StatusBar.tsx      # Footer metrics
```

### Needed New Components
```
ui/src/components/
├── generation/
│   ├── WriterPanel.tsx       # Text generation
│   ├── ArtistPanel.tsx       # Image generation
│   ├── ContextViewer.tsx     # Retrieved chunks
│   ├── StyleSelector.tsx     # Style exemplars
│   └── QualityDashboard.tsx  # QC results
├── content/
│   ├── RichTextEditor.tsx    # Node content
│   ├── SceneMetadata.tsx     # Scene fields
│   ├── CharacterPanel.tsx    # Character DB
│   └── EntityManager.tsx     # Entity CRUD
├── analysis/
│   ├── ToneHeatmap.tsx       # Tone visualization
│   ├── TimelineView.tsx      # Chronological
│   ├── SearchPanel.tsx       # Semantic search
│   └── ProfileEditor.tsx     # Profile corrections
└── system/
    ├── Dashboard.tsx         # Operations
    ├── BudgetPanel.tsx       # Cost tracking
    └── SettingsPanel.tsx     # Privacy/settings
```

---

**End of Document**

For implementation details, see:
- `agents/` - Backend agent implementations
- `core/` - Engine implementations  
- `GOALS.md` - Full project goals
- `PRD.md` - Product requirements
