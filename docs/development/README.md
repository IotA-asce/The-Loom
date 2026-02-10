# Development Documentation

This directory contains development guides and goal tracking for The Loom.

## Sprint Completion Status

### Frontend Sprints (1-21) ✅ Complete

| Sprint | Feature | Key Deliverables |
|--------|---------|------------------|
| 1-10 | Foundation | Graph, Panels, Editor, Search, Import, DualView, Tuner |
| 11 | API Foundation | Backend endpoints, WebSocket, Progress tracking |
| 12 | Mobile Polish | Responsive panels, Touch events, NodeSearch, History |
| 13 | Character Identity | CharacterGallery, LoRA training UI |
| 14 | QC Dashboard | Quality scoring, Failure categorization, Drift detection |
| 15 | Graph Edge Management | EdgeRenderer, LayoutControls, 5 algorithms |
| 16 | Minimap & Bookmarks | Viewport navigation, Bookmark system |
| 17 | Operations Dashboard | System metrics, Job queue, Budget controls |
| 18 | Maturity Rating | Rating badges, Content warnings, Target audience |
| 19 | Recommendations | AI branch suggestions, Constraints, Impact preview |
| 20 | Profile Editor | Tone controls, Genre tags, Version history, Comments |
| 21 | Offline Support | Action queue, Sync management, Optimistic updates |

**Total: 224 UI items, 30 components, 14 stores**

### Backend Sprints (22-30) ✅ Complete

| Sprint | Feature | Key Deliverables |
|--------|---------|------------------|
| 22 | LLM Integration | Gemini, OpenAI, Anthropic, Ollama support |
| 23 | Vector Database | ChromaDB, hybrid search, embeddings |
| 24 | Diffusion Backend | Local SD, Stability AI, ControlNet |
| 25 | Character LoRA | LoRA training, identity packs |
| 26 | QC Pipeline | Anatomy/composition scoring, auto-redraw |
| 27 | Graph Persistence | SQLite graph DB, event sourcing |
| 28 | Collaboration | Real-time rooms, cursors, edit locks |
| 29 | Observability | Metrics, SLOs, structured logging |
| 30 | Security | JWT auth, RBAC, rate limiting, Docker |

## Development Guidelines

### Code Style
- Python: Black formatter, Ruff linter
- TypeScript: ESLint + Prettier
- Follow existing patterns in the codebase

### Testing
- Write tests for new features
- Maintain >80% coverage
- Run `make lint && make test` before committing

### Commits
- Use conventional commits: `feat:`, `fix:`, `docs:`, etc.
- Keep commits focused and atomic

## Documents

- **[GOALS.md](./GOALS.md)** - Original project goals and vision
- **[UI_GOALS.md](./UI_GOALS.md)** - Detailed frontend sprint tracking
- **[BACKEND_GOALS.md](./BACKEND_GOALS.md)** - Detailed backend sprint tracking

## Getting Started

See the main [README](../../README.md) for setup instructions.

---

For questions, refer to [AGENTS.md](../../AGENTS.md) for AI coding guidelines.
