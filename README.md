# The Loom 🧵

[![CI](https://github.com/IotA-asce/The-Loom/actions/workflows/ci.yml/badge.svg)](https://github.com/IotA-asce/The-Loom/actions/workflows/ci.yml)

> *Weaving infinite timelines from existing stories.*

The Loom is a Python-first storytelling framework that analyzes source narratives, branches plot timelines, and generates both prose and manga-style outputs with coordinated AI agents. It preserves the original tone—from wholesome children's tales to visceral adult fiction—without sanitization or bias.

---

## ✨ What The Loom Does

| Capability | Description |
|------------|-------------|
| **📚 Multi-Format Ingestion** | Parse `.txt`, `.pdf`, `.epub`, `.cbz`, and loose image folders |
| **🎭 Tone Preservation** | Analyze and replicate any genre—from Kodomomuke to Seinen, slice-of-life to horror |
| **🌳 Branching Narratives** | Create alternate timelines with a navigable "Tree of Possibilities" |
| **✍️ Prose Generation** | Style-faithful text generation with character voice integrity |
| **🎨 Manga Generation** | Panel sequences with atmosphere control and identity consistency |
| **🔄 State Integrity** | Event-sourced edit logs, idempotent jobs, and cross-modal synchronization |
| **🎨 Interactive UI** | Graph-based branch visualization, dual-view editor, tuner controls |
| **🔒 Operations & Governance** | Observability, incident readiness, privacy controls, content governance |
| **📊 Evaluation & Release** | Benchmark suites, release gates, beta program, changelog |

---

## 🚀 Current Status

**Phase 0–10 Complete** — The Loom is release-ready with comprehensive benchmarks, release gates, beta program, and full documentation.

| Phase | Status | Key Deliverables |
|-------|--------|------------------|
| Phase 0 | ✅ Complete | Repository scaffolding, CI/CD, test baseline |
| Phase 1 | ✅ Complete | Safe file ingestion (text, PDF, EPUB, CBZ, images) |
| Phase 2 | ✅ Complete | Tone profiling and maturity spectrum engine |
| Phase 3 | ✅ Complete | Retrieval engine with branch-aware memory |
| Phase 4 | ✅ Complete | Story graph with divergence and consequence simulation |
| Phase 5 | ✅ Complete | Writer agent with style fidelity controls |
| Phase 6 | ✅ Complete | Artist agent with panel continuity and cross-modal alignment |
| Phase 7 | ✅ Complete | Orchestration engine with edit provenance and sync semantics |
| Phase 8 | ✅ Complete | Interactive frontend and dual-view UI |
| Phase 9 | ✅ Complete | Operations, security, and governance |
| Phase 10 | ✅ Complete | Evaluation, hardening, and release |

---

## 🏗️ Architecture

The Loom orchestrates four specialized agents:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Archivist  │────▶│   Writer    │◄───▶│   Artist    │◄───▶│   Director  │
│  (Ingest)   │     │  (Text Gen) │     │ (Image Gen) │     │(Orchestrate)│
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                    │                   │                   │
       ▼                    ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Core Services                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ Story Graph  │  │    Tone      │  │  Retrieval   │  │     Sync    │ │
│  │   Engine     │  │   Engine     │  │   Engine     │  │   Manager   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Agent Responsibilities

| Agent | Purpose |
|-------|---------|
| **Archivist** | Ingests source material, extracts events, performs OCR on manga pages |
| **Writer** | Generates prose with style mimicry, voice constraints, and long-range coherence |
| **Artist** | Generates manga panels with continuity anchors, atmosphere presets, and identity packs |
| **Director** | Orchestrates agents, manages edit provenance, maintains cross-modal sync |

---

## 📁 Repository Layout

```
the-loom/
├── agents/              # Agent implementations
│   ├── archivist.py    # Ingestion and analysis
│   ├── writer.py       # Text generation interface
│   ├── artist.py       # Image generation interface
│   └── director.py     # Orchestration and coordination
├── core/               # Core engines
│   ├── graph_logic.py           # Story branching mechanics
│   ├── profile_engine.py        # Tone/maturity analysis
│   ├── retrieval_engine.py      # Vector memory and search
│   ├── story_graph_engine.py    # Event and temporal logic
│   ├── text_generation_engine.py # Writer implementation
│   ├── image_generation_engine.py # Artist implementation
│   ├── orchestration_engine.py  # Phase 7: State integrity
│   ├── frontend_workflow_engine.py # Phase 8: Frontend workflows
│   └── operations_engine.py     # Phase 9: Operations & governance
├── tests/              # Test suite
│   ├── fixtures/       # Golden test fixtures
│   └── test_*.py       # Unit and integration tests
├── ui/                 # Frontend (Phase 8 complete)
│   ├── api.py         # FastAPI backend API
│   ├── src/           # React frontend components
│   │   ├── components/# GraphCanvas, TunerPanel, DualView
│   │   └── store.ts   # State management
├── models/             # Model storage (local LLM weights)
└── docs/               # Documentation
```

---

## 🛠️ Getting Started

### Prerequisites

- Python 3.12+
- (Optional) Local LLM runtime (Ollama, LM Studio) for private inference

### Installation

```bash
# Clone the repository
git clone https://github.com/IotA-asce/The-Loom.git
cd The-Loom

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running Checks

```bash
# Run linting
make lint

# Run tests
make test

# Run specific test
pytest tests/test_orchestration_engine.py -v
```

---

## 🧪 Testing Philosophy

Every phase has comprehensive tests:

```bash
# Phase 1: Ingestion security and parsing
pytest tests/test_ingestion_security.py tests/test_text_ingestion.py -v

# Phase 6: Image generation with continuity
pytest tests/test_artist_engine.py -v

# Phase 7: Orchestration and state integrity
pytest tests/test_orchestration_engine.py -v
```

---

## 📋 Example Usage

### Creating a Generation Plan

```python
from agents.director import create_generation_plan, initialize_sync_state

# Create an idempotent generation plan
plan = create_generation_plan(
    branch_id="branch-001",
    scene_id="scene-001",
    include_text=True,
    include_images=True,
)

# Initialize sync state for dual-view
sync = initialize_sync_state("scene-001", text_version="v1", image_version="v1")
```

### Logging Edits

```python
from agents.director import log_text_edit, log_panel_redraw

# Log a text edit
log_text_edit(
    branch_id="branch-001",
    scene_id="scene-001",
    span_start=100,
    span_end=250,
    previous_content="old dialogue",
    new_content="revised dialogue",
    actor="user",
    reason="clarity improvement"
)

# Log a panel redraw request
log_panel_redraw(
    branch_id="branch-001",
    scene_id="scene-001",
    panel_index=3,
    actor="user",
    reason="anatomy fix"
)
```

### Checking Agent Contracts

```python
from agents.director import validate_agent_contract

# Validate writer agent compatibility
is_valid = validate_agent_contract(
    agent_name="writer",
    input_data={"story_id": "s1", "branch_id": "b1", "user_prompt": "test"},
    model_version="llama-3",
    workflow_version="text-gen-v1"
)
```

---

## 🎯 Design Principles

| Principle | Description |
|-----------|-------------|
| **Tone Fidelity First** | Match source style without flattening extremes |
| **Branch-First Logic** | Alternate timelines are first-class objects |
| **Local-First Privacy** | Private by default; no data exfiltration |
| **Deterministic Testing** | Reproducible behavior for validation |
| **Clear Agent Boundaries** | Separation of ingest, write, draw, and direct |

---

## 📚 Documentation

- [`PRD.md`](./PRD.md) — Product Requirements Document
- [`STRATEGY.md`](./STRATEGY.md) — Problem-first architecture decisions
- [`GOALS.md`](./GOALS.md) — Implementation roadmap and checklist
- [`AGENTS.md`](./AGENTS.md) — Engineering conventions for contributors

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Follow the existing code style (enforced by `ruff` and `black`)
2. Add tests for new capabilities
3. Update documentation for behavior changes
4. Keep PRs scoped to a single goal

---

## 📄 License

MIT License — see [`LICENSE`](./LICENSE) for details.

---

## 🗺️ Roadmap

### Upcoming (Phase 8+)

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| Phase 8 | ✅ Complete | Interactive graph UX, dual-view, tuner controls |
| Phase 9 | 📝 Planned | Operations, incident readiness, privacy controls |
| Phase 10 | 📝 Planned | Benchmark suites, beta program, public release |

---

<p align="center">
  <i>"Every story is a thread. The Loom weaves them into infinite possibilities."</i>
</p>
