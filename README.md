# The Loom

[![CI](https://github.com/IotA-asce/The-Loom/actions/workflows/ci.yml/badge.svg)](https://github.com/IotA-asce/The-Loom/actions/workflows/ci.yml)

Weaving infinite timelines from existing stories.

The Loom is a Python-first storytelling framework for analyzing source narratives,
branching plot timelines, and generating both prose and manga-style outputs with
coordinated LLM agents.

## Project Status

This repository now has **Phase 0 complete**, **Phase 1 complete**,
**Phase 2 complete**, **Phase 3 complete**, and **Phase 4 (story graph core) implemented**.

- Project docs are established: `PRD.md`, `STRATEGY.md`, `GOALS.md`, `AGENTS.md`
- Initial Python scaffolding is in place (`agents/`, `core/`, `tests/`, tooling)
- CI now runs lint + test on push/PR
- Ingestion trust-boundary checks exist for `.cbz` and image-folder sources
- Text ingestion exists for `.txt`, `.pdf` (with fallback), and `.epub` (chapter-aware)
- Manga page normalization exists for EXIF orientation, color mode, alpha handling, and spread detection
- OCR baseline exists with fallback/ensemble path and JSON report storage with coordinates/confidence
- Ingestion dedupe exists with content hashing, near-duplicate detection, and default idempotent behavior
- Text/visual tone profiling exists with scene/panel analysis, uncertainty scoring, and shift detection
- Maturity spectrum engine exists with smoothing, preset mapping, correction loops, and override audit trails
- Retrieval engine exists with hierarchical memory, branch-aware namespaces, hybrid ranking, incremental refresh, and runtime/cost tracking
- Story graph engine exists with event extraction, relation/temporal inference, divergence lifecycle workflows, consequence simulation, and schema migrations

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

```bash
pytest tests/test_manga_ingestion_pipeline.py::test_folder_ingestion_supports_png_jpg_jpeg_webp -q
```

```bash
pytest tests/test_ocr_pipeline.py::test_sidecar_ocr_fallback_extracts_regions -q
```

```bash
pytest tests/test_profile_engine.py::test_benchmark_precision_recall_and_tone_jitter_thresholds -q
```

```bash
pytest tests/test_retrieval_engine.py::test_phase3_done_criteria_thresholds_hold -q
```

```bash
pytest tests/test_story_graph_engine.py::test_phase4_done_criteria_thresholds_hold -q
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

Phase 1 progress (G1.3 completed):

- `ingest_cbz_pages()` and `ingest_image_folder_pages()` implemented with format support for `.png`, `.jpg`, `.jpeg`, `.webp`
- Manga page normalization includes EXIF orientation handling, RGB normalization, and alpha flattening
- Natural page ordering and spread-page detection are now part of ingestion metadata

Phase 1 progress (G1.4 completed):

- OCR baseline extraction implemented for manga pages
- Low-confidence fallback and ensemble selection path implemented
- Dialogue region classification (`speech`, `narration`, `thought`) added
- OCR reports can be persisted with coordinates and confidence scores

Phase 1 progress (G1.5 completed):

- Content hashing added for text chunks and manga pages
- Near-duplicate detection added for text and image ingestion
- Re-ingestion is idempotent by default through ingestion dedupe cache

Phase 2 progress (G2.1 completed):

- Scene-level text profiling implemented with multi-label tagging for violence/romance/humor/horror/wholesome/psychological signals
- Uncertainty scoring added for low-confidence scenes
- Abrupt tonal shifts and peak-intensity scenes detected per profile run

Phase 2 progress (G2.2 completed):

- Panel-level visual tone classification implemented (`light`, `balanced`, `dark`, `gritty`)
- Visual cues now include brightness, contrast, line density, texture entropy, and composition balance
- Panel signals aggregate into scene and chapter visual profiles

Phase 2 progress (G2.3 completed):

- Maturity spectrum scores generated from text + visual signals
- Rolling smoothing window reduces tone jitter in long sequences
- Maturity bands map to generation presets for parameterized downstream generation
- Manual maturity overrides supported with actor/reason metadata

Phase 2 progress (G2.4 completed):

- Human correction loop added for scene profile adjustments
- Profile versioning and provenance tracking implemented per branch
- Override audit events are queryable by branch/version
- Regression benchmark tests added for precision/recall and jitter tolerance

Phase 3 progress (G3.1 completed):

- Hierarchical chunking implemented for chapter/scene/sentence levels
- Canonical metadata attached for story, branch, version, lineage, and timestamps
- Unresolved-thread tracker added for long-form narrative memory

Phase 3 progress (G3.2 completed):

- Branch-aware namespace partitioning implemented for retrieval index storage
- Branch lineage filters applied at query time
- Namespace compaction and dedup maintenance jobs implemented

Phase 3 progress (G3.3 completed):

- Hybrid retrieval implemented (`BM25 + embedding`)
- Canon-aware reranking layer added for branch/canon relevance
- Retrieval quality metrics implemented (`Precision@K`, `MRR`, `nDCG`)

Phase 3 progress (G3.4 completed):

- Incremental re-embedding path implemented for edited chunks
- Stale chunk suppression implemented in retrieval responses
- Retrieval invalidation tests added for branch rewrite workflows

Phase 3 progress (G3.5 completed):

- Query/result caching layers implemented with cache-hit tracking
- Retrieval budget controls added (token, candidate, and cost limits)
- Runtime metrics now expose p95 latency and p95 cost

Phase 4 progress (G4.1 completed):

- Hybrid event extraction pipeline implemented with normalized schema and confidence fields
- Duplicate event merge logic added to suppress redundant event nodes

Phase 4 progress (G4.2 completed):

- Canonical entity ids implemented via alias graph resolution
- Causality and dependency relation extraction added for event graph edges
- Entity-state contradiction detection added for canonical consistency checks

Phase 4 progress (G4.3 completed):

- Temporal ordering inference implemented beyond source order constraints
- Contradiction detection added for cycles and impossible temporal edges
- Automated repair workflow added to remove low-confidence cycle edges

Phase 4 progress (G4.4 completed):

- Divergence node creation and branch lineage tracking implemented
- High-impact branch point recommendations implemented
- Branch budget enforcement with archive/merge workflows implemented

Phase 4 progress (G4.5 completed):

- Affected-subgraph consequence simulation implemented
- Hard canon constraints and soft style penalties integrated into scoring
- Downstream consistency tracked against baseline full recompute

Phase 4 progress (G4.6 completed):

- Graph snapshot schema versioning implemented (current v3)
- Replayable migration manager with rollback checkpoints implemented
- Historical snapshot migration replay tests added for v1/v2 payloads

Next implementation slices are tracked in `GOALS.md` (starting from `G5.1`).

## Guiding Engineering Principles

- Tone fidelity first: match source style without flattening
- Branch-first logic: make alternate timelines first-class objects
- Local-first privacy where possible
- Deterministic testing around graph logic and branch consequences
- Clear agent boundaries between ingest, write, draw, and direct

## License

MIT - see `LICENSE`.
