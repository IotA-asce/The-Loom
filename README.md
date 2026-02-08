# The Loom

[![CI](https://github.com/IotA-asce/The-Loom/actions/workflows/ci.yml/badge.svg)](https://github.com/IotA-asce/The-Loom/actions/workflows/ci.yml)

Weaving infinite timelines from existing stories.

The Loom is a Python-first storytelling framework for analyzing source narratives,
branching plot timelines, and generating both prose and manga-style outputs with
coordinated LLM agents.

## Project Status

This repository is now in **Phase 0 (foundation) implementation**.

- Project docs are established: `PRD.md`, `STRATEGY.md`, `GOALS.md`, `AGENTS.md`
- Initial Python scaffolding is in place (`agents/`, `core/`, `tests/`, tooling)
- CI now runs lint + test on push/PR

Treat `PRD.md` as product intent, `STRATEGY.md` as problem-first architecture,
and `GOALS.md` as the step-by-step execution checklist.

## Vision

Most AI storytelling tools lose tonal fidelity over long outputs or extreme genre
shifts. The Loom aims to preserve the source tone across the full spectrum:

- wholesome to dark
- children-focused to mature/adult
- slice-of-life to horror/violent action

The core goal is style-faithful branching storytelling, not forced normalization.

## What The Loom Is Intended To Do

- Ingest text and manga inputs (`.txt`, `.pdf`, `.epub`, `.cbz`, image folders)
- Analyze narrative and visual tone to build a "maturity/style profile"
- Build a navigable event graph (the "Tree of Possibilities")
- Generate alternate branches in prose and matching manga panels
- Keep character consistency and atmosphere across branches

## Planned Architecture

From the current PRD, the system is planned around specialized agents:

- `archivist` - ingestion and tonal analysis
- `writer` - style-faithful prose generation
- `artist` - visual generation with atmosphere controls
- `director` - orchestration and tuning controls

Supporting layers include graph logic, style/character profiles, local model
integration, and a node-based UI for branching and editing.

## Development Roadmap (From PRD)

1. Foundation: ingestion + rating classifier
2. Weaver: node graph + branch-aware writing
3. Illustrator: manga panel pipeline + atmosphere control
4. Director: full UI + editing/polish loop

See `PRD.md` for milestone-level deliverables and constraints.

## Repository Layout

Current repository (foundation scaffolding):

```text
.
├── .github/workflows/ci.yml
├── .pre-commit-config.yaml
├── AGENTS.md
├── GOALS.md
├── LICENSE
├── Makefile
├── PRD.md
└── README.md
```

Key implementation directories:

```text
.
├── agents/
├── core/
├── docs/
├── models/
├── scripts/
├── tests/
│   └── fixtures/
└── ui/
```

## Getting Started

Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run project checks:

```bash
make lint
make test
```

Optional build command:

```bash
make build
```

Run a single test:

```bash
pytest tests/test_smoke.py::test_supported_manga_extensions_include_required_formats -q
```

## Phase 0 Coverage

Implemented in the current baseline:

- Repository scaffolding and Python package layout
- Lint/format/type/test toolchain (`ruff`, `black`, `mypy`, `pytest`)
- Pre-commit configuration
- CI workflow with failure artifact upload for fixture diffs
- Fixture baseline for text/pdf/epub/cbz/loose manga image pages
- Golden fixture examples for chapter parsing and OCR

Next implementation slices are tracked in `GOALS.md` (starting from Phase 1).

## Guiding Engineering Principles

- Tone fidelity first: match source style without flattening
- Branch-first logic: make alternate timelines first-class objects
- Local-first privacy where possible
- Deterministic testing around graph logic and branch consequences
- Clear agent boundaries between ingest, write, draw, and direct

## License

MIT - see `LICENSE`.
