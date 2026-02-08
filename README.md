# The Loom

[![CI](https://github.com/IotA-asce/The-Loom/actions/workflows/ci.yml/badge.svg)](https://github.com/IotA-asce/The-Loom/actions/workflows/ci.yml)

Weaving infinite timelines from existing stories.

The Loom is a Python-first storytelling framework for analyzing source narratives,
branching plot timelines, and generating both prose and manga-style outputs with
coordinated LLM agents.

## Project Status

This repository now has **Phase 0 complete** and **Phase 1 (G1.1 + G1.2) implemented**.

- Project docs are established: `PRD.md`, `STRATEGY.md`, `GOALS.md`, `AGENTS.md`
- Initial Python scaffolding is in place (`agents/`, `core/`, `tests/`, tooling)
- CI now runs lint + test on push/PR
- Ingestion trust-boundary checks exist for `.cbz` and image-folder sources
- Text ingestion exists for `.txt`, `.pdf` (with fallback), and `.epub` (chapter-aware)

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
pytest tests/test_ingestion_security.py::test_cbz_ingestion_rejects_path_traversal -q
```

```bash
pytest tests/test_text_ingestion.py::test_epub_ingestion_extracts_chapters_from_spine -q
```

## Phase Progress

Phase 0 completed:

- Repository scaffolding and Python package layout
- Lint/format/type/test toolchain (`ruff`, `black`, `mypy`, `pytest`)
- Pre-commit configuration
- CI workflow with failure artifact upload for fixture diffs
- Fixture baseline for text/pdf/epub/cbz/loose manga image pages
- Golden fixture examples for chapter parsing and OCR

Phase 1 progress (G1.1 completed):

- Sandboxed ingestion workers with timeout controls
- File size and page count limits for folders and archives
- MIME/extension/signature consistency checks
- CBZ path traversal and compression-ratio abuse protection

Phase 1 progress (G1.2 completed):

- `.txt` ingestion with encoding normalization and newline normalization
- `.pdf` ingestion with primary parser path and fallback extraction strategy
- `.epub` ingestion with spine-based chapter extraction and fallback HTML scan
- Parser confidence scoring plus warnings/errors in ingestion reports

Next implementation slices are tracked in `GOALS.md` (starting from `G1.3`).

## Guiding Engineering Principles

- Tone fidelity first: match source style without flattening
- Branch-first logic: make alternate timelines first-class objects
- Local-first privacy where possible
- Deterministic testing around graph logic and branch consequences
- Clear agent boundaries between ingest, write, draw, and direct

## License

MIT - see `LICENSE`.
