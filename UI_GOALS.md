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


---

## 11. Comprehensive Implementation Checklist

This section consolidates all remaining UI features into an actionable checklist. Use this as the master tracking document for UI development.

### Legend
- `[ ]` Not started
- `[-]` In progress
- `[x]` Complete
- **🔴 Critical** - Blocks core workflows
- **🟡 High** - Important for full functionality
- **🟢 Low** - Nice to have

---

### 📚 A. Content Management (Phase A)

#### A.1 Node Content Editing
- [x] **A.1.1** Rich text editor component
  - [x] Markdown support
  - [x] WYSIWYG toolbar
  - [x] Auto-save drafts
  - [x] Undo/redo within editor
- [x] **A.1.2** Inline node editing
  - [x] Double-click to edit
  - [x] ESC to cancel, Enter to save
  - [x] Visual edit mode indicator
- [x] **A.1.3** Node content display
  - [x] Preview on hover
  - [x] Expand/collapse long content
  - [x] Syntax highlighting for dialogue
- [x] **A.1.4** Version history
  - [x] Save revisions on edit
  - [-] Diff viewer between versions
  - [x] Restore previous version

#### A.2 Scene Metadata 🔴
- [x] **A.2.1** Metadata form fields
  - [x] Title input
  - [x] Location selector
  - [x] Time-of-day picker
  - [x] Estimated reading time
- [x] **A.2.2** Character presence
  - [x] Multi-select character checklist
  - [-] Character entry/exit markers
  - [-] Auto-detect from content
- [x] **A.2.3** Mood/tone tags
  - [x] Tag input with autocomplete
  - [x] Preset mood options
  - [x] Color-coded mood indicators

#### A.3 Node Type System
- [x] **A.3.1** Type definitions
  - [x] Chapter nodes
  - [x] Scene nodes
  - [x] Beat nodes
  - [x] Dialogue nodes
- [x] **A.3.2** Visual differentiation
  - [x] Different shapes per type
  - [x] Color coding
  - [x] Icon indicators
- [x] **A.3.3** Type-specific fields
  - [x] Conditional form fields per type
  - [x] Validation rules per type
  - [x] Chapter: number, arc, summary
  - [x] Scene: location, time, weather, POV
  - [x] Beat: type, goal, outcome, stakes
  - [x] Dialogue: speaker, emotion, action, listener

#### A.4 Story Reading View 🔴
- [x] **A.4.1** Reading mode toggle
  - [x] Hide graph, show content
  - [x] Scrollable narrative view
  - [x] Branch selection dropdown
- [x] **A.4.2** Navigation
  - [x] Previous/next scene buttons
  - [x] Chapter jump menu
  - [x] Progress indicator
- [x] **A.4.3** Reading preferences
  - [x] Font size controls
  - [x] Light/dark theme
  - [x] Line spacing options

---

### ✍️ B. Text Generation (Phase B)

#### B.1 Writer Panel 🔴
- [x] **B.1.1** Generation request interface
  - [ ] Context window selector
  - [x] Prompt composition textarea
  - [x] Temperature slider (0-2)
  - [x] Max tokens input
  - [ ] Model selector (if multiple)
- [x] **B.1.2** Submit workflow
  - [x] Submit button with validation
  - [ ] Cancel generation button
  - [x] Progress indicator (streaming)
  - [ ] Estimated time display
- [x] **B.1.3** Generated content display
  - [x] Rich text output area
  - [x] Dialogue highlighting
  - [-] Paragraph numbering
  - [x] Word count display
- [x] **B.1.4** Action buttons
  - [x] Accept button (creates node)
  - [x] Reject button (discards)
  - [x] Regenerate button
  - [-] Edit inline button

#### B.2 Context Assembly Viewer 🔴
- [x] **B.2.1** Retrieved chunks display
  - [x] List of context chunks
  - [x] Relevance scores
  - [x] Source attribution
  - [x] Expand/collapse each chunk
  - [x] Token count per chunk
- [x] **B.2.2** Manual context management
  - [x] Reorder chunks (up/down buttons)
  - [x] Remove chunk button
  - [x] Context search/filter
  - [x] Pin important chunks
- [x] **B.2.3** Token budget visualization
  - [x] Stacked progress bar (prompt/context/generation)
  - [x] Color-coded segments
  - [x] Warning at 80%
  - [x] Error at 100%
  - [x] Legend with breakdown
- [x] **B.2.4** Save context presets
  - [x] Name and save current context
  - [x] Load preset button
  - [x] Delete preset button
  - [x] Active preset indicator

#### B.3 Style Fidelity Controls 🟡
- [x] **B.3.1** Style similarity display
  - [x] Overall similarity score (average)
  - [-] Per-paragraph comparison (deferred)
  - [-] Visual similarity meter (deferred)
- [x] **B.3.2** Style exemplar selection
  - [x] List retrieved exemplars
  - [x] Preview each exemplar
  - [x] Select/deselect checkboxes
  - [x] "Use as style guide" button (star toggle)
- [x] **B.3.3** Style profile indicator
  - [x] Active style profile panel
  - [x] Exemplars count
  - [x] Average similarity score

#### B.4 Character Voice Management 🟡
- [x] **B.4.1** Character list view
  - [x] Grid of character cards
  - [x] Search/filter by name
  - [x] Sort by importance/appearance/name
  - [x] Active voices summary
- [x] **B.4.2** Voice card display
  - [x] Character name and aliases
  - [x] Voice traits list
  - [x] Sample dialogue quotes
  - [x] Consistency score
- [x] **B.4.3** Character selector in generation
  - [x] New "Voices" tab in Writer panel
  - [x] Voice enforcement toggle per character
  - [x] "Focus on character" option (star badge)

#### B.5 Contradiction Detection Display 🟡
- [x] **B.5.1** Warning indicators
  - [x] Yellow warning banner for minor issues
  - [x] Red banner for contradictions
  - [x] Count badge in status bar
- [x] **B.5.2** Contradiction detail view
  - [x] Expandable contradiction items
  - [x] Severity badges (high/medium/low)
  - [x] Type and suggested fix display
  - [-] Side-by-side comparison (deferred)
  - [-] Source reference links (deferred)
- [x] **B.5.3** Resolution actions
  - [x] "Ignore" button
  - [x] "Apply Fix" button
  - [x] "Regenerate with fix" button

---

### 🎨 C. Image Generation (Phase C)

#### C.1 Scene Blueprint Editor 🔴
- [x] **C.1.1** Scene elements form
  - [x] Setting description textarea
  - [x] Time of day selector (Dawn to Midnight)
  - [x] Weather selector (Clear, Cloudy, Rainy, Stormy, Foggy, Snowy)
- [x] **C.1.2** Character positioning
  - [x] Character presence checklist
  - [x] Position dropdown (left/center/right/background)
  - [x] Pose description input
  - [x] Expression selector (neutral, happy, sad, angry, surprised, fearful, determined)
- [x] **C.1.3** Camera controls
  - [x] Shot type buttons (Wide/Medium/Close-up/Extreme Close)
  - [x] Camera angle buttons (Eye Level/High Angle/Low Angle/Dutch)
  - [x] Focus point input
- [x] **C.1.4** Environment/props
  - [x] Key props list with add/remove
  - [x] Props display with tags

#### C.2 Atmosphere Controls 🔴
- [x] **C.2.1** Preset selector
  - [x] Light/Wholesome preset
  - [x] Neutral/Dramatic preset
  - [x] Dark/Moody preset
  - [x] Horror preset
- [x] **C.2.2** Lighting constraints
  - [x] Light source direction picker (5 directions)
  - [x] Intensity slider (0-100%)
  - [x] Contrast slider (0-100%)
  - [x] Shadow hardness slider (0-100%)
- [x] **C.2.3** Texture constraints
  - [x] Texture detail level slider
  - [x] Style toggle (clean/gritty)
  - [x] Weathering effects slider
- [x] **C.2.4** Live preview
  - [x] Atmosphere preview gradient box
  - [x] Preset name display

#### C.3 Panel Sequence Viewer 🔴
- [x] **C.3.1** Grid view
  - [x] 2-column grid layout
  - [x] Panel numbering
  - [x] Selection checkbox per panel (batch mode)
  - [x] Panel actions (regenerate, delete)
  - [x] Issue badges for continuity problems
- [x] **C.3.2** Sequential reader mode
  - [x] Full-panel viewer with navigation
  - [x] Previous/next buttons
  - [x] Progress bar
  - [x] Panel counter display
- [x] **C.3.3** Comparison view (Split mode)
  - [x] Split view with source text
  - [x] Panel grid beside text
- [x] **C.3.4** Continuity indicators
  - [x] Warning icons for drift
  - [x] Color-coded issue badges (high/medium/low)

#### C.4 Character Identity Management 🟡
- [ ] **C.4.1** Character gallery
  - [ ] Grid of character portraits
  - [ ] Filter by importance
  - [ ] Search by name
  - [ ] Sort by panel appearance
- [ ] **C.4.2** Identity pack builder
  - [ ] Face reference upload
  - [ ] Silhouette reference upload
  - [ ] Costume reference upload
  - [ ] Reference image preview
- [ ] **C.4.3** LoRA training interface
  - [ ] Training trigger button
  - [ ] Progress indicator
  - [ ] Training history log
  - [ ] Model version selector
- [ ] **C.4.4** Drift detection alerts
  - [ ] Alert banner when drift detected
  - [ ] Affected panels list
  - [ ] "Retrain LoRA" button
  - [ ] Ignore/accept current option

#### C.5 Quality Control Dashboard 🟡
- [ ] **C.5.1** QC scores display
  - [ ] Overall quality meter
  - [ ] Per-panel scores
  - [ ] Category breakdown (anatomy/composition/color)
- [ ] **C.5.2** Failure categorization
  - [ ] Filter by failure type
  - [ ] Count per category
  - [ ] Example thumbnails
- [ ] **C.5.3** Correction workflow
  - [ ] Select panels for correction
  - [ ] Correction reason input
  - [ ] Priority selector
  - [ ] Submit correction batch
- [ ] **C.5.4** Pass/retry queue
  - [ ] Queue status display
  - [ ] Retry failed generations
  - [ ] Cancel pending jobs
  - [ ] Results notification

#### C.6 Generation Request Interface 🔴
- [x] **C.6.1** Request form
  - [x] Panel count input (1-16)
  - [x] Aspect ratio selector (1:1, 4:3, 16:9, 9:16, Cinematic)
  - [x] Seed input (optional)
- [x] **C.6.2** Advanced options
  - [x] CFG scale slider (1-15)
  - [x] Step count selector (10-50)
  - [x] Sampler method dropdown (6 options)
  - [x] Negative prompt input
- [x] **C.6.3** Batch controls
  - [x] Batch mode toggle
  - [x] Multi-select panels
  - [x] Batch regenerate
  - [x] Batch delete
- [x] **C.6.4** Progress tracking
  - [x] Overall progress bar
  - [x] Current step indicator
  - [x] ETA display
  - [x] Cancel button

---

### 🔎 D. Retrieval & Memory (Phase D)

#### D.1 Semantic Search Interface 🟡
- [ ] **D.1.1** Search input
  - [ ] Natural language query box
  - [ ] Search history dropdown
  - [ ] Saved searches list
  - [ ] Voice input (optional)
- [ ] **D.1.2** Filter controls
  - [ ] Branch selector
  - [ ] Time range picker
  - [ ] Entity filter (character/location)
  - [ ] Content type filter
- [ ] **D.1.3** Results display
  - [ ] List view with snippets
  - [ ] Relevance score per result
  - [ ] Source metadata (chapter, scene)
  - [ ] "Add to context" button per result
- [ ] **D.1.4** Result preview
  - [ ] Expand to full content
  - [ ] Highlight search terms
  - [ ] Navigation to source node

#### D.2 Memory Browser 🟡
- [ ] **D.2.1** Hierarchical navigation
  - [ ] Arc level view
  - [ ] Chapter level view
  - [ ] Scene level view
  - [ ] Breadcrumb navigation
- [ ] **D.2.2** Summary display
  - [ ] Arc summaries
  - [ ] Chapter summaries
  - [ ] Scene summaries
  - [ ] Summary edit button
- [ ] **D.2.3** Thread tracking
  - [ ] Unresolved threads list
  - [ ] Thread status indicators
  - [ ] "Resolve thread" button
  - [ ] Thread visualization graph
- [ ] **D.2.4** Freshness indicators
  - [ ] Stale content badges
  - [ ] Last updated timestamp
  - [ ] Update in progress spinner
  - [ ] Refresh button

---

### 🌿 E. Consequence Simulation

#### E.1 What-If Simulator 🟡
- [ ] **E.1.1** Change input
  - [ ] Select node to modify
  - [ ] Proposed change textarea
  - [ ] Change type selector
- [ ] **E.1.2** Impact preview
  - [ ] Affected nodes list
  - [ ] Visual diff in graph
  - [ ] Affected subgraph highlight
- [ ] **E.1.3** Consistency scoring
  - [ ] Overall consistency score
  - [ ] Per-node impact score
  - [ ] Risk level indicator
- [ ] **E.1.4** Cost estimation
  - [ ] Token usage estimate
  - [ ] Time estimate
  - [ ] Cost in credits/currency

#### E.2 Recommendation Panel 🟢
- [ ] **E.2.1** High-impact suggestions
  - [ ] Suggested branch points list
  - [ ] Divergence score per suggestion
  - [ ] Impact summary
- [ ] **E.2.2** One-click actions
  - [ ] "Create branch here" button
  - [ ] Preview impact button
  - [ ] Dismiss suggestion button

#### E.3 Constraint Violation Display 🟢
- [ ] **E.3.1** Canon constraint checker
  - [ ] Active constraints list
  - [ ] Violation count badge
  - [ ] Severity indicators
- [ ] **E.3.2** Violation details
  - [ ] Violated constraint description
  - [ ] Affected content preview
  - [ ] Suggested fixes list

---

### 📊 F. Profile & Analysis

#### F.1 Tone Analysis Visualization 🟡
- [ ] **F.1.1** Tone heatmap
  - [ ] Color-coded scene tones
  - [ ] Timeline x-axis
  - [ ] Intensity y-axis
  - [ ] Zoom/pan controls
- [ ] **F.1.2** Intensity peaks
  - [ ] Peak detection markers
  - [ ] Peak type classification
  - [ ] Click to navigate to scene
- [ ] **F.1.3** Genre indicators
  - [ ] Genre classification display
  - [ ] Multi-genre tag cloud
  - [ ] Confidence score

#### F.2 Maturity Rating Display 🟢
- [ ] **F.2.1** Overall rating
  - [ ] Rating badge (G/PG/PG-13/R/etc)
  - [ ] Rating justification summary
- [ ] **F.2.2** Category breakdown
  - [ ] Violence score bar
  - [ ] Language score bar
  - [ ] Sexual content score bar
  - [ ] Mature themes score bar
- [ ] **F.2.3** Audience comparison
  - [ ] Target audience selector
  - [ ] Suitability indicator
  - [ ] Content warnings list

#### F.3 Profile Editor 🟢
- [ ] **F.3.1** Manual corrections
  - [ ] Tone override controls
  - [ ] Intensity adjustment sliders
  - [ ] Genre tag editor
- [ ] **F.3.2** Version history
  - [ ] Profile versions list
  - [ ] Diff between versions
  - [ ] Restore previous version
- [ ] **F.3.3** Override logging
  - [ ] Reason input field
  - [ ] Timestamp and author
  - [ ] Audit trail view

---

### ⚙️ G. Operations & System

#### G.1 System Dashboard 🟢
- [ ] **G.1.1** SLO metrics
  - [ ] Latency charts
  - [ ] Success rate gauges
  - [ ] Error rate trends
- [ ] **G.1.2** Job queue status
  - [ ] Pending jobs count
  - [ ] In-progress jobs list
  - [ ] Completed jobs history
- [ ] **G.1.3** Recent alerts
  - [ ] Error notifications
  - [ ] Warning messages
  - [ ] Dismiss/clear buttons

#### G.2 Budget Controls 🟡
- [ ] **G.2.1** Usage display
  - [ ] Current period usage
  - [ ] Usage by branch
  - [ ] Usage by operation type
- [ ] **G.2.2** Cost estimation
  - [ ] Pre-generation estimate
  - [ ] Confidence interval
  - [ ] Budget remaining
- [ ] **G.2.3** Limit warnings
  - [ ] 50% warning
  - [ ] 80% warning
  - [ ] 100% block with override option

#### G.3 Privacy Settings 🟢
- [ ] **G.3.1** Provider toggles
  - [ ] Local-only mode checkbox
  - [ ] External provider opt-in
  - [ ] Provider selection dropdown
- [ ] **G.3.2** Data retention
  - [ ] Retention period selector
  - [ ] Auto-delete toggle
  - [ ] Manual purge button
- [ ] **G.3.3** Export/delete
  - [ ] Export all data button
  - [ ] Delete account/data button
  - [ ] Confirmation dialogs

---

### 🕸️ H. Enhanced Graph Features

#### H.1 Edge Management 🟢
- [ ] **H.1.1** Visual edge creation
  - [ ] Drag from node to node
  - [ ] Connection preview line
  - [ ] Snap to node highlight
- [ ] **H.1.2** Edge configuration
  - [ ] Edge type selector
  - [ ] Edge label input
  - [ ] Line style selector (solid/dashed)
  - [ ] Color picker
- [ ] **H.1.3** Edge display
  - [ ] Label visibility toggle
  - [ ] Edge weight visualization
  - [ ] Arrow direction indicators

#### H.2 Advanced Navigation 🟢
- [ ] **H.2.1** Minimap
  - [ ] Overview of full graph
  - [ ] Viewport rectangle
  - [ ] Click to jump
- [ ] **H.2.2** Search and jump
  - [ ] Node search box
  - [ ] Fuzzy matching
  - [ ] Enter to focus and center
- [ ] **H.2.3** Bookmarks
  - [ ] Bookmark current node
  - [ ] Bookmarks list dropdown
  - [ ] Click to navigate
- [ ] **H.2.4** History
  - [ ] Recent nodes list
  - [ ] Back/forward navigation
  - [ ] Clear history button

#### H.3 Graph Layout 🟢
- [ ] **H.3.1** Layout algorithms
  - [ ] Hierarchical layout
  - [ ] Force-directed layout
  - [ ] Circular layout
  - [ ] Timeline layout
- [ ] **H.3.2** Branch clustering
  - [ ] Group by branch
  - [ ] Collapse/expand branches
  - [ ] Branch color coding
- [ ] **H.3.3** Layout controls
  - [ ] Layout selector dropdown
  - [ ] Apply layout button
  - [ ] Animate transitions toggle

#### H.4 Collaboration 🟢
- [ ] **H.4.1** Multi-user indicators
  - [ ] Other user cursors
  - [ ] User color coding
  - [ ] User name labels
- [ ] **H.4.2** Comments
  - [ ] Add comment to node
  - [ ] Comment thread view
  - [ ] Resolve comment button
- [ ] **H.4.3** Notifications
  - [ ] Change notifications
  - [ ] Mention notifications
  - [ ] Notification settings

---

### 🎯 I. UX & Workflow Improvements

#### I.1 Onboarding
- [ ] **I.1.1** Welcome modal
  - [ ] App introduction
  - [ ] Feature highlights
  - [ ] Get started button
- [ ] **I.1.2** Interactive tutorial
  - [ ] Step-by-step guide
  - [ ] Highlight UI elements
  - [ ] Skip option
- [ ] **I.1.3** Sample templates
  - [ ] Template gallery
  - [ ] One-click import
  - [ ] Template preview

#### I.2 Keyboard Navigation 🔴
- [x] **I.2.1** Graph navigation
  - [x] Arrow keys for node selection
  - [x] Enter to edit
  - [x] Delete to remove
- [x] **I.2.2** Global shortcuts
  - [x] Ctrl+?: Show shortcuts
  - [x] Ctrl+Z: Undo
  - [x] Ctrl+Y: Redo
  - [x] Ctrl+T: Toggle tuner
  - [x] Ctrl+D: Toggle dual view
  - [x] Ctrl+S: Save
  - [x] Ctrl+N: New node
  - [x] Ctrl+R: Toggle reading mode
- [x] **I.2.3** Focus management
  - [x] Tab order optimization
  - [x] Focus trap in modals (RichTextEditor)
  - [x] Escape to close panels

#### I.3 Loading & Error States 🔴
- [x] **I.3.1** Loading indicators
  - [x] Skeleton screens (basic)
  - [x] Progress bars (generation)
  - [x] Spinner for async ops
- [x] **I.3.2** Error handling
  - [x] Toast notifications system
  - [x] Error boundary fallback
  - [x] useToast hook for easy usage
  - [-] Retry buttons (partial)
- [-] **I.3.3** Offline support (deferred)
  - [ ] Offline detection
  - [ ] Queue changes locally
  - [ ] Sync when back online

#### I.4 Responsive Design 🟡
- [ ] **I.4.1** Mobile optimization
  - [ ] Touch gestures
  - [ ] Collapsible panels
  - [ ] Mobile-optimized graph
- [ ] **I.4.2** Tablet support
  - [ ] Split view layouts
  - [ ] Touch-friendly controls
  - [ ] Orientation handling

---

### 🔧 J. Technical Infrastructure

#### J.1 State Management
- [ ] **J.1.1** Store separation
  - [ ] Graph store
  - [ ] Generation store
  - [ ] Retrieval store
  - [ ] System store
- [ ] **J.1.2** Async state
  - [ ] Loading states
  - [ ] Error states
  - [ ] Optimistic updates

#### J.2 API Layer
- [ ] **J.2.1** API client
  - [ ] Request/response interceptors
  - [ ] Error handling
  - [ ] Request deduplication
- [ ] **J.2.2** Caching
  - [ ] Request caching
  - [ ] Cache invalidation
  - [ ] Stale-while-revalidate
- [ ] **J.2.3** Retry logic
  - [ ] Exponential backoff
  - [ ] Max retry count
  - [ ] Circuit breaker

#### J.3 Real-Time Updates 🟡
- [ ] **J.3.1** WebSocket/SSE
  - [ ] Connection management
  - [ ] Reconnection logic
  - [ ] Message handling
- [ ] **J.3.2** Progress streaming
  - [ ] Generation progress
  - [ ] Upload progress
  - [ ] Processing status

---

## 12. Quick Stats

| Category | Total Items | Critical | High | Low |
|----------|-------------|----------|------|-----|
| Content Management | 28 | 4 | 12 | 12 |
| Text Generation | 32 | 12 | 12 | 8 |
| Image Generation | 44 | 16 | 16 | 12 |
| Retrieval & Memory | 20 | 0 | 20 | 0 |
| Consequence Simulation | 12 | 0 | 6 | 6 |
| Profile & Analysis | 16 | 0 | 4 | 12 |
| Operations & System | 16 | 0 | 4 | 12 |
| Enhanced Graph | 24 | 0 | 0 | 24 |
| UX & Workflow | 20 | 4 | 8 | 8 |
| Technical Infrastructure | 12 | 0 | 4 | 8 |
| **TOTAL** | **224** | **36** | **86** | **102** |

---

## 13. Recommended Sprint Planning

### Sprint 1-2: Content Foundation (36 items)
Focus: A.1, A.2, A.3, A.4, I.2, I.3

### Sprint 3-4: Text Generation (32 items)
Focus: B.1, B.2, B.3, B.4, B.5

### Sprint 5-6: Image Generation (44 items)
Focus: C.1, C.2, C.3, C.6

### Sprint 7-8: Advanced Features (60 items)
Focus: D.1, D.2, E.1, F.1, H.1, H.2, H.3

### Sprint 9-10: Polish & Infrastructure (52 items)
Focus: I.1, I.4, J.1, J.2, J.3, remaining items

---

**End of Document**

For questions or clarifications, refer to:
- `agents/` - Backend agent implementations
- `core/` - Engine implementations
- `GOALS.md` - Full project goals
- `PRD.md` - Product requirements
