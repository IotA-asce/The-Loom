# The Loom 🧵

[![CI](https://github.com/IotA-asce/The-Loom/actions/workflows/ci.yml/badge.svg)](https://github.com/IotA-asce/The-Loom/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> *Weaving infinite timelines from existing stories.*

**The Loom** is a Python-first storytelling framework that analyzes source narratives, branches plot timelines, and generates both prose and manga-style outputs with coordinated AI agents. It preserves the original tone—from wholesome children's tales to visceral adult fiction—without sanitization or bias.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **📚 Multi-Format Ingestion** | Parse `.txt`, `.pdf`, `.epub`, `.cbz`, and loose image folders with security sandboxing |
| **🎭 Tone Preservation** | Analyze and replicate any genre—from Kodomomuke to Seinen, slice-of-life to horror |
| **🌳 Branching Narratives** | Create alternate timelines with a navigable "Tree of Possibilities" |
| **✍️ Prose Generation** | Style-faithful text generation with character voice integrity |
| **🎨 Manga Generation** | Panel sequences with atmosphere control and identity consistency |
| **🔄 State Integrity** | Event-sourced edit logs, idempotent jobs, and cross-modal synchronization |
| **🖥️ Interactive UI** | Graph-based branch visualization, dual-view editor, tuner controls |
| **🔒 Security & Privacy** | Local-first defaults, PII redaction, file sandboxing, kill switches |
| **📊 Observability** | Structured logging, SLO monitoring, incident runbooks |
| **🚀 Release Ready** | Comprehensive benchmarks, release gates, beta program framework |

---

## 🚀 Quick Start

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
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Verify Installation

```bash
# Run all checks
make lint && make test

# Run benchmark suite
python -c "from core.benchmark_engine import ReleaseEngine; e = ReleaseEngine(); e.benchmarks.run_suite(); print(e.benchmarks.generate_report())"
```

---

## 🎮 Running the Application

### Option 1: Start the Web UI (Recommended)

The Loom includes a React-based web interface with a FastAPI backend.

```bash
# Terminal 1: Start the backend API
cd The-Loom
source .venv/bin/activate
python -m ui.api

# Terminal 2: Start the frontend (in a new terminal)
cd The-Loom/ui
npm install  # First time only
npm run dev
```

Then open http://localhost:3000 in your browser.

### Option 2: Use Python API Directly

```python
# Create a script (e.g., run_loom.py)
from agents.archivist import ingest_text_file
from core.story_graph_engine import BranchLifecycleManager

# 1. Ingest a story
result = ingest_text_file("my_story.txt")
print(f"Ingested {result.chunk_count} chunks")

# 2. Create a branch
manager = BranchLifecycleManager()
manager.create_root_branch("main")
branch = manager.create_divergence_node(
    parent_branch_id="main",
    divergence_event_id="evt-001",
    label="Alternate Ending"
)
print(f"Created branch: {branch.branch_id}")

# 3. Run generation (requires configured LLM backend)
# See docs/ for LLM setup instructions
```

Run it:
```bash
source .venv/bin/activate
python run_loom.py
```

### Option 3: Interactive Python Shell

```bash
source .venv/bin/activate
python
```

```python
>>> from core.benchmark_engine import ReleaseEngine
>>> engine = ReleaseEngine()
>>> metrics = engine.evaluate_phase10_done_criteria()
>>> print(f"Release ready: {metrics.release_ready}")
```

---

## 📖 Usage Examples

### Basic Story Ingestion

```python
from agents.archivist import ingest_text_file

# Ingest a story file
result = ingest_text_file("path/to/story.txt")
print(f"Ingested {result.chunk_count} chunks")
```

### Creating a Branch

```python
from core.story_graph_engine import BranchLifecycleManager

manager = BranchLifecycleManager()
manager.create_root_branch("main")

# Create an alternate timeline branch
branch = manager.create_divergence_node(
    parent_branch_id="main",
    divergence_event_id="evt-001",
    label="What if the hero failed?"
)
print(f"Created branch: {branch.branch_id}")
```

### Generation with Sync

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
sync = initialize_sync_state(
    "scene-001",
    text_version="v1",
    image_version="v1"
)
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

### Running Benchmarks

```python
from core.benchmark_engine import ReleaseEngine

engine = ReleaseEngine()

# Run full benchmark suite
run = engine.benchmarks.run_suite()

# Generate report
report = engine.benchmarks.generate_report()
print(f"Pass rate: {report['summary']['pass_rate']:.1%}")
```

### Checking Release Readiness

```python
from core.benchmark_engine import ReleaseEngine

engine = ReleaseEngine()

# Check if ready for release
metrics = engine.evaluate_phase10_done_criteria()
print(f"Release ready: {metrics.release_ready}")
print(f"All gates pass: {metrics.all_gates_pass}")
print(f"Benchmark pass rate: {metrics.benchmarks_pass_rate:.1%}")
```

---

## 🏗️ Architecture

The Loom orchestrates four specialized agents coordinated by a central Director:

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
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │Operations    │  │ Benchmark    │  │   Release    │                   │
│  │   Engine     │  │   Engine     │  │   Engine     │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Agent Responsibilities

| Agent | Purpose | Key Capabilities |
|-------|---------|------------------|
| **Archivist** | Ingests source material | Text/PDF/EPUB/CBZ parsing, OCR, content hashing |
| **Writer** | Generates prose | Style mimicry, voice constraints, long-range coherence |
| **Artist** | Generates manga panels | Continuity anchors, atmosphere presets, identity packs |
| **Director** | Orchestrates workflow | Job scheduling, edit provenance, cross-modal sync |

---

## 📁 Repository Structure

```
the-loom/
├── agents/                    # Agent implementations
│   ├── archivist.py          # Ingestion and analysis
│   ├── writer.py             # Text generation interface
│   ├── artist.py             # Image generation interface
│   └── director.py           # Orchestration and coordination
├── core/                      # Core engines
│   ├── archivist_engine.py   # Ingestion pipeline
│   ├── artist_engine.py      # Image generation
│   ├── benchmark_engine.py   # Benchmarks and release
│   ├── frontend_workflow_engine.py  # UI workflows
│   ├── graph_logic.py        # Story branching mechanics
│   ├── image_generation_engine.py   # Artist implementation
│   ├── orchestration_engine.py      # State integrity
│   ├── operations_engine.py  # Security and governance
│   ├── profile_engine.py     # Tone/maturity analysis
│   ├── retrieval_engine.py   # Vector memory and search
│   ├── story_graph_engine.py # Event and temporal logic
│   ├── text_generation_engine.py    # Writer implementation
│   └── writer_engine.py      # Text generation
├── tests/                     # Test suite (160+ tests)
│   ├── test_*.py             # Unit and integration tests
│   └── fixtures/             # Golden test fixtures
├── ui/                        # Frontend (React + FastAPI)
│   ├── api.py                # Backend API
│   ├── src/                  # React components
│   └── package.json          # Frontend dependencies
├── models/                    # Model storage (local LLM weights)
├── docs/                      # Documentation
├── README.md                  # This file
├── CHANGELOG.md               # Release notes
├── GOALS.md                   # Implementation roadmap
├── PRD.md                     # Product requirements
├── STRATEGY.md                # Architecture decisions
└── AGENTS.md                  # Contributor guidelines
```

---

## ✅ Implementation Status

**All 10 Phases Complete — The Loom v1.0.0 is Release Ready** 🎉

| Phase | Component | Status | Tests |
|-------|-----------|--------|-------|
| 0 | Project Foundation | ✅ Complete | 4 tests |
| 1 | Safe Ingestion | ✅ Complete | 12 tests |
| 2 | Tone Profiling | ✅ Complete | 10 tests |
| 3 | Retrieval Engine | ✅ Complete | 8 tests |
| 4 | Story Graph | ✅ Complete | 15 tests |
| 5 | Text Generation | ✅ Complete | 6 tests |
| 6 | Image Generation | ✅ Complete | 8 tests |
| 7 | Orchestration | ✅ Complete | 16 tests |
| 8 | Frontend | ✅ Complete | 30 tests |
| 9 | Operations | ✅ Complete | 47 tests |
| 10 | Evaluation | ✅ Complete | 36 tests |
| **Total** | | **✅ 160 tests** | **100% pass** |

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
make test

# Run specific phase tests
pytest tests/test_ingestion_*.py -v
pytest tests/test_orchestration_engine.py -v
pytest tests/test_frontend_phase8.py -v

# Run with coverage
pytest --cov=core --cov=agents --cov-report=html

# Run benchmarks
python -c "from core.benchmark_engine import ReleaseEngine; e = ReleaseEngine(); e.benchmarks.run_suite()"
```

### Benchmark Categories

| Category | Benchmarks | Target |
|----------|------------|--------|
| Ingestion | 4 | < 5s for 1MB PDF |
| Retrieval | 4 | < 200ms P95 |
| Narrative | 4 | > 80% accuracy |
| Visual | 4 | > 85% consistency |
| UX | 4 | < 16ms frame time |

---

## 🔒 Security & Privacy

### Security Features

- **File Sandboxing**: Untrusted files parsed in isolated workers
- **Path Traversal Protection**: Prevents directory escape attacks
- **Zip Bomb Detection**: Rejects compression bombs automatically
- **Input Validation**: Strict schema validation on all inputs
- **Kill Switches**: Emergency stops for runaway workloads

### Privacy Features

- **Local-First Default**: No external calls without explicit opt-in
- **PII Redaction**: Automatic detection and redaction of email, phone, SSN, IP
- **Data Retention**: Configurable policies with automatic enforcement
- **Audit Logging**: Complete provenance for all operations

---

## 📊 Observability

### SLOs Defined

| SLO | Target | Measurement |
|-----|--------|-------------|
| Ingestion Latency | P95 < 5s | Measured |
| Retrieval Latency | P95 < 200ms | Measured |
| Generation Success | > 99% | Measured |
| Sync Success | > 99.5% | Measured |

### Monitoring

```python
from core.operations_engine import OperationsEngine

ops = OperationsEngine()

# Log structured event
ops.observability.log(
    level=LogLevel.INFO,
    component=Component.INGESTION,
    message="Story ingested successfully",
    request_id="req-123",
    job_id="job-456"
)

# Check for breached SLOs
breached = ops.observability.get_breached_slos()
```

---

## 🎯 Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Tone Fidelity First** | Profile engine preserves source style without flattening extremes |
| **Branch-First Logic** | Alternate timelines are first-class objects with full lineage tracking |
| **Local-First Privacy** | All data processing happens locally by default |
| **Deterministic Testing** | Reproducible behavior with fixtures and mock models |
| **Clear Agent Boundaries** | Strict contracts between ingest, write, draw, and direct |
| **Defense in Depth** | Multiple security layers from sandboxing to kill switches |

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [`PRD.md`](./PRD.md) | Product Requirements Document |
| [`STRATEGY.md`](./STRATEGY.md) | Problem-first architecture decisions |
| [`GOALS.md`](./GOALS.md) | Implementation roadmap and phase checklist |
| [`AGENTS.md`](./AGENTS.md) | Engineering conventions for contributors |
| [`CHANGELOG.md`](./CHANGELOG.md) | Release notes and version history |

---

## 🤝 Contributing

We welcome contributions! Please:

1. **Follow Code Style**: Enforced by `ruff` and `black`
   ```bash
   make lint  # Check style
   make format  # Auto-fix issues
   ```

2. **Add Tests**: All new capabilities need tests
   ```bash
   pytest tests/test_your_feature.py -v
   ```

3. **Update Documentation**: Keep docs in sync with code changes

4. **Keep PRs Focused**: One goal or tightly-related slice per PR

5. **Run Full Suite**: Before submitting
   ```bash
   make lint && make test
   ```

See [`AGENTS.md`](./AGENTS.md) for detailed contributor guidelines.

---

## 📄 License

MIT License — see [`LICENSE`](./LICENSE) for details.

---

## 🙏 Acknowledgments

The Loom was built with inspiration from:

- The open-source AI/ML community
- Interactive fiction and narrative game engines
- Version control systems (for branch concepts)

---

<p align="center">
  <i>"Every story is a thread. The Loom weaves them into infinite possibilities."</i>
</p>

<p align="center">
  <b>🧵 The Loom v1.0.0 — The Weaver 🧵</b>
</p>
