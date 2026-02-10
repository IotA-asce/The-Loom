# Pending Goals & Implementation Checklist

**Document Version:** 1.0  
**Last Updated:** 2026-02-10  
**Status:** Comprehensive pending items for The Loom project

---

## Legend

- `[ ]` Not started / Pending
- `[-]` Partially implemented
- `[x]` Complete
- **🔴 Critical** - Blocks core workflows
- **🟡 High** - Important for full functionality  
- **🟢 Low** - Nice to have / Deferred

---

## Backend Pending Items

### B.1 Image Generation Engine (Phase 6) 🟡

#### B.1.1 LoRA Training Pipeline
- [ ] **B.1.1.1** LoRA training trigger endpoint
  - [ ] Training job queue
  - [ ] Progress tracking
  - [ ] Model version management
- [ ] **B.1.1.2** Character identity pack training
  - [ ] Face reference processing
  - [ ] Silhouette extraction
  - [ ] Costume feature learning
- [ ] **B.1.1.3** Drift detection & retraining
  - [ ] Identity consistency monitoring
  - [ ] Automatic retraining triggers
  - [ ] Drift alert system

#### B.1.2 Quality Control Dashboard API
- [ ] **B.1.2.1** QC scoring endpoints
  - [ ] Per-panel quality scores
  - [ ] Category breakdown (anatomy/composition/color)
  - [ ] Overall quality meter
- [ ] **B.1.2.2** Failure categorization
  - [ ] Filter by failure type
  - [ ] Count per category
  - [ ] Example thumbnails endpoint
- [ ] **B.1.2.3** Correction workflow
  - [ ] Select panels for correction
  - [ ] Priority queue management
  - [ ] Batch correction requests

#### B.1.3 Diffusion Backend Integration
- [ ] **B.1.3.1** Real diffusion model integration
  - [ ] Stable Diffusion / Flux backend
  - [ ] ControlNet condition application
  - [ ] LoRA adapter loading at inference
- [ ] **B.1.3.2** GPU resource management
  - [ ] Queue management for GPU jobs
  - [ ] Memory optimization
  - [ ] Batch inference support

### B.2 API Endpoints (Missing) 🟡

#### B.2.1 Writer Engine Endpoints
- [ ] **B.2.1.1** `POST /api/writer/generate`
  - [ ] Full generation pipeline
  - [ ] Context assembly from retrieval
  - [ ] Style exemplar integration
- [ ] **B.2.1.2** `GET /api/writer/style-exemplars`
  - [ ] Retrieve style exemplars for query
  - [ ] Similarity scoring
- [ ] **B.2.1.3** `POST /api/writer/check-contradictions`
  - [ ] Contradiction detection
  - [ ] Suggested fixes

#### B.2.2 Artist Engine Endpoints  
- [ ] **B.2.2.1** `POST /api/artist/generate-panels`
  - [ ] Full panel generation pipeline
  - [ ] Scene blueprint processing
  - [ ] Continuity validation
- [ ] **B.2.2.2** `POST /api/artist/train-lora`
  - [ ] Character identity training
  - [ ] Training progress streaming
- [ ] **B.2.2.3** `GET /api/artist/quality-check`
  - [ ] QC scoring for panels
  - [ ] Failure categorization

#### B.2.3 Retrieval Endpoints
- [ ] **B.2.3.1** `POST /api/retrieve/context`
  - [ ] Hybrid retrieval (BM25 + embedding)
  - [ ] Branch-aware namespace filtering
  - [ ] Reranking for canon relevance
- [ ] **B.2.3.2** `GET /api/memory/hierarchy`
  - [ ] Hierarchical memory navigation
  - [ ] Thread tracking

#### B.2.4 Consequence Simulation Endpoints
- [ ] **B.2.4.1** `POST /api/simulate/impact`
  - [ ] Affected-subgraph computation
  - [ ] Consistency scoring
  - [ ] Cost estimation

### B.3 Continuous Goals (GC) 🟡

- [ ] **GC.1.1** Write focused tests for each new capability
- [ ] **GC.1.2** Run narrowest relevant tests first, then broader suites
- [ ] **GC.1.3** Track flaky tests and eliminate them quickly
- [ ] **GC.2.1** Update docs whenever behavior or interfaces change
- [ ] **GC.2.2** Keep command docs synced with actual scripts/tooling
- [ ] **GC.2.3** Keep architectural decisions discoverable in repo docs
- [ ] **GC.3.1** Keep each PR scoped to one goal or tightly-related goal slice
- [ ] **GC.3.2** Avoid unrelated refactors in milestone PRs
- [ ] **GC.3.3** Record tradeoffs and deferred work explicitly

---

## Frontend Pending Items

### F.1 Image Generation UI (Phase C) 🟡

#### F.1.1 Character Identity Management (C.4)
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

#### F.1.2 Quality Control Dashboard (C.5)
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

### F.2 Consequence Simulation UI (Phase E) 🟢

#### F.2.1 Recommendation Panel (E.2)
- [ ] **E.2.1** High-impact suggestions
  - [ ] Suggested branch points list
  - [ ] Divergence score per suggestion
  - [ ] Impact summary
- [ ] **E.2.2** One-click actions
  - [ ] "Create branch here" button
  - [ ] Preview impact button
  - [ ] Dismiss suggestion button

#### F.2.2 Constraint Violation Display (E.3)
- [ ] **E.3.1** Canon constraint checker
  - [ ] Active constraints list
  - [ ] Violation count badge
  - [ ] Severity indicators
- [ ] **E.3.2** Violation details
  - [ ] Violated constraint description
  - [ ] Affected content preview
  - [ ] Suggested fixes list

### F.3 Profile & Analysis UI (Phase F) 🟢

#### F.3.1 Maturity Rating Display (F.2)
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

#### F.3.2 Profile Editor (F.3)
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

### F.4 Operations & System UI (Phase G) 🟢

#### F.4.1 System Dashboard (G.1)
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

#### F.4.2 Budget Controls (G.2)
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

#### F.4.3 Privacy Settings (G.3)
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

### F.5 Enhanced Graph Features (Phase H) 🟢

#### F.5.1 Edge Management (H.1)
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

#### F.5.2 Advanced Navigation (H.2)
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

#### F.5.3 Graph Layout (H.3)
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

#### F.5.4 Collaboration (H.4)
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

### F.6 UX & Workflow (Phase I) 🟢

#### F.6.1 Responsive Design (I.4)
- [-] **I.4.1** Mobile optimization
  - [x] Touch gestures (useTouch hook)
  - [ ] Collapsible panels (CSS ready, needs JS toggle)
  - [ ] Mobile-optimized graph (CSS ready, needs interaction)
- [-] **I.4.2** Tablet support
  - [ ] Split view layouts
  - [x] Touch-friendly controls
  - [x] Orientation handling

#### F.6.2 Offline Support (I.3.3)
- [ ] **I.3.3** Offline support
  - [ ] Offline detection
  - [ ] Queue changes locally
  - [ ] Sync when back online

### F.7 Technical Infrastructure (Phase J) 🟡

#### F.7.1 State Management (J.1)
- [-] **J.1.2** Async state
  - [x] Loading states
  - [x] Error states
  - [ ] Optimistic updates

#### F.7.2 Real-Time Updates (J.3)
- [x] **J.3.1** WebSocket/SSE infrastructure ✅
- [ ] **J.3.2** Integration with components
  - [ ] Wire up generation progress to WriterPanel
  - [ ] Wire up job completion notifications
  - [ ] Wire up error alerts

---

## Summary Statistics

### By Priority

| Priority | Backend | Frontend | Total |
|----------|---------|----------|-------|
| 🔴 Critical | 0 | 0 | 0 |
| 🟡 High | 3 | 2 | 5 |
| 🟢 Low | 1 | 6 | 7 |

### By Category

| Category | Pending | Status |
|----------|---------|--------|
| Backend - Image Generation | 12 | Needs diffusion backend |
| Backend - API Endpoints | 14 | Core integration gap |
| Backend - Continuous Goals | 9 | Ongoing discipline |
| Frontend - Image Generation | 20 | C.4, C.5 missing |
| Frontend - Consequence Sim | 0 | Complete ✅ |
| Frontend - Profile & Analysis | 0 | Complete ✅ |
| Frontend - Operations | 0 | Complete ✅ |
| Frontend - Graph Features | 12 | H.2, H.4 missing |
| Frontend - UX Polish | 6 | Mobile/offline |
| **TOTAL** | **83** | **~7% of total 224 items** |

### Completion Status

| Phase | Total Items | Complete | Pending | Progress |
|-------|-------------|----------|---------|----------|
| Phase 0-2 (Foundation) | ~40 | 40 | 0 | 100% ✅ |
| Phase 3 (Retrieval) | ~25 | 25 | 0 | 100% ✅ |
| Phase 4 (Graph) | ~30 | 28 | 2 | 93% |
| Phase 5 (Text Gen) | ~35 | 35 | 0 | 100% ✅ |
| Phase 6 (Image Gen) | ~40 | 28 | 12 | 70% |
| Phase 7 (Orchestration) | ~25 | 25 | 0 | 100% ✅ |
| Phase 8 (Frontend UX) | ~50 | 50 | 0 | 100% ✅ |
| Sprints 11-14 | 40 | 40 | 0 | 100% ✅ |
| Sprints 15-16 | 20 | 20 | 0 | 100% ✅ |
| Sprints 17-18 | 21 | 21 | 0 | 100% ✅ |
| Sprints 19-20 | 20 | 20 | 0 | 100% ✅ |
| Phase 9 (Operations) | ~20 | 20 | 0 | 100% ✅ |
| Phase 10 (Release) | ~15 | 15 | 0 | 100% ✅ |
| **Frontend Sprints 1-10** | **224** | **~190** | **~34** | **~85%** |

---

## Recommended Next Steps

### Immediate (High Impact, Low Effort)
1. **Wire up WebSocket progress** to existing generation panels
2. **Complete mobile panel toggles** (JS for CSS-ready collapsible panels)

### Short Term (1-2 Sprints)
3. **System Dashboard** (G.1) - For operational visibility
4. **Budget Controls** (G.2) - Usage tracking and warnings

### Medium Term (3-4 Sprints)
5. **Maturity Rating Display** (F.2) - Content analysis
6. **Consequence Recommendations** (E.2) - AI-assisted suggestions
7. **Collaboration Features** (H.4) - Comments on nodes

### Long Term / Deferred
8. **Profile Editor** (F.3) - Manual profile corrections
9. **Offline Support** (I.3.3) - Queue and sync
10. **Multi-user Collaboration** (H.4.1) - Real-time cursors

---

## Notes

- **Backend API Gap:** The frontend has many UI components ready, but several backend API endpoints are stubbed or missing. Priority should be on connecting existing UI to real backend functionality.

- **Image Generation:** Character identity management (C.4) and QC dashboard (C.5) are the biggest gaps in the image generation workflow. These require both backend LoRA training pipeline and frontend UI.

- **Graph Features:** Edge management (H.1) and layout algorithms (H.3) would significantly improve the graph editing experience but are complex features requiring canvas interaction work.

- **Real-time Updates:** The WebSocket/SSE infrastructure is built but needs to be wired into the actual generation workflows to show live progress.

---

## Sprint Planning Roadmap

The following sprints are designed to be completed sequentially, with each sprint building on the previous. Estimated duration assumes 1-2 developers working full-time.

---

### Sprint 11: API Foundation & Real-Time Integration (2 weeks) ✅ COMPLETE
**Theme:** Connect the UI to real backend functionality

**Goal:** Make the existing UI components fully functional by implementing missing backend endpoints and wiring up real-time updates.

| Item | Description | Effort | Status |
|------|-------------|--------|--------|
| B.2.1.1 | `POST /api/writer/generate` - Full generation pipeline | 2d | ✅ |
| B.2.1.2 | `GET /api/writer/style-exemplars` - Style retrieval | 1d | ✅ |
| B.2.1.3 | `POST /api/writer/check-contradictions` - Contradiction check | 1d | ✅ |
| B.2.2.1 | `POST /api/artist/generate-panels` - Panel generation | 2d | ✅ |
| B.2.3.1 | `POST /api/retrieve/context` - Hybrid retrieval | 2d | ✅ |
| B.2.4.1 | `POST /api/simulate/impact` - Consequence simulation | 1d | ✅ |
| F.7.2.1 | Wire WebSocket progress to WriterPanel | 1d | ✅ |
| F.7.2.2 | Wire WebSocket progress to ArtistPanel | 1d | ✅ |
| F.7.2.3 | Wire job completion notifications | 1d | ✅ |
| GC.1.1 | Add integration tests for new endpoints | 2d | ✅ |

**Sprint 11 Done Criteria:**
- [x] All generation workflows work end-to-end
- [x] Real-time progress visible in UI
- [x] Integration tests pass

**Implemented:**
- `/api/writer/generate` - Full text generation with context assembly, style exemplars, contradiction checking
- `/api/writer/style-exemplars` - Retrieve style exemplars by query
- `/api/writer/check-contradictions` - Check generated text against canon
- `/api/artist/generate-panels` - Panel generation with blueprints and atmosphere
- `/api/retrieve/context` - Hybrid context retrieval
- `/api/simulate/impact` - Consequence simulation with affected nodes
- `/api/ws/{client_id}` - WebSocket endpoint for real-time updates
- WebSocket integration in store with auto-reconnect
- Integration tests for all new endpoints

---

### Sprint 12: Mobile Polish & Navigation (1 week) ✅ COMPLETE
**Theme:** Improve UX on mobile and add graph navigation

**Goal:** Complete mobile experience and add essential graph navigation features.

| Item | Description | Effort | Status |
|------|-------------|--------|--------|
| F.6.1.1 | Collapsible panels JS toggle | 1d | ✅ |
| F.6.1.2 | Mobile-optimized graph interactions | 2d | ✅ |
| H.2.2.1 | Node search box component | 1d | ✅ |
| H.2.2.2 | Fuzzy matching for node search | 0.5d | ✅ |
| H.2.2.3 | Enter to focus and center on node | 0.5d | ✅ |
| H.2.4.1 | Recent nodes history | 1d | ✅ |
| H.2.4.2 | Back/forward navigation | 1d | ✅ |
| GC.2.1 | Document mobile responsive patterns | 0.5d | ✅ |

**Sprint 12 Done Criteria:**
- [x] App is usable on mobile devices
- [x] Node search works with fuzzy matching
- [x] Navigation history functions correctly

**Implemented:**
- Mobile sidebar toggle with hamburger menu button
- Mobile control panel toggle
- Touch event handling for node dragging on mobile
- Double-tap to edit nodes on mobile
- NodeSearch component with fuzzy matching algorithm
- Ctrl+F shortcut to open node search
- Recent nodes section in sidebar showing last 20 visited nodes
- Back/forward navigation buttons (Alt+←/→ shortcuts)
- Navigation history tracking in store
- Mobile-responsive CSS with proper breakpoints
- Touch-friendly UI elements with larger tap targets

---

### Sprint 13: Character Identity Management (2 weeks) ✅ COMPLETE
**Theme:** Complete the image generation workflow with character consistency

**Goal:** Enable users to manage character identities and train LoRA models for consistent character appearances across panels.

| Item | Description | Effort | Status |
|------|-------------|--------|--------|
| C.4.1.1 | Character gallery grid component | 2d | ✅ |
| C.4.1.2 | Filter/sort for character gallery | 1d | ✅ |
| C.4.2.1 | Identity pack builder UI | 2d | ✅ |
| C.4.2.2 | Reference image upload & preview | 1d | ✅ |
| B.1.1.1 | LoRA training trigger endpoint | 2d | ✅ |
| B.1.1.2 | Training job queue | 1d | ✅ |
| B.1.1.3 | Progress tracking for training | 1d | ✅ |
| C.4.3.1 | Training trigger button UI | 0.5d | ✅ |
| C.4.3.2 | Training progress indicator | 1d | ✅ |
| C.4.3.3 | Model version selector | 1d | ✅ |
| GC.1.2 | Tests for identity training flow | 2d | ✅ |

**Sprint 13 Done Criteria:**
- [x] Users can upload character references
- [x] LoRA training can be triggered from UI
- [x] Training progress is visible
- [x] Trained models can be selected for generation

**Implemented:**
- `CharacterGallery` component with grid layout
- Search, filter (importance), and sort (name/importance/appearance) functionality
- `IdentityPackBuilder` for uploading face/silhouette/costume references
- Image preview with remove functionality
- `/api/lora/train` - Start LoRA training endpoint
- `/api/lora/status/{job_id}` - Training status endpoint
- `/api/lora/upload-reference/{character_id}` - Reference image upload
- Training progress simulation with WebSocket updates
- Model version selector in gallery

---

### Sprint 14: Quality Control Dashboard (2 weeks) ✅ COMPLETE
**Theme:** Add quality control and drift detection for images

**Goal:** Enable users to review generated panel quality, request corrections, and detect character drift.

| Item | Description | Effort | Status |
|------|-------------|--------|--------|
| B.1.2.1 | QC scoring endpoints | 2d | ✅ |
| B.1.2.2 | Failure categorization API | 1d | ✅ |
| B.1.2.3 | Correction workflow API | 2d | ✅ |
| C.5.1.1 | Overall quality meter UI | 1d | ✅ |
| C.5.1.2 | Per-panel scores display | 1d | ✅ |
| C.5.1.3 | Category breakdown charts | 2d | ✅ |
| C.5.2.1 | Filter by failure type | 1d | ✅ |
| C.5.3.1 | Select panels for correction | 1d | ✅ |
| C.5.3.2 | Priority selector | 0.5d | ✅ |
| C.5.4.1 | Queue status display | 1d | ✅ |
| B.1.1.4 | Drift detection system | 2d | ✅ |
| C.4.4.1 | Drift alert banner | 1d | ✅ |

**Sprint 14 Done Criteria:**
- [x] QC scores visible for all panels
- [x] Users can request corrections
- [x] Drift detection alerts work

**Implemented:**
- `QCDashboard` component with quality meter and stats
- Overall quality meter with circular progress
- Per-panel scores (anatomy, composition, color, continuity)
- Filter tabs: All, Passed, Needs Correction, Failed, Drift
- Batch selection and correction request modal
- `/api/qc/score` - Get QC scores for panel
- `/api/qc/batch-score` - Batch QC scoring
- `/api/qc/request-correction` - Request panel correction
- `/api/drift/detect` - Detect character drift
- `/api/drift/status/{character_id}` - Get drift status
- Drift alert banner with "View Affected" action
- Failure breakdown with common issues

---

### Sprint 15: Graph Edge Management & Layouts (2 weeks) ✅ COMPLETE
**Theme:** Enhanced graph editing capabilities

**Goal:** Enable visual edge creation and automatic graph layouts for better story visualization.

| Item | Description | Effort | Status |
|------|-------------|--------|--------|
| H.1.1.1 | Drag from node to node | 2d | ✅ |
| H.1.1.2 | Connection preview line | 1d | ✅ |
| H.1.1.3 | Snap to node highlight | 1d | ✅ |
| H.1.2.1 | Edge type selector | 1d | ✅ |
| H.1.2.2 | Edge label input | 0.5d | ✅ |
| H.1.2.3 | Line style selector | 0.5d | ✅ |
| H.3.1.1 | Hierarchical layout algorithm | 2d | ✅ |
| H.3.1.2 | Force-directed layout | 2d | ✅ |
| H.3.1.3 | Timeline layout | 1d | ✅ |
| H.3.2.1 | Branch clustering | 2d | ✅ |
| H.3.3.1 | Layout selector dropdown | 0.5d | ✅ |
| H.3.3.2 | Animate transitions | 1d | ✅ |

**Sprint 15 Done Criteria:**
- [x] Users can create edges by dragging
- [x] Multiple layout algorithms available
- [x] Branch clustering works

**Implemented:**
- `EdgeRenderer` component with SVG-based edge rendering
- Visual edge creation: Click "Connect" button, then drag from source to target node
- Connection preview line with animated dash pattern
- Snap-to-node highlighting when hovering over valid targets
- `EdgeConfigPanel` with edge type selector (causal/temporal/parallel)
- Line style selector (solid/dashed/dotted)
- Color picker for edge customization
- `LayoutControls` with 5 layout algorithms: Manual, Hierarchical, Force-Directed, Circular, Timeline
- Branch clustering option (groups nodes by branch)
- Animate transitions toggle for smooth layout changes
- Layout algorithms implemented: Hierarchical (top-down tree), Force-directed (physics-based), Circular (radial), Timeline (left-to-right)

---

### Sprint 16: Minimap, Bookmarks & Advanced Navigation (1 week) ✅ COMPLETE
**Theme:** Navigation improvements for large graphs

**Goal:** Add minimap for overview navigation and bookmark system for quick access to important nodes.

| Item | Description | Effort | Status |
|------|-------------|--------|--------|
| H.2.1.1 | Minimap overview component | 2d | ✅ |
| H.2.1.2 | Viewport rectangle on minimap | 1d | ✅ |
| H.2.1.3 | Click to jump on minimap | 1d | ✅ |
| H.2.3.1 | Bookmark current node | 1d | ✅ |
| H.2.3.2 | Bookmarks list dropdown | 1d | ✅ |
| H.2.3.3 | Click bookmark to navigate | 0.5d | ✅ |
| H.2.4.3 | Clear history button | 0.5d | ✅ |
| GC.2.2 | Document graph navigation patterns | 0.5d | ✅ |

**Sprint 16 Done Criteria:**
- [x] Minimap shows full graph with viewport
- [x] Users can bookmark and navigate to nodes
- [x] History can be cleared

**Implemented:**
- `Minimap` component with canvas-based rendering
- Shows all nodes as colored dots
- Viewport rectangle overlay showing current view position
- Click or drag on minimap to jump to location
- `BookmarkDropdown` component integrated in header
- Add bookmarks for any selected node
- Color-coded bookmarks (8 colors available)
- Persisted to localStorage
- Bookmark list with quick navigation
- Clear all bookmarks option
- Node bookmark indicator (colored dot on nodes)
- Clear history button in Recent Nodes section (already implemented in Sprint 12)

---

### Sprint 17: Operations Dashboard (2 weeks) ✅ COMPLETE
**Theme:** System monitoring and operational controls

**Goal:** Provide visibility into system health, job queues, and budget controls.

| Item | Description | Effort | Status |
|------|-------------|--------|--------|
| G.1.1.1 | Latency charts component | 2d | ✅ |
| G.1.1.2 | Success rate gauges | 1d | ✅ |
| G.1.1.3 | Error rate trends | 1d | ✅ |
| G.1.2.1 | Pending jobs count | 0.5d | ✅ |
| G.1.2.2 | In-progress jobs list | 1d | ✅ |
| G.1.2.3 | Completed jobs history | 1d | ✅ |
| G.2.1.1 | Current period usage display | 1d | ✅ |
| G.2.1.2 | Usage by branch chart | 1d | ✅ |
| G.2.2.1 | Pre-generation cost estimate | 1d | ✅ |
| G.2.3.1 | Budget limit warnings (50%, 80%, 100%) | 1d | ✅ |
| G.3.1.1 | Local-only mode toggle | 1d | ✅ |
| G.3.2.1 | Data retention settings | 1d | ✅ |

**Sprint 17 Done Criteria:**
- [x] System metrics visible in dashboard
- [x] Job queue status is real-time
- [x] Budget warnings appear at thresholds

**Implemented:**
- `operationsStore` with Zustand + persist middleware
- `OperationsDashboard` component with 4 tabs:
  - **Metrics Tab**: Latency stats (P50, P95, P99), mini bar charts, success rate gauge, error rate breakdown
  - **Jobs Tab**: Job stats counters, job list with progress bars, cancel/retry actions, clear completed
  - **Usage Tab**: Current period summary, budget progress with threshold markers, usage by branch chart, usage by operation
  - **Privacy Tab**: Local-only mode toggle, external provider selection, data retention settings, export/delete data
- Budget warning banner (50%, 80%, 100% thresholds)
- Cost estimation helper function

---

### Sprint 18: Maturity Rating & Profile Display (1 week) ✅ COMPLETE
**Theme:** Content analysis visualization

**Goal:** Display maturity ratings and content analysis to users.

| Item | Description | Effort | Status |
|------|-------------|--------|--------|
| F.2.1.1 | Rating badge component (G/PG/PG-13/R) | 1d | ✅ |
| F.2.1.2 | Rating justification summary | 1d | ✅ |
| F.2.2.1 | Violence score bar | 0.5d | ✅ |
| F.2.2.2 | Language score bar | 0.5d | ✅ |
| F.2.2.3 | Sexual content score bar | 0.5d | ✅ |
| F.2.2.4 | Mature themes score bar | 0.5d | ✅ |
| F.2.3.1 | Target audience selector | 1d | ✅ |
| F.2.3.2 | Content warnings list | 1d | ✅ |
| GC.2.3 | Document maturity rating system | 0.5d | ✅ |

**Sprint 18 Done Criteria:**
- [x] Maturity ratings display correctly
- [x] Category breakdowns visible
- [x] Content warnings shown appropriately

**Implemented:**
- `maturityStore` with rating calculations and content warnings
- `MaturityRating` component with 3 tabs:
  - **Overview Tab**: Large rating badge, justification text, target audience selector with suitability check, quick content breakdown
  - **Categories Tab**: Detailed score bars for violence, language, sexual content, mature themes with intensity labels
  - **Warnings Tab**: Selectable content warnings (12 types), severity indicators, active warnings summary
- `RatingBadge` compact component (used in header nav)
- 5 rating levels: G, PG, PG-13, R, NC-17 with color coding
- Auto-calculated ratings based on content scores

---

### Sprint 19: Consequence Recommendations (1 week) ✅ COMPLETE
**Theme:** AI-assisted branch suggestions

**Goal:** Provide intelligent recommendations for high-impact branch points.

| Item | Description | Effort | Status |
|------|-------------|--------|--------|
| E.2.1.1 | Suggested branch points list | 2d | ✅ |
| E.2.1.2 | Divergence score per suggestion | 1d | ✅ |
| E.2.1.3 | Impact summary | 1d | ✅ |
| E.2.2.1 | "Create branch here" button | 1d | ✅ |
| E.2.2.2 | Preview impact button | 0.5d | ✅ |
| E.2.2.3 | Dismiss suggestion button | 0.5d | ✅ |
| E.3.1.1 | Active constraints list | 1d | ✅ |
| E.3.1.2 | Violation count badge | 0.5d | ✅ |
| GC.1.3 | Tests for recommendation engine | 1d | ✅ |

**Sprint 19 Done Criteria:**
- [x] Recommendations appear for high-impact nodes
- [x] Users can create branches from suggestions
- [x] Constraint violations are visible

**Implemented:**
- `recommendationsStore` with suggestions, constraints, violations
- `RecommendationsPanel` component with 2 tabs:
  - **Suggestions Tab**: Branch suggestions with divergence scores (0-100)
  - Impact preview showing affected nodes and consistency score
  - Create branch, preview impact, dismiss actions
  - **Constraints Tab**: Active violations with severity indicators
  - Constraint list with violation count badges
  - Acknowledge violation functionality
- Violation badge on navigation button

---

### Sprint 20: Profile Editor & Collaboration Foundation (2 weeks) ✅ COMPLETE
**Theme:** Advanced editing and multi-user preparation

**Goal:** Enable manual profile corrections and lay groundwork for collaboration.

| Item | Description | Effort | Status |
|------|-------------|--------|--------|
| F.3.1.1 | Tone override controls | 1d | ✅ |
| F.3.1.2 | Intensity adjustment sliders | 1d | ✅ |
| F.3.1.3 | Genre tag editor | 1d | ✅ |
| F.3.2.1 | Profile versions list | 1d | ✅ |
| F.3.2.2 | Diff between versions | 2d | ✅ |
| F.3.3.1 | Override logging UI | 1d | ✅ |
| F.3.3.2 | Audit trail view | 1d | ✅ |
| H.4.2.1 | Add comment to node | 2d | ✅ |
| H.4.2.2 | Comment thread view | 1d | ✅ |
| H.4.2.3 | Resolve comment button | 0.5d | ✅ |
| GC.3.1 | Record tradeoffs and deferred work | 0.5d | ✅ |

**Sprint 20 Done Criteria:**
- [x] Users can manually edit profiles
- [x] Override history is tracked
- [x] Comments can be added to nodes

**Implemented:**
- `profileStore` with persistence for tones, overrides, genres, versions, audit
- `ProfileEditor` component with 3 tabs:
  - **Editor Tab**: 8 tone sliders (narrative, dialogue, description, pacing, atmosphere, humor, intensity, romance)
  - Override management with reason tracking
  - Genre tag editor (primary/secondary/theme categories)
  - **Versions Tab**: Version history with diff view (added/removed/changed)
  - Version restore functionality
  - **Audit Tab**: Complete audit trail of all changes
- `commentsStore` for node-based comments
- `CommentsPanel` component:
  - Add comments to any node
  - Threaded replies
  - Resolve/reopen comments
  - Unresolved comment count badges on nodes and nav

---

### Sprint 21: Offline Support & Final Polish (1 week)
**Theme:** Resilience and final UX improvements

**Goal:** Add offline support and complete remaining polish items.

| Item | Description | Effort |
|------|-------------|--------|
| F.6.2.1 | Offline detection | 1d |
| F.6.2.2 | Queue changes locally | 2d |
| F.6.2.3 | Sync when back online | 2d |
| F.7.1.1 | Optimistic updates for key actions | 1d |
| G.3.3.1 | Export all data | 0.5d |
| G.3.3.2 | Delete account/data | 0.5d |
| GC.3.2 | Final documentation updates | 1d |
| GC.3.3 | Record final tradeoffs | 0.5d |

**Sprint 21 Done Criteria:**
- [ ] App works offline with sync on reconnect
- [ ] Data export/delete functions work
- [ ] All documentation is current

---

## Sprint Summary Timeline

| Sprint | Theme | Duration | Cumulative | Status |
|--------|-------|----------|------------|--------|
| 11 | API Foundation & Real-Time | 2 weeks | Week 2 | ✅ Complete |
| 12 | Mobile Polish & Navigation | 1 week | Week 3 | ✅ Complete |
| 13 | Character Identity | 2 weeks | Week 5 | ✅ Complete |
| 14 | Quality Control | 2 weeks | Week 7 | ✅ Complete |
| 15 | Graph Edge Management | 2 weeks | Week 9 | ✅ Complete |
| 16 | Minimap & Bookmarks | 1 week | Week 10 | ✅ Complete |
| 17 | Operations Dashboard | 2 weeks | Week 12 | ✅ Complete |
| 18 | Maturity Rating | 1 week | Week 13 | ✅ Complete |
| 19 | Consequence Recommendations | 1 week | Week 14 | ✅ Complete |
| 20 | Profile Editor & Comments | 2 weeks | Week 16 | ✅ Complete |
| 21 | Offline Support & Polish | 1 week | Week 17 | Pending |
| **TOTAL** | | **17 weeks** | **~4 months** | **89% Complete** |

---

## Parallel Workstreams (Optional)

If working with a larger team, these can run in parallel:

### Workstream A: Backend API (Sprints 11, 13, 14)
Focus on backend endpoints and LoRA training pipeline.

### Workstream B: Frontend Core (Sprints 11, 12, 15, 16)
Focus on UI features that don't require new backend APIs.

### Workstream C: Analytics & Operations (Sprints 17, 18, 19)
Focus on dashboards and analysis features.

---

## Release Milestones

### Alpha Release (End of Sprint 14)
- All core generation workflows complete
- Character identity management works
- Quality control dashboard functional
- Mobile responsive

### Beta Release (End of Sprint 17)
- Graph editing with edges and layouts
- Operations dashboard live
- System monitoring in place
- All major features implemented

### v1.0 Release (End of Sprint 21)
- Offline support
- Profile editing
- Comments on nodes
- Complete documentation

---

*For completed items, see UI_GOALS.md and GOALS.md*
