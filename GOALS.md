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
- [x] Implement `.txt` parser with encoding normalization
- [x] Implement `.pdf` parser with fallback strategy
- [x] Implement `.epub` parser with chapter extraction support
- [x] Build parser confidence scoring and error reporting

### G1.3 Manga ingestion pipeline
- [x] Implement `ingest_cbz_pages()` for archive-based manga imports
- [x] Implement `ingest_image_folder_pages()` for loose page folders
- [x] Support page formats: `.png`, `.jpg`, `.jpeg`, `.webp`
- [x] Normalize EXIF orientation, color space, and alpha handling
- [x] Apply natural page ordering and spread detection

### G1.4 OCR and page semantics
- [x] Implement OCR baseline on manga pages
- [x] Add OCR fallback/ensemble path for low-confidence pages
- [x] Detect dialogue regions and classify bubble/narration types
- [x] Store OCR text with page coordinates and confidence

### G1.5 Idempotency and deduplication
- [x] Add content hashing for chunks and pages
- [x] Add near-duplicate detection for repeated imports
- [x] Ensure re-ingestion is idempotent by default

### Phase 1 done criteria
- [x] Mixed fixture ingestion success rate meets target
- [x] Per-format decode success (png/jpg/jpeg/webp/cbz) meets target
- [x] Security fixture suite passes

## Phase 2 - Tone, Style, and Maturity Profiling

### G2.1 Text profile extraction
- [x] Implement scene-level sentiment/intensity multi-label tagging
- [x] Add uncertainty scoring for low-confidence classifications
- [x] Detect abrupt tonal shifts and peak intensity moments

### G2.2 Visual profile extraction
- [x] Implement panel-level visual tonal classification
- [x] Add style cues beyond brightness (line density, texture, composition)
- [x] Aggregate panel tone into scene and chapter profiles

### G2.3 Maturity spectrum engine
- [x] Implement maturity/rating score bands with smoothing
- [x] Map score bands to generation parameter presets
- [x] Add explicit user overrides with audit logging

### G2.4 Profile quality controls
- [x] Create correction loop for human profile edits
- [x] Store profile versions and change provenance
- [x] Add profile regression tests with benchmark fixtures

### Phase 2 done criteria
- [x] Profile precision/recall targets met on benchmark scenes
- [x] Tone jitter index remains within tolerance
- [x] Overrides are traceable per branch version

## Phase 3 - Retrieval and Long-Form Memory

### G3.1 Chunking and memory model
- [x] Implement hierarchical chunking (sentence, scene, chapter)
- [x] Attach canonical metadata (story, branch, version, time)
- [x] Build unresolved-thread tracker for narrative memory

### G3.2 Vector index strategy
- [x] Implement branch-aware index namespace partitioning
- [x] Add branch lineage filters in retrieval queries
- [x] Add index compaction and dedup maintenance jobs

### G3.3 Ranking and retrieval quality
- [x] Implement hybrid retrieval (BM25 + embedding)
- [x] Add reranking layer for canon relevance
- [x] Track retrieval metrics (Precision@K, MRR, nDCG)

### G3.4 Freshness and incremental updates
- [x] Implement incremental re-embedding on edits
- [x] Mark stale chunks and suppress stale retrieval hits
- [x] Add retrieval invalidation tests for branch rewrites

### G3.5 Performance and cost controls
- [x] Add query/result caching layers
- [x] Add retrieval budget controls per request
- [x] Track p95 latency and retrieval cost per query

### Phase 3 done criteria
- [x] Wrong-branch retrieval incidence is near zero
- [x] Retrieval quality beats baseline method
- [x] p95 retrieval latency and cost are within target

## Phase 4 - Story Graph and Branching Core

### G4.1 Event extraction and normalization
- [x] Build hybrid event extraction pipeline
- [x] Normalize event schema and confidence fields
- [x] Add duplicate event merge logic

### G4.2 Entity and relation integrity
- [x] Implement canonical entity IDs with alias graph
- [x] Add relation extraction for causality and dependencies
- [x] Add conflict detection for entity-state contradictions

### G4.3 Temporal and causal ordering
- [x] Infer chronological ordering beyond source order
- [x] Add contradiction detector for impossible sequences
- [x] Add repair workflow for ordering errors

### G4.4 Divergence and branch lifecycle
- [x] Implement divergence node creation and lineage tracking
- [x] Add system recommendations for high-impact branch points
- [x] Add branch budgets and archive/merge workflows

### G4.5 Consequence simulation
- [x] Implement affected-subgraph recompute pipeline
- [x] Add hard canon constraints and soft style penalties
- [x] Track downstream consistency versus baseline recompute

### G4.6 Graph persistence and migration
- [x] Version graph schema explicitly
- [x] Add replayable migrations with rollback checkpoints
- [x] Add migration tests against historical snapshots

### Phase 4 done criteria
- [x] Event/temporal quality targets met
- [x] Branch lineage and consequence simulation remain consistent
- [x] Schema migrations pass replay tests

## Phase 5 - Text Generation Engine

### G5.1 Writer agent baseline
- [x] Implement Writer Agent interface and contract tests
- [x] Add branch-aware context assembly from retrieval
- [x] Add deterministic generation mode for tests

### G5.2 Style fidelity controls
- [x] Implement style profile embeddings
- [x] Add style exemplar retrieval and prompt grounding
- [x] Track style similarity metrics against source windows

### G5.3 Character voice integrity
- [x] Create per-character voice cards
- [x] Enforce dialogue/voice constraints in generation
- [x] Add voice confusion regression tests

### G5.4 Long-range coherence
- [x] Implement unresolved-thread carryover checks
- [x] Add arc/chapter memory summaries into generation context
- [x] Add contradiction checks after chapter generation

### G5.5 Prompt governance and safety
- [x] Create versioned prompt registry with rollback
- [x] Enforce strict system/developer/user prompt layering
- [x] Implement prompt injection defense tests using hostile fixtures

### G5.6 Tuner mapping for text
- [x] Map violence/humor/romance controls with calibrated curves
- [x] Add expected-impact preview for slider changes
- [x] Validate user expectation match in tuning tests

### Phase 5 done criteria
- [x] Style and voice targets met on benchmark stories
- [x] Long-range contradiction rate below threshold
- [x] Prompt version and provenance are fully traceable

## Phase 6 - Manga/Image Generation Engine

### G6.1 Artist agent baseline
- [x] Implement Artist Agent interface and job contract
- [x] Integrate diffusion backend with ControlNet-compatible flow
- [x] Add deterministic seed support and artifact metadata

### G6.2 Panel continuity and scene planning
- [x] Build shared scene blueprint for panel sequences
- [x] Add continuity anchors (camera, pose, environment, props)
- [x] Validate continuity across 4-panel outputs

### G6.3 Atmosphere and tone controls
- [x] Implement atmosphere presets for light/dark ranges
- [x] Add explicit lighting and texture constraints
- [x] Validate readability for high-contrast and dark scenes

### G6.4 Character identity consistency
- [x] Build identity packs (face/silhouette/costume cues)
- [x] Add LoRA/adaptor management and training hooks
- [x] Add drift detection and retraining triggers

### G6.5 Visual quality guardrails
- [x] Implement anatomy/composition QC scoring
- [x] Add correction loop and selective redraw flow
- [x] Track rejection and final pass rates

### G6.6 Cross-modal alignment
- [x] Use shared structured scene plans for text + image
- [x] Add mismatch detection between prose and panel semantics
- [x] Add reconcile workflow when modalities diverge

### Phase 6 done criteria
- [x] Panel continuity and identity metrics meet target
- [x] Atmosphere control behaves predictably
- [x] Cross-modal mismatch rate stays within threshold

## Phase 7 - Orchestration and State Integrity

### G7.1 Director agent contracts
- [x] Define strict typed contracts for all agent inputs/outputs
- [x] Add contract test suite in CI
- [x] Add compatibility matrix for model and workflow versions

### G7.2 Job orchestration reliability
- [x] Add idempotency keys for generation jobs
- [x] Implement transactional state transitions per branch version
- [x] Add bounded retry policies and dead-letter handling

### G7.3 Edit provenance and regeneration
- [x] Implement event-sourced edit log for text and panels
- [x] Scope regeneration to affected spans/panels
- [x] Prevent overwrite of user edits in async reruns

### G7.4 Sync semantics for dual outputs
- [x] Add shared scene/version IDs across modalities
- [x] Add stale-state indicators and reconcile actions
- [x] Add sync regression tests for async race scenarios

### Phase 7 done criteria
- [x] Duplicate lineage IDs remain zero
- [x] Recovery from partial failures is reliable
- [x] Edit provenance remains complete and queryable

## Phase 8 - Frontend and User Workflow

### G8.1 Interactive graph UX
- [x] Implement node graph rendering with virtualization
- [x] Add semantic zoom modes (overview/scene/detail)
- [x] Add undo/redo and autosave checkpoints

### G8.2 Branching workflow UX
- [x] Add branch creation from any node
- [x] Show branch lineage and impact previews
- [x] Add branch archive/merge actions

### G8.3 Tuner and control panel
- [x] Implement violence/humor/romance controls
- [x] Add control precedence rules and preview
- [x] Add warnings for extreme settings

### G8.4 Dual-view and Director Mode
- [x] Implement text + manga split view
- [x] Add explicit sync status and stale content badges
- [x] Implement sentence edit and panel redraw workflows

### G8.5 Accessibility and mobile readiness
- [x] Add keyboard-first navigation for critical actions
- [x] Add semantic labels for assistive technologies
- [x] Ensure responsive layouts for mobile and tablet
- [x] Add non-color indicators for state changes and warnings

### Phase 8 done criteria
- [x] Graph performance remains usable on large branches
- [x] Critical flows are keyboard-usable and mobile-usable
- [x] Dual-view sync state is always visible and accurate

## Phase 9 - Operations, Security, and Governance

### G9.1 Observability and SLOs
- [x] Add structured logs with request/job/branch correlation IDs
- [x] Add traces across ingestion, retrieval, generation, and orchestration
- [x] Define SLOs for latency, failure rate, and sync success

### G9.2 Incident readiness
- [x] Create runbooks for parser, model, and orchestration failures
- [x] Add failure replay tooling for representative incidents
- [x] Add postmortem template and recurring incident review

### G9.3 Capacity and cost management
- [x] Add queue priority classes (interactive vs background)
- [x] Add per-job and per-branch token/image budgets
- [x] Add kill switches for runaway workloads

### G9.4 Privacy and retention controls
- [x] Enforce local-first execution defaults
- [x] Add explicit external provider opt-in controls
- [x] Implement log redaction and data retention policies

### G9.5 Legal and license compliance
- [x] Implement source rights attestation at ingestion
- [x] Maintain model/checkpoint/adapter license registry
- [x] Add policy gate before export/share workflows

### G9.6 Mature-content governance
- [x] Implement policy profiles by deployment context
- [x] Add explicit confirmation and override logging for high-intensity settings
- [x] Add review routing for borderline content cases

### Phase 9 done criteria
- [x] Security, privacy, and compliance checks pass
- [x] SLO dashboards and alerts are active
- [x] Budget controls prevent runaway cost

## Phase 10 - Evaluation, Hardening, and Release

### G10.1 Benchmark suite completion
- [x] Finalize benchmark sets for ingestion, retrieval, narrative, visual, and UX
- [x] Automate benchmark runs in CI/nightly workflows
- [x] Track trend lines and regression alerts over time

### G10.2 Release gate verification
- [x] Ingestion gate passes
- [x] Retrieval gate passes
- [x] Narrative gate passes
- [x] Visual gate passes
- [x] UX gate passes
- [x] Security gate passes
- [x] Privacy/compliance gate passes
- [x] Operability gate passes
- [x] Cost gate passes

### G10.3 Beta program and feedback loop
- [x] Prepare beta test plan with representative user personas
- [x] Capture structured feedback on tone fidelity and usability
- [x] Prioritize and close beta-critical issues

### G10.4 Public release readiness
- [x] Finalize docs (`README.md`, `AGENTS.md`, `STRATEGY.md`, user docs)
- [x] Tag stable release and publish changelog
- [x] Define post-release monitoring and patch cadence

### Phase 10 done criteria
- [x] All release gates pass consistently
- [x] Beta-critical issues are resolved
- [x] Release documentation is complete and accurate

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
