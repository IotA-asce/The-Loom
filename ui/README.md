# The Loom UI - Phase 8 Frontend

Interactive frontend for The Loom storytelling framework with branching narrative visualization and dual-view editing.

## Features

### G8.1: Interactive Graph UX
- **Node graph rendering** with virtualization for large graphs
- **Semantic zoom modes**: Overview, Scene, Detail
- **Undo/redo** with full history stack
- **Autosave checkpoints** for recovery

### G8.2: Branching Workflow UX
- **Branch creation** from any selected node
- **Impact preview** showing downstream effects
- **Branch lineage** visualization
- **Archive/merge** actions

### G8.3: Tuner and Control Panel
- **Violence/Humor/Romance sliders** with calibrated curves
- **Precedence rules** for conflicting settings
- **Warnings** for extreme settings
- **Impact preview** showing expected tone

### G8.4: Dual-view and Director Mode
- **Text + Manga split view**
- **Sync status badges** with non-color indicators
- **Sentence edit** workflow
- **Panel redraw** requests
- **Reconcile actions**

### G8.5: Accessibility and Mobile Readiness
- **Keyboard shortcuts** for all critical actions
- **Semantic labels** for assistive technologies
- **Responsive layouts** for mobile and tablet
- **Non-color indicators** for state changes

## Architecture

```
ui/
├── api.py              # FastAPI backend API
├── src/
│   ├── components/     # React components
│   │   ├── GraphCanvas.tsx      # Virtualized graph view
│   │   ├── BranchPanel.tsx      # Branch management
│   │   ├── TunerPanel.tsx       # Tuner controls
│   │   ├── DualView.tsx         # Dual-view editor
│   │   └── StatusBar.tsx        # Status indicators
│   ├── store.ts        # Zustand state management
│   ├── types/          # TypeScript definitions
│   └── ...
└── package.json
```

## Development

### Prerequisites
- Node.js 18+
- Python 3.12+ (for API)

### Setup

```bash
# Install frontend dependencies
cd ui
npm install

# Install API dependencies (from project root)
pip install fastapi uvicorn pydantic
```

### Running

```bash
# Start the API (from project root)
python -m ui.api

# Start the frontend (in another terminal, from ui/)
npm run dev
```

The UI will be available at `http://localhost:3000` with API proxy to `http://localhost:8000`.

### Build

```bash
npm run build
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+T | Toggle Tuner Panel |
| Ctrl+D | Toggle Dual View |
| Ctrl+S | Save Checkpoint |
| Ctrl++ | Zoom In |
| Ctrl+- | Zoom Out |

## API Endpoints

### Graph
- `GET /api/graph/metrics` - Render metrics
- `POST /api/graph/nodes` - Create node
- `POST /api/graph/viewport` - Update viewport
- `POST /api/graph/undo` - Undo operation
- `POST /api/graph/redo` - Redo operation

### Branches
- `GET /api/branches` - List branches
- `POST /api/branches` - Create branch
- `GET /api/branches/impact/{node_id}` - Impact preview
- `POST /api/branches/archive` - Archive branch
- `POST /api/branches/merge` - Merge branches

### Tuner
- `POST /api/tuner/resolve` - Resolve tuner settings

### Dual View
- `POST /api/dualview/initialize` - Initialize sync state
- `POST /api/dualview/sentence-edit` - Edit sentence
- `POST /api/dualview/panel-redraw` - Request redraw
- `POST /api/dualview/reconcile` - Reconcile versions

### Phase 8 Metrics
- `GET /api/phase8/metrics` - Complete Phase 8 metrics
