# Changelog

All notable changes to The Loom project.

## [1.0.0] - 2026-02-10

### Sprint 30: Security & Production Hardening ✅

#### Added
- **Authentication & Authorization**
  - JWT token-based authentication (access + refresh tokens)
  - Role-based access control (RBAC): Admin, Editor, Viewer, Service
  - Password hashing with salt
  - Project-level permissions
  - API key management for service accounts
  
- **Rate Limiting**
  - Token bucket algorithm implementation
  - Per-endpoint categories: auth, generate, api, websocket
  - Per-client tracking with headers
  - Configurable limits per category
  
- **Docker Deployment**
  - Multi-stage Dockerfile with security hardening
  - Docker Compose with optional Redis, Prometheus, Grafana
  - Non-root user execution
  - Health checks

#### API Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - Logout & revoke token
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Current user info
- `POST /api/auth/api-keys` - Create API key
- `GET /api/auth/api-keys` - List API keys
- `DELETE /api/auth/api-keys/{id}` - Revoke API key
- `GET /api/auth/rate-limit` - Rate limit status

---

## [0.9.0] - 2026-02-10

### Sprint 29: Observability/Monitoring ✅

#### Added
- **Metrics Collection**
  - Counter, gauge, and histogram metrics
  - Request latency tracking (p50, p95, p99)
  - Error rate tracking
  - Generation success/failure rates
  - Token usage tracking
  
- **SLO Tracking**
  - Availability target: 99.9%
  - Latency p95 target: 500ms
  - Error rate target: 0.1%
  - SLO status endpoints
  
- **Health Checks**
  - Component health monitoring
  - Overall system status
  - Response time tracking
  
- **Structured Logging**
  - Correlation ID support
  - Log level filtering
  - Contextual log entries

#### API Endpoints
- `GET /api/ops/metrics` - System metrics (JSON)
- `GET /api/ops/metrics/prometheus` - Prometheus format
- `GET /api/ops/slos` - SLO status
- `GET /api/ops/health` - Health check
- `GET /api/ops/logs` - Recent log entries

---

## [0.8.0] - 2026-02-10

### Sprint 28: Real-time Collaboration ✅

#### Added
- **Collaboration Rooms**
  - Room-based WebSocket sessions
  - User presence tracking
  - Automatic color assignment (10 colors)
  
- **Cursor & Selection**
  - Real-time cursor position broadcasting
  - Node selection indicators
  - Selection sync across clients
  
- **Edit Locks**
  - Node-level edit locking
  - 5-minute lock timeout
  - Automatic lock release on disconnect
  
- **Event Broadcasting**
  - User join/leave events
  - Lock/unlock notifications
  - Change events

#### API Endpoints
- `POST /api/collaboration/join` - Join collaboration room
- `POST /api/collaboration/leave` - Leave room
- `POST /api/collaboration/cursor` - Update cursor position
- `POST /api/collaboration/select` - Select node
- `POST /api/collaboration/lock` - Acquire edit lock
- `POST /api/collaboration/unlock` - Release edit lock
- `GET /api/collaboration/presence/{room_id}` - Get presence state

---

## [0.7.0] - 2026-02-10

### Sprint 27: Graph Persistence & Event Sourcing ✅

#### Added
- **Graph Database**
  - SQLite-backed graph persistence
  - Node/Edge CRUD operations
  - Branch lineage tracking
  - JSON metadata support
  
- **Event Sourcing**
  - Event store with SQLite backend
  - Event types: NODE_CREATED, TEXT_EDITED, PANEL_GENERATED, etc.
  - Audit trail generation
  - Event replay for state reconstruction
  
- **Project Management**
  - Project save/load
  - JSON export/import
  - Transaction support

#### API Endpoints
- `POST /api/graph/nodes/save` - Save node
- `GET /api/graph/nodes/{id}` - Get node
- `DELETE /api/graph/nodes/{id}` - Delete node
- `GET /api/graph/nodes` - List nodes
- `POST /api/graph/edges/save` - Save edge
- `GET /api/graph/edges` - List edges
- `POST /api/project/save` - Save project
- `GET /api/project/load/{id}` - Load project
- `POST /api/project/export` - Export project
- `GET /api/events/audit/{type}/{id}` - Get audit trail
- `GET /api/events/recent` - Activity feed

---

## [0.6.0] - 2026-02-10

### Sprint 26: Quality Control Pipeline ✅

#### Added
- **QC Analysis**
  - Anatomy scoring (proportions, pose, hands, face)
  - Composition scoring (rule of thirds, balance, focal point)
  - Readability scoring (contrast, clarity, legibility)
  - Content flags (NSFW detection)
  
- **Scoring Levels**
  - EXCELLENT (0.9+), GOOD (0.7+), ACCEPTABLE (0.5+)
  - POOR (0.3+), REJECT (<0.3)
  
- **Auto-Redraw**
  - Automatic retry on QC failure
  - Configurable retry attempts
  - Best image selection

#### API Endpoints
- `POST /api/qc/analyze` - Analyze image quality
- `GET /api/qc/analyzers` - List available analyzers
- `GET /api/qc/reports/{image_id}` - Get detailed QC report
- `POST /api/qc/auto-redraw` - Auto-redraw failed images

---

## [0.5.0] - 2026-02-09

### Sprints 24-25: Image Generation & Character LoRA ✅

#### Added
- **Diffusion Backends**
  - Local Stable Diffusion with ControlNet
  - Stability AI cloud API
  - Mock backend for testing
  - Backend auto-detection
  
- **Image Storage**
  - Local filesystem storage
  - JSON metadata tracking
  - Image versioning
  
- **LoRA Training**
  - Character identity packs
  - Training job management
  - Progress tracking
  - Adapter versioning

#### API Endpoints
- `GET /api/diffusion/backends` - List available backends
- `POST /api/diffusion/config` - Configure backend
- `POST /api/artist/generate` - Generate and store panels
- `GET /api/images/{image_id}` - Serve image
- `GET /api/images/{image_id}/metadata` - Get metadata
- `DELETE /api/images/{image_id}` - Delete image
- `GET /api/images` - List images
- `POST /api/lora/train` - Start LoRA training
- `GET /api/lora/status/{job_id}` - Check training status
- `POST /api/characters/identity-pack` - Build identity pack

---

## [0.4.0] - 2026-02-08

### Sprints 22-23: LLM Integration & Vector Database ✅

#### Added
- **LLM Backends**
  - Gemini (Google)
  - OpenAI (GPT-4, GPT-3.5)
  - Anthropic (Claude)
  - Ollama (local models)
  - Fallback chain support
  
- **Vector Store**
  - ChromaDB integration
  - Hybrid search (vector + BM25)
  - OpenAI embeddings
  - HuggingFace embeddings

#### API Endpoints
- `GET /api/llm/providers` - List available providers
- `POST /api/llm/config` - Configure LLM backend
- `POST /api/llm/test` - Test LLM connection
- `POST /api/writer/generate` - Generate text
- `POST /api/index/build` - Build vector index
- `GET /api/index/stats` - Index statistics
- `POST /api/retrieve/vector-search` - Hybrid semantic search

---

## [0.3.0] - 2026-02-01

### Sprint 11: API Foundation ✅

#### Added
- FastAPI backend setup
- WebSocket support for real-time updates
- Progress tracking endpoints
- Async job handling

---

## [0.2.0] - 2026-01-25

### Sprints 1-10: Frontend Foundation ✅

#### Added
- React + TypeScript + Vite setup
- Graph editor with React Flow
- Panel studio for manga layout
- Dual-view editor (text + visual)
- Node search with filtering
- Branch timeline visualization
- Tuner controls for generation
- Story import functionality

---

## [0.1.0] - 2026-01-15

### Project Initialization

#### Added
- Project structure
- Core engine scaffolding
- Agent framework
- Documentation framework

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

---

## Contributing Changes

When adding to this changelog:

1. Add new entries at the top
2. Use the format: `### Category` then `- Description`
3. Reference issue/PR numbers when applicable
4. Mark breaking changes clearly
