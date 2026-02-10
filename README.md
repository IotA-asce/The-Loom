# The Loom 🧵

[![CI](https://github.com/IotA-asce/The-Loom/actions/workflows/ci.yml/badge.svg)](https://github.com/IotA-asce/The-Loom/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> *Weaving infinite timelines from existing stories.*

**The Loom** is a full-stack storytelling framework for branching narratives with AI-generated prose and manga. Analyze source stories, create alternate timelines, collaborate in real-time, and produce professional-quality content with coordinated AI agents.

---

## ✨ Features Overview

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **📚 Multi-Format Ingestion** | Parse `.txt`, `.pdf`, `.epub`, `.cbz`, and loose image folders |
| **🎭 Tone Preservation** | Replicate any genre—from children's tales to visceral fiction |
| **🌳 Branching Narratives** | Visual "Tree of Possibilities" with drag-and-drop graph editor |
| **✍️ Prose Generation** | Style-faithful text with character voice integrity |
| **🎨 Manga Generation** | Panel sequences with atmosphere control and LoRA character consistency |
| **👥 Real-time Collaboration** | Multi-user editing with cursors, presence, and edit locks |
| **🔄 State Integrity** | Event sourcing, audit trails, and cross-modal sync |
| **🔒 Security First** | JWT auth, RBAC, rate limiting, and Docker deployment |
| **📊 Observability** | Prometheus metrics, SLO tracking, structured logging |

### Technology Stack

**Frontend (Sprints 1-21)**
- React 18 + TypeScript + Vite
- Zustand state management (14 stores)
- React Flow for graph visualization
- Tailwind CSS + Radix UI

**Backend (Sprints 22-30)**
- FastAPI with WebSocket support
- SQLite with event sourcing
- ChromaDB for vector search
- JWT authentication + RBAC

**AI/ML**
- LLM: Gemini, OpenAI, Anthropic, Ollama
- Image: Local Stable Diffusion, Stability AI
- Embeddings: OpenAI, HuggingFace
- Quality Control: CLIP-based scoring

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+ (for UI)
- (Optional) GPU for local image generation

### Installation

```bash
# Clone the repository
git clone https://github.com/IotA-asce/The-Loom.git
cd The-Loom

# Backend setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ui
npm install
cd ..
```

### Configuration

```bash
# Set your API keys (at least one LLM provider)
export GEMINI_API_KEY="your-key"          # Recommended
export OPENAI_API_KEY="your-key"          # Alternative
export ANTHROPIC_API_KEY="your-key"       # Alternative

# Optional: Image generation
export STABILITY_API_KEY="your-key"       # Cloud option

# Optional: Security
export JWT_SECRET="your-secret-key"       # Production only
```

### Running Locally

```bash
# Terminal 1: Start backend
source .venv/bin/activate
python -m ui.api

# Terminal 2: Start frontend
cd ui
npm run dev
```

Open http://localhost:5173 (frontend) and http://localhost:8000/docs (API docs).

### Docker Deployment

```bash
# Production deployment
docker-compose up -d

# With monitoring (Prometheus + Grafana)
docker-compose --profile monitoring up -d
```

---

## 📖 Usage Guide

### 1. Ingest a Story

```python
from agents.archivist import ingest_text_file

result = ingest_text_file("path/to/story.txt")
print(f"Ingested {result.chunk_count} chunks")
```

### 2. Create a Branch Timeline

```python
from core.story_graph_engine import BranchLifecycleManager

manager = BranchLifecycleManager()
manager.create_root_branch("main")

# Create an alternate timeline
branch = manager.create_divergence_node(
    parent_branch_id="main",
    divergence_event_id="evt-001",
    label="What if the hero failed?"
)
```

### 3. Generate Content

```python
from core.text_generation_engine import WriterEngine
from core.llm_backend import LLMRequest, LLMMessage

engine = WriterEngine()

request = LLMRequest(
    messages=(
        LLMMessage(role="system", content="You are a fantasy writer."),
        LLMMessage(role="user", content="Write a battle scene."),
    ),
    temperature=0.7,
)

response = await engine.generate(request)
print(response.content)
```

### 4. Generate Manga Panels

```python
from core.image_generation_engine import (
    generate_and_store_panels,
    SceneBlueprint,
    AtmospherePreset,
)

blueprint = SceneBlueprint(
    setting="Medieval castle courtyard",
    time_of_day="dusk",
    lighting_direction="side",
)

panels = await generate_and_store_panels(
    story_id="story-001",
    scene_id="scene-001",
    blueprint=blueprint,
    atmosphere=AtmospherePreset.TENSE,
    num_panels=4,
)
```

### 5. Real-time Collaboration

```python
from core.collaboration import get_collaboration_engine

engine = get_collaboration_engine()

# Join room
room, presence = await engine.join_room(
    room_id="story-001",
    user_id="user-123",
    user_name="Alice"
)

# Update cursor
await engine.update_cursor(
    room_id="story-001",
    user_id="user-123",
    x=100.5,
    y=200.0
)

# Lock node for editing
success, error = await engine.acquire_edit_lock(
    room_id="story-001",
    node_id="node-456",
    user_id="user-123",
    user_name="Alice"
)
```

### 6. Authentication

```python
from core.auth import get_auth_manager, UserRole

auth = get_auth_manager()

# Register user
user = auth.create_user(
    email="alice@example.com",
    username="alice",
    password="secure-password",
    role=UserRole.EDITOR
)

# Login
token = auth.create_access_token(user)
```

---

## 🏗️ Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐ │
│  │ Graph   │ │ Editor  │ │ Search  │ │  Tuner  │ │  Panels  │ │
│  │ Editor  │ │ (Dual)  │ │         │ │ Controls│ │          │ │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬─────┘ │
│       └─────────────┴───────────┴───────────┴───────────┘       │
│                         Zustand Stores                           │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP / WebSocket
┌─────────────────────────────┼───────────────────────────────────┐
│                         Backend (FastAPI)                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐ │
│  │  Auth   │ │  Graph  │ │ Generate│ │  Vector │ │   Ops    │ │
│  │ (JWT)   │ │   API   │ │   API   │ │ Search  │ │ Monitoring│ │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬─────┘ │
│       └─────────────┴───────────┴───────────┴───────────┘       │
│                         Core Engine                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                         AI Backends                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐ │
│  │ Gemini  │ │ OpenAI  │ │Anthropic│ │ Local   │ │ Stability│ │
│  │         │ │         │ │         │ │    SD   │ │    AI    │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └──────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                         Data Layer                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐ │
│  │   SQLite    │ │  ChromaDB   │ │   Events    │ │  Images  │ │
│  │  (Graph)    │ │  (Vectors)  │ │   (Audit)   │ │ (Storage)│ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Core Modules

| Module | Purpose |
|--------|---------|
| `core/auth.py` | JWT authentication, RBAC, API keys |
| `core/rate_limit.py` | Token bucket rate limiting |
| `core/collaboration.py` | Real-time collaboration |
| `core/observability.py` | Metrics, logging, SLOs |
| `core/llm_backend.py` | Unified LLM interface |
| `core/vector_store.py` | Semantic search with ChromaDB |
| `core/diffusion_backend.py` | Image generation backends |
| `core/image_storage.py` | Image persistence |
| `core/graph_persistence.py` | SQLite graph database |
| `core/event_store.py` | Event sourcing layer |
| `core/qc_analysis.py` | Quality control pipeline |
| `core/text_generation_engine.py` | Writer engine |
| `core/image_generation_engine.py` | Artist engine |

---

## 🔌 API Reference

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Create new account |
| `/api/auth/login` | POST | Get access token |
| `/api/auth/logout` | POST | Revoke token |
| `/api/auth/refresh` | POST | Refresh access token |
| `/api/auth/me` | GET | Current user info |

### Graph Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/graph/nodes` | GET/POST | List/create nodes |
| `/api/graph/nodes/{id}` | GET/DELETE | Get/delete node |
| `/api/graph/edges` | GET/POST | List/create edges |
| `/api/graph/persist` | POST | Save full graph |

### Content Generation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/writer/generate` | POST | Generate prose |
| `/api/artist/generate` | POST | Generate panels |
| `/api/lora/train` | POST | Train character LoRA |
| `/api/qc/analyze` | POST | Analyze image quality |

### Collaboration

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/collaboration/join` | POST | Join room |
| `/api/collaboration/cursor` | POST | Update cursor |
| `/api/collaboration/lock` | POST | Acquire edit lock |
| `/api/ws/{client_id}` | WS | WebSocket connection |

### Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ops/metrics` | GET | System metrics |
| `/api/ops/health` | GET | Health check |
| `/api/ops/slos` | GET | SLO status |

Full API documentation available at `/docs` when running the backend.

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=core --cov-report=html

# Run specific test file
pytest tests/test_phase8_integration.py -v

# Run linting
make lint
```

---

## 📁 Project Structure

```
The-Loom/
├── agents/                 # AI agent implementations
│   ├── archivist.py       # Story ingestion
│   ├── director.py        # Generation orchestration
│   ├── editor.py          # Text refinement
│   ├── writer.py          # Prose generation
│   └── artist.py          # Image generation
├── core/                   # Core engine modules
│   ├── auth.py            # Authentication
│   ├── collaboration.py   # Real-time collaboration
│   ├── observability.py   # Monitoring
│   ├── rate_limit.py      # Rate limiting
│   ├── llm_backend.py     # LLM abstraction
│   ├── diffusion_backend.py # Image generation
│   ├── vector_store.py    # Semantic search
│   ├── graph_persistence.py # Graph database
│   ├── event_store.py     # Event sourcing
│   ├── qc_analysis.py     # Quality control
│   ├── text_generation_engine.py
│   └── image_generation_engine.py
├── ui/                     # Frontend React app
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── stores/        # Zustand stores
│   │   └── hooks/         # Custom hooks
│   └── api.py             # FastAPI backend
├── tests/                  # Test suite
├── docs/                   # Documentation
├── Dockerfile             # Container build
├── docker-compose.yml     # Orchestration
├── requirements.txt       # Python deps
├── pyproject.toml         # Project config
└── README.md              # This file
```

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes, run checks
make lint && make test

# 3. Commit and push
git commit -m "feat: add my feature"
git push origin feature/my-feature

# 4. Create Pull Request
```

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/), and [ChromaDB](https://www.trychroma.com/)
- Inspired by branching narrative games and collaborative writing tools
- Special thanks to the open-source AI community

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/IotA-asce/The-Loom/issues)
- **Discussions**: [GitHub Discussions](https://github.com/IotA-asce/The-Loom/discussions)
- **Documentation**: `/docs` endpoint when running locally

---

<p align="center">
  <em>Weaving stories, one branch at a time.</em>
</p>
