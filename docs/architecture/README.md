# Architecture Documentation

This directory contains high-level architecture documents for The Loom.

## Documents

### PRD.md - Product Requirements Document
The original product requirements defining what The Loom should do, including:
- Core features and capabilities
- User stories and personas
- Functional requirements
- Non-functional requirements

### STRATEGY.md - Technical Strategy
Technical decisions and architectural strategy:
- Technology stack choices
- Design patterns
- Integration strategies
- Security considerations

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  React + TypeScript + Vite                                  │
│  ├─ Graph Editor (React Flow)                               │
│  ├─ Dual-View Editor                                        │
│  ├─ Panel Studio                                            │
│  └─ Real-time Collaboration                                 │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / WebSocket
┌────────────────────────┼────────────────────────────────────┐
│                        Backend                               │
│  FastAPI + Python 3.12                                     │
│  ├─ Authentication (JWT + RBAC)                            │
│  ├─ Graph API                                             │
│  ├─ Generation API (Writer + Artist)                      │
│  ├─ Collaboration Engine                                  │
│  └─ Observability (Metrics + Logs)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                        Data Layer                            │
│  ├─ SQLite (Graph persistence + Event sourcing)            │
│  ├─ ChromaDB (Vector search)                               │
│  └─ Filesystem (Images + Assets)                           │
└─────────────────────────────────────────────────────────────┘
```

## Backend Sprint Completion

| Sprint | Feature | Status |
|--------|---------|--------|
| 22 | LLM Integration | ✅ Complete |
| 23 | Vector Database | ✅ Complete |
| 24 | Diffusion Backend | ✅ Complete |
| 25 | Character LoRA | ✅ Complete |
| 26 | QC Pipeline | ✅ Complete |
| 27 | Graph Persistence | ✅ Complete |
| 28 | Collaboration | ✅ Complete |
| 29 | Observability | ✅ Complete |
| 30 | Security & Docker | ✅ Complete |

## Design Principles

1. **Local-First**: Core functionality works without external APIs
2. **Modular**: Each AI provider is swappable
3. **Observable**: Everything is measured and logged
4. **Secure**: Auth, rate limiting, input validation
5. **Collaborative**: Real-time multi-user editing

---

See [Backend Goals](../development/BACKEND_GOALS.md) for detailed sprint information.
