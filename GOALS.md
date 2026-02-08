# GOALS.md

Comprehensive, sequential implementation goals for The Loom.

Use this as the execution checklist for building the project from docs to a
production-ready application. Goals are ordered and should be completed phase by
phase.

## How to use this file

- Complete phases in order.
- Do not start a later phase until the current phase done criteria are checked.
- Link pull requests/issues to goal IDs (for example, `G3.4`).
- Update checkboxes as work is completed.

## Phase 0 - Project Foundation

### G0.1 Repository scaffolding
- [x] Create base directories: `agents/`, `core/`, `ui/`, `tests/`, `models/`, `scripts/`, `docs/`
- [x] Add initial package layout for Python modules
- [x] Add `.gitignore` with Python, Node, cache, model, and local env artifacts
- [x] Add `requirements.txt` or lockfile strategy

### G0.2 Tooling and standards
- [x] Add `pyproject.toml` with `ruff`, `black`, `pytest`, and optional `mypy` config
- [x] Add a `Makefile` (or task runner) with `lint`, `format`, `test`, `build` targets
- [x] Configure pre-commit hooks for lint/format checks
- [x] Add baseline typing rules and import ordering conventions

### G0.3 Test and fixture baseline
- [x] Create smoke test structure in `tests/`
- [x] Add fixture folders for text, pdf, epub, cbz, and loose image pages
- [x] Add golden test fixtures for sample chapter parsing and OCR outputs

### G0.4 CI baseline
- [x] Add CI workflow for lint + tests on PRs
- [x] Add artifact upload for failing fixture diffs
- [x] Add status badges to README once CI is live

### Phase 0 done criteria
- [x] `make lint` (or equivalent) passes
- [x] `pytest -q` runs and passes smoke tests
- [x] CI runs on every PR

## Phase 1 - Safe, Reliable Ingestion

### G1.1 File trust boundary and sandboxing
- [x] Implement sandboxed parsing workers for untrusted files
- [x] Enforce file size, page count, and timeout limits
- [x] Validate MIME type and extension consistency
- [x] Add archive path traversal and zip bomb protection

### G1.2 Text ingestion pipeline
- [ ] Implement `.txt` parser with encoding normalization
- [ ] Implement `.pdf` parser with fallback strategy
- [ ] Implement `.epub` parser with chapter extraction support
- [ ] Build parser confidence scoring and error reporting

### G1.3 Manga ingestion pipeline
- [ ] Implement `ingest_cbz_pages()` for archive-based manga imports
- [ ] Implement `ingest_image_folder_pages()` for loose page folders
- [ ] Support page formats: `.png`, `.jpg`, `.jpeg`, `.webp`
- [ ] Normalize EXIF orientation, color space, and alpha handling
- [ ] Apply natural page ordering and spread detection

### G1.4 OCR and page semantics
- [ ] Implement OCR baseline on manga pages
- [ ] Add OCR fallback/ensemble path for low-confidence pages
- [ ] Detect dialogue regions and classify bubble/narration types
- [ ] Store OCR text with page coordinates and confidence

### G1.5 Idempotency and deduplication
- [ ] Add content hashing for chunks and pages
- [ ] Add near-duplicate detection for repeated imports
- [ ] Ensure re-ingestion is idempotent by default

### Phase 1 done criteria
- [ ] Mixed fixture ingestion success rate meets target
- [ ] Per-format decode success (png/jpg/jpeg/webp/cbz) meets target
- [ ] Security fixture suite passes

## Phase 2 - Tone, Style, and Maturity Profiling

### G2.1 Text profile extraction
- [ ] Implement scene-level sentiment/intensity multi-label tagging
- [ ] Add uncertainty scoring for low-confidence classifications
- [ ] Detect abrupt tonal shifts and peak intensity moments

### G2.2 Visual profile extraction
- [ ] Implement panel-level visual tonal classification
- [ ] Add style cues beyond brightness (line density, texture, composition)
- [ ] Aggregate panel tone into scene and chapter profiles

### G2.3 Maturity spectrum engine
- [ ] Implement maturity/rating score bands with smoothing
- [ ] Map score bands to generation parameter presets
- [ ] Add explicit user overrides with audit logging

### G2.4 Profile quality controls
- [ ] Create correction loop for human profile edits
- [ ] Store profile versions and change provenance
- [ ] Add profile regression tests with benchmark fixtures

### Phase 2 done criteria
- [ ] Profile precision/recall targets met on benchmark scenes
- [ ] Tone jitter index remains within tolerance
- [ ] Overrides are traceable per branch version

## Phase 3 - Retrieval and Long-Form Memory

### G3.1 Chunking and memory model
- [ ] Implement hierarchical chunking (sentence, scene, chapter)
- [ ] Attach canonical metadata (story, branch, version, time)
- [ ] Build unresolved-thread tracker for narrative memory

### G3.2 Vector index strategy
- [ ] Implement branch-aware index namespace partitioning
- [ ] Add branch lineage filters in retrieval queries
- [ ] Add index compaction and dedup maintenance jobs

### G3.3 Ranking and retrieval quality
- [ ] Implement hybrid retrieval (BM25 + embedding)
- [ ] Add reranking layer for canon relevance
- [ ] Track retrieval metrics (Precision@K, MRR, nDCG)

### G3.4 Freshness and incremental updates
- [ ] Implement incremental re-embedding on edits
- [ ] Mark stale chunks and suppress stale retrieval hits
- [ ] Add retrieval invalidation tests for branch rewrites

### G3.5 Performance and cost controls
- [ ] Add query/result caching layers
- [ ] Add retrieval budget controls per request
- [ ] Track p95 latency and retrieval cost per query

### Phase 3 done criteria
- [ ] Wrong-branch retrieval incidence is near zero
- [ ] Retrieval quality beats baseline method
- [ ] p95 retrieval latency and cost are within target

## Phase 4 - Story Graph and Branching Core

### G4.1 Event extraction and normalization
- [ ] Build hybrid event extraction pipeline
- [ ] Normalize event schema and confidence fields
- [ ] Add duplicate event merge logic

### G4.2 Entity and relation integrity
- [ ] Implement canonical entity IDs with alias graph
- [ ] Add relation extraction for causality and dependencies
- [ ] Add conflict detection for entity-state contradictions

### G4.3 Temporal and causal ordering
- [ ] Infer chronological ordering beyond source order
- [ ] Add contradiction detector for impossible sequences
- [ ] Add repair workflow for ordering errors

### G4.4 Divergence and branch lifecycle
- [ ] Implement divergence node creation and lineage tracking
- [ ] Add system recommendations for high-impact branch points
- [ ] Add branch budgets and archive/merge workflows

### G4.5 Consequence simulation
- [ ] Implement affected-subgraph recompute pipeline
- [ ] Add hard canon constraints and soft style penalties
- [ ] Track downstream consistency versus baseline recompute

### G4.6 Graph persistence and migration
- [ ] Version graph schema explicitly
- [ ] Add replayable migrations with rollback checkpoints
- [ ] Add migration tests against historical snapshots

### Phase 4 done criteria
- [ ] Event/temporal quality targets met
- [ ] Branch lineage and consequence simulation remain consistent
- [ ] Schema migrations pass replay tests

## Phase 5 - Text Generation Engine

### G5.1 Writer agent baseline
- [ ] Implement Writer Agent interface and contract tests
- [ ] Add branch-aware context assembly from retrieval
- [ ] Add deterministic generation mode for tests

### G5.2 Style fidelity controls
- [ ] Implement style profile embeddings
- [ ] Add style exemplar retrieval and prompt grounding
- [ ] Track style similarity metrics against source windows

### G5.3 Character voice integrity
- [ ] Create per-character voice cards
- [ ] Enforce dialogue/voice constraints in generation
- [ ] Add voice confusion regression tests

### G5.4 Long-range coherence
- [ ] Implement unresolved-thread carryover checks
- [ ] Add arc/chapter memory summaries into generation context
- [ ] Add contradiction checks after chapter generation

### G5.5 Prompt governance and safety
- [ ] Create versioned prompt registry with rollback
- [ ] Enforce strict system/developer/user prompt layering
- [ ] Implement prompt injection defense tests using hostile fixtures

### G5.6 Tuner mapping for text
- [ ] Map violence/humor/romance controls with calibrated curves
- [ ] Add expected-impact preview for slider changes
- [ ] Validate user expectation match in tuning tests

### Phase 5 done criteria
- [ ] Style and voice targets met on benchmark stories
- [ ] Long-range contradiction rate below threshold
- [ ] Prompt version and provenance are fully traceable

## Phase 6 - Manga/Image Generation Engine

### G6.1 Artist agent baseline
- [ ] Implement Artist Agent interface and job contract
- [ ] Integrate diffusion backend with ControlNet-compatible flow
- [ ] Add deterministic seed support and artifact metadata

### G6.2 Panel continuity and scene planning
- [ ] Build shared scene blueprint for panel sequences
- [ ] Add continuity anchors (camera, pose, environment, props)
- [ ] Validate continuity across 4-panel outputs

### G6.3 Atmosphere and tone controls
- [ ] Implement atmosphere presets for light/dark ranges
- [ ] Add explicit lighting and texture constraints
- [ ] Validate readability for high-contrast and dark scenes

### G6.4 Character identity consistency
- [ ] Build identity packs (face/silhouette/costume cues)
- [ ] Add LoRA/adaptor management and training hooks
- [ ] Add drift detection and retraining triggers

### G6.5 Visual quality guardrails
- [ ] Implement anatomy/composition QC scoring
- [ ] Add correction loop and selective redraw flow
- [ ] Track rejection and final pass rates

### G6.6 Cross-modal alignment
- [ ] Use shared structured scene plans for text + image
- [ ] Add mismatch detection between prose and panel semantics
- [ ] Add reconcile workflow when modalities diverge

### Phase 6 done criteria
- [ ] Panel continuity and identity metrics meet target
- [ ] Atmosphere control behaves predictably
- [ ] Cross-modal mismatch rate stays within threshold

## Phase 7 - Orchestration and State Integrity

### G7.1 Director agent contracts
- [ ] Define strict typed contracts for all agent inputs/outputs
- [ ] Add contract test suite in CI
- [ ] Add compatibility matrix for model and workflow versions

### G7.2 Job orchestration reliability
- [ ] Add idempotency keys for generation jobs
- [ ] Implement transactional state transitions per branch version
- [ ] Add bounded retry policies and dead-letter handling

### G7.3 Edit provenance and regeneration
- [ ] Implement event-sourced edit log for text and panels
- [ ] Scope regeneration to affected spans/panels
- [ ] Prevent overwrite of user edits in async reruns

### G7.4 Sync semantics for dual outputs
- [ ] Add shared scene/version IDs across modalities
- [ ] Add stale-state indicators and reconcile actions
- [ ] Add sync regression tests for async race scenarios

### Phase 7 done criteria
- [ ] Duplicate lineage IDs remain zero
- [ ] Recovery from partial failures is reliable
- [ ] Edit provenance remains complete and queryable

## Phase 8 - Frontend and User Workflow

### G8.1 Interactive graph UX
- [ ] Implement node graph rendering with virtualization
- [ ] Add semantic zoom modes (overview/scene/detail)
- [ ] Add undo/redo and autosave checkpoints

### G8.2 Branching workflow UX
- [ ] Add branch creation from any node
- [ ] Show branch lineage and impact previews
- [ ] Add branch archive/merge actions

### G8.3 Tuner and control panel
- [ ] Implement violence/humor/romance controls
- [ ] Add control precedence rules and preview
- [ ] Add warnings for extreme settings

### G8.4 Dual-view and Director Mode
- [ ] Implement text + manga split view
- [ ] Add explicit sync status and stale content badges
- [ ] Implement sentence edit and panel redraw workflows

### G8.5 Accessibility and mobile readiness
- [ ] Add keyboard-first navigation for critical actions
- [ ] Add semantic labels for assistive technologies
- [ ] Ensure responsive layouts for mobile and tablet
- [ ] Add non-color indicators for state changes and warnings

### Phase 8 done criteria
- [ ] Graph performance remains usable on large branches
- [ ] Critical flows are keyboard-usable and mobile-usable
- [ ] Dual-view sync state is always visible and accurate

## Phase 9 - Operations, Security, and Governance

### G9.1 Observability and SLOs
- [ ] Add structured logs with request/job/branch correlation IDs
- [ ] Add traces across ingestion, retrieval, generation, and orchestration
- [ ] Define SLOs for latency, failure rate, and sync success

### G9.2 Incident readiness
- [ ] Create runbooks for parser, model, and orchestration failures
- [ ] Add failure replay tooling for representative incidents
- [ ] Add postmortem template and recurring incident review

### G9.3 Capacity and cost management
- [ ] Add queue priority classes (interactive vs background)
- [ ] Add per-job and per-branch token/image budgets
- [ ] Add kill switches for runaway workloads

### G9.4 Privacy and retention controls
- [ ] Enforce local-first execution defaults
- [ ] Add explicit external provider opt-in controls
- [ ] Implement log redaction and data retention policies

### G9.5 Legal and license compliance
- [ ] Implement source rights attestation at ingestion
- [ ] Maintain model/checkpoint/adapter license registry
- [ ] Add policy gate before export/share workflows

### G9.6 Mature-content governance
- [ ] Implement policy profiles by deployment context
- [ ] Add explicit confirmation and override logging for high-intensity settings
- [ ] Add review routing for borderline content cases

### Phase 9 done criteria
- [ ] Security, privacy, and compliance checks pass
- [ ] SLO dashboards and alerts are active
- [ ] Budget controls prevent runaway cost

## Phase 10 - Evaluation, Hardening, and Release

### G10.1 Benchmark suite completion
- [ ] Finalize benchmark sets for ingestion, retrieval, narrative, visual, and UX
- [ ] Automate benchmark runs in CI/nightly workflows
- [ ] Track trend lines and regression alerts over time

### G10.2 Release gate verification
- [ ] Ingestion gate passes
- [ ] Retrieval gate passes
- [ ] Narrative gate passes
- [ ] Visual gate passes
- [ ] UX gate passes
- [ ] Security gate passes
- [ ] Privacy/compliance gate passes
- [ ] Operability gate passes
- [ ] Cost gate passes

### G10.3 Beta program and feedback loop
- [ ] Prepare beta test plan with representative user personas
- [ ] Capture structured feedback on tone fidelity and usability
- [ ] Prioritize and close beta-critical issues

### G10.4 Public release readiness
- [ ] Finalize docs (`README.md`, `AGENTS.md`, `STRATEGY.md`, user docs)
- [ ] Tag stable release and publish changelog
- [ ] Define post-release monitoring and patch cadence

### Phase 10 done criteria
- [ ] All release gates pass consistently
- [ ] Beta-critical issues are resolved
- [ ] Release documentation is complete and accurate

## Continuous goals (run across all phases)

### GC.1 Test discipline
- [ ] Write focused tests for each new capability
- [ ] Run narrowest relevant tests first, then broader suites
- [ ] Track flaky tests and eliminate them quickly

### GC.2 Documentation discipline
- [ ] Update docs whenever behavior or interfaces change
- [ ] Keep command docs synced with actual scripts/tooling
- [ ] Keep architectural decisions discoverable in repo docs

### GC.3 Scope discipline
- [ ] Keep each PR scoped to one goal or tightly-related goal slice
- [ ] Avoid unrelated refactors in milestone PRs
- [ ] Record tradeoffs and deferred work explicitly
