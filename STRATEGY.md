# STRATEGY.md

Problem-first strategy for The Loom.

## 1) Document Intent

This file is not a feature wishlist. It is a dissection of the project into small,
concrete problem statements. For each problem, it records:

- the problem statement
- the possibility space
- the proposed solution
- the first validation signal

Use this as the execution map for planning, implementation, and reviews.

## 2) Working Method

For each problem statement in this document:

1. Explore at least 2-3 viable implementation paths.
2. Choose one primary approach and one fallback path.
3. Define a measurable validation signal.
4. Keep decisions reversible unless data proves otherwise.

## 3) Global Constraints From PRD

- Tone fidelity is the product core (no default tonal flattening).
- Branching logic is first-class (not a side feature).
- Text and manga outputs must stay synchronized.
- Local-first execution and privacy are default assumptions.
- Manga ingestion must support `.cbz` and loose image folders (`.png`, `.jpg`/`.jpeg`, `.webp`).
- Mature-content capability is required, with explicit governance controls.

## 4) Problem Statements and Proposed Solutions

### Domain A: Ingestion and Profiling

#### PS-01: File trust boundary
Problem statement: Ingestion accepts complex file types (`.pdf`, `.epub`, `.cbz`) that can carry malicious payloads.
Possibilities: (A) permissive parsing with warnings, (B) strict allowlist without sandboxing, (C) sandboxed parsing plus strict validation.
Proposed solution: Use option C with size limits, MIME checks, and archive path traversal guards.
Validation signal: Security test suite catches known malicious fixtures with zero escapes.

#### PS-02: Parser reliability across formats
Problem statement: A single parser per format will fail on edge-case documents.
Possibilities: (A) one parser only, (B) parser fallback chain, (C) fallback chain plus manual recovery states.
Proposed solution: Use B + C with parser confidence scoring.
Validation signal: Parse completeness and structural integrity exceed target per format.

#### PS-03: Text normalization fidelity
Problem statement: Encoding noise and layout artifacts degrade downstream NLP and retrieval.
Possibilities: (A) raw text ingestion, (B) deterministic normalization pipeline, (C) aggressive rewrite normalization.
Proposed solution: Use B; avoid C to preserve author voice.
Validation signal: Encoding-error rate and tokenization failures trend toward zero.

#### PS-04: Chapter and scene segmentation
Problem statement: Poor segmentation corrupts branch points and memory retrieval.
Possibilities: (A) rule-based split only, (B) model-based split only, (C) hybrid segmentation with confidence.
Proposed solution: Use C and flag low-confidence boundaries for review.
Validation signal: Segmentation F1 on annotated corpora meets threshold.

#### PS-05: Idempotent ingestion and deduplication
Problem statement: Re-importing the same source creates duplicate chunks and noisy memory.
Possibilities: (A) no dedup, (B) hash-based dedup only, (C) hash + semantic near-duplicate detection.
Proposed solution: Use C with branch-aware duplicate policy.
Validation signal: Duplicate chunk rate remains near zero after repeated imports.

#### PS-06: Manga page source handling, format decoding, and ordering
Problem statement: Manga pages arrive either in `.cbz` archives or as loose image files; format decoding (`.png`, `.jpg`/`.jpeg`, `.webp`), EXIF orientation, and inconsistent naming can break ingestion chronology.
Possibilities: (A) support archive input only, (B) support archives and folders with one decoder path, (C) dual ingestion methods (`.cbz` extractor + folder walker) with format-aware decode/normalization and ordering safeguards.
Proposed solution: Use C. Build two explicit ingest methods: `ingest_cbz_pages()` and `ingest_image_folder_pages()`; support `.png`, `.jpg`, `.jpeg`, `.webp`; apply orientation fix, colorspace normalization, alpha flattening rules, and natural page ordering.
Validation signal: Per-format decode success rate (`png/jpg/jpeg/webp`) and page-order accuracy both exceed target on mixed-source test sets.

#### PS-07: OCR quality on stylized text
Problem statement: Stylized fonts, rotated bubbles, and low-resolution scans reduce OCR quality.
Possibilities: (A) single OCR engine, (B) OCR ensemble voting, (C) ensemble plus pre-processing and confidence routing.
Proposed solution: Use C.
Validation signal: Character error rate and low-confidence share remain within thresholds.

#### PS-08: Dialogue region type and speaker alignment
Problem statement: Speech, thought, and narration are conflated; speaker attribution drifts.
Possibilities: (A) pure OCR text extraction, (B) bubble-type classifier + geometry rules, (C) multimodal speaker linking.
Proposed solution: Use B now, evolve to C.
Validation signal: Dialogue-type and speaker-link accuracy improve each release.

#### PS-09: Visual tonal profiling
Problem statement: Brightness-only heuristics misclassify style and mood.
Possibilities: (A) brightness/contrast heuristics, (B) multimodal style classifier, (C) B plus human correction loop.
Proposed solution: Use C.
Validation signal: Panel-level style F1 and correction acceptance rate.

#### PS-10: Maturity profile stability
Problem statement: Scene-to-scene maturity scoring jitters and destabilizes generation.
Possibilities: (A) per-scene raw score, (B) smoothed score bands, (C) smoothed bands plus user override.
Proposed solution: Use C with explicit override logs.
Validation signal: Tone jitter index stays under configured tolerance.

### Domain B: Retrieval and Long-Form Memory

#### PS-11: Chunk size and structure
Problem statement: Poor chunking harms recall and context relevance.
Possibilities: (A) fixed token chunks, (B) scene-aware chunks, (C) hierarchical chunks (sentence, scene, chapter).
Proposed solution: Use C.
Validation signal: Retrieval precision improves versus fixed-size baseline.

#### PS-12: Branch-aware index namespace
Problem statement: Retrieval leaks context across branches.
Possibilities: (A) one global index, (B) branch filters at query time, (C) namespace partitioning by story/branch/version.
Proposed solution: Use C with query-time lineage filters.
Validation signal: Wrong-branch retrieval incidence stays near zero.

#### PS-13: Stale index after edits
Problem statement: Branch edits invalidate embeddings but index stays stale.
Possibilities: (A) full reindex always, (B) incremental reindex, (C) incremental + stale-chunk quarantine.
Proposed solution: Use C.
Validation signal: Stale retrieval hits remain below threshold.

#### PS-14: Ranking strategy
Problem statement: Embedding-only retrieval misses lexical anchors and canon facts.
Possibilities: (A) embedding-only, (B) BM25-only, (C) hybrid retrieval + reranking.
Proposed solution: Use C.
Validation signal: MRR and nDCG outperform single-method baselines.

#### PS-15: Memory architecture for 2M+ words
Problem statement: Flat memory does not scale for long sagas.
Possibilities: (A) one memory store, (B) chapter-level summaries, (C) hierarchical memory graph (scene/chapter/arc) with lazy fetch.
Proposed solution: Use C.
Validation signal: Coherence score and latency remain stable with corpus growth.

#### PS-16: Retrieval cost and latency control
Problem statement: Long queries and reranking can become expensive and slow.
Possibilities: (A) no cache, (B) query cache only, (C) multi-layer cache plus query budget controls.
Proposed solution: Use C.
Validation signal: p95 retrieval latency and cost-per-query stay in target band.

### Domain C: Story Graph and Branch Logic

#### PS-17: Event extraction coverage
Problem statement: Implicit events are missed, causing logic gaps.
Possibilities: (A) rule extraction, (B) LLM extraction, (C) hybrid extraction with confidence scoring.
Proposed solution: Use C.
Validation signal: Event recall against annotated scenes.

#### PS-18: Entity resolution and aliasing
Problem statement: Characters with aliases or title changes split into separate entities.
Possibilities: (A) exact string matching, (B) embedding matching, (C) canonical entity ids with alias graph.
Proposed solution: Use C.
Validation signal: Entity-merge precision and split-error rate.

#### PS-19: Temporal and causal ordering
Problem statement: Nonlinear narratives produce wrong chronology.
Possibilities: (A) source-order assumption, (B) temporal extraction model, (C) temporal model + contradiction detector.
Proposed solution: Use C.
Validation signal: Temporal contradiction count per 100 events.

#### PS-20: Event node granularity
Problem statement: Too fine nodes create noise; too coarse nodes reduce branch control.
Possibilities: (A) sentence-level nodes, (B) chapter-level nodes, (C) adaptive granularity by scene complexity.
Proposed solution: Use C with user-controlled zoom.
Validation signal: Branch edit success rate and user correction frequency.

#### PS-21: Divergence point quality
Problem statement: Branching at low-impact points produces weak alternatives.
Possibilities: (A) user picks any node, (B) system recommends high-impact nodes, (C) recommendations + impact preview.
Proposed solution: Use C.
Validation signal: User adoption of recommendations and branch distinctiveness score.

#### PS-22: Branch explosion
Problem statement: Unbounded branching harms usability and compute budgets.
Possibilities: (A) no limits, (B) hard branch cap, (C) soft budgets with archive/merge guidance.
Proposed solution: Use C.
Validation signal: Active branch count remains within UX threshold.

#### PS-23: Consequence propagation depth
Problem statement: Local edits do not correctly affect downstream events.
Possibilities: (A) local recompute only, (B) full branch recompute, (C) affected-subgraph recompute with dependency tracking.
Proposed solution: Use C.
Validation signal: Downstream consistency score versus full recompute baseline.

#### PS-24: Canon constraints and continuity
Problem statement: Generated branches violate character canon and world rules.
Possibilities: (A) prompt reminders only, (B) hard constraints only, (C) hard constraints plus soft style penalties.
Proposed solution: Use C.
Validation signal: Canon-violation rate per branch.

#### PS-25: Graph schema versioning and migration
Problem statement: Graph/profile schema changes break old projects.
Possibilities: (A) no versioning, (B) forward-only migration, (C) explicit schema versions + replayable migrations + rollback.
Proposed solution: Use C.
Validation signal: Migration replay success on historical snapshots.

### Domain D: Text Generation

#### PS-26: Style mimicry beyond vocabulary
Problem statement: Output copies words but misses cadence and narrative rhythm.
Possibilities: (A) prompt-only mimicry, (B) style embedding controls, (C) style embeddings + retrieval exemplars.
Proposed solution: Use C.
Validation signal: Style similarity score and human preference results.

#### PS-27: Character voice separation
Problem statement: Distinct characters converge into one narrator voice.
Possibilities: (A) no voice model, (B) per-character voice cards, (C) voice cards + dialogue constraint checks.
Proposed solution: Use C.
Validation signal: Voice confusion rate across sampled dialogues.

#### PS-28: Long-range coherence
Problem statement: Chapters loop, contradict, or forget unresolved arcs.
Possibilities: (A) large context only, (B) summary memory only, (C) hierarchical memory + unresolved-thread tracker.
Proposed solution: Use C.
Validation signal: Plot contradiction rate and unresolved-thread closure rate.

#### PS-29: Intensity slider mapping to text behavior
Problem statement: User sliders produce nonlinear and surprising output changes.
Possibilities: (A) direct parameter mapping, (B) rule-based mapping, (C) calibrated curves with preview deltas.
Proposed solution: Use C.
Validation signal: User expectation match score in tuning tests.

#### PS-30: Prompt version management
Problem statement: Prompt edits silently alter behavior and complicate debugging.
Possibilities: (A) unversioned prompts, (B) semantic version tags, (C) versioned prompt registry with changelog and rollback.
Proposed solution: Use C.
Validation signal: Every artifact can be traced to exact prompt version.

#### PS-31: Prompt injection and source contamination
Problem statement: Ingested text can include hostile instructions.
Possibilities: (A) ignore risk, (B) heuristic filtering, (C) strict prompt isolation plus red-team tests.
Proposed solution: Use C.
Validation signal: Injection benchmark pass rate meets release threshold.

### Domain E: Manga and Image Generation

#### PS-32: Panel sequence continuity
Problem statement: Consecutive panels drift in camera, pose, and environment.
Possibilities: (A) generate panels independently, (B) sequential conditioning, (C) shared scene blueprint + continuity anchors.
Proposed solution: Use C.
Validation signal: Panel continuity score across 4-panel sequences.

#### PS-33: Atmosphere control
Problem statement: "Dark" scenes become muddy rather than intentional.
Possibilities: (A) keyword prompts only, (B) style presets, (C) style presets + lighting/texture constraints.
Proposed solution: Use C.
Validation signal: Human-rated atmosphere accuracy and readability.

#### PS-34: Anatomy, action, and composition errors
Problem statement: Action-heavy scenes produce visual artifacts.
Possibilities: (A) accept raw output, (B) post-filter scoring, (C) post-filter + corrective redraw loop.
Proposed solution: Use C.
Validation signal: Artifact rejection rate and final pass quality.

#### PS-35: Character identity persistence
Problem statement: Character appearance drifts across emotion extremes and battle states.
Possibilities: (A) text prompts only, (B) LoRA only, (C) identity pack + LoRA + reference conditioning.
Proposed solution: Use C.
Validation signal: Identity consistency metric across scenes.

#### PS-36: LoRA lifecycle and overfitting
Problem statement: Frequent training can overfit and reduce generalization.
Possibilities: (A) train per project ad hoc, (B) reusable adapters, (C) adapter registry with drift-triggered retraining.
Proposed solution: Use C.
Validation signal: Retrain frequency and adapter reuse ratio.

#### PS-37: Text-image semantic alignment
Problem statement: Generated panel content can diverge from generated prose.
Possibilities: (A) separate text and image prompts, (B) shared scene summary, (C) structured scene plan consumed by both modalities.
Proposed solution: Use C.
Validation signal: Cross-modal alignment score and mismatch incidence.

### Domain F: Orchestration and UX

#### PS-38: Agent contract consistency
Problem statement: Agent handoffs fail when schemas drift.
Possibilities: (A) informal JSON, (B) typed schemas only, (C) typed schemas + contract tests in CI.
Proposed solution: Use C.
Validation signal: Contract breakage rate trends toward zero.

#### PS-39: Retry safety and idempotency
Problem statement: Retries duplicate work and corrupt lineage.
Possibilities: (A) naive retries, (B) retry with locks, (C) idempotency keys + transactional state transitions.
Proposed solution: Use C.
Validation signal: Duplicate lineage id count remains zero.

#### PS-40: Director Mode edit provenance
Problem statement: Manual edits are hard to trace and can be overwritten.
Possibilities: (A) mutable state only, (B) append-only edit log, (C) event-sourced edit log + scoped regeneration.
Proposed solution: Use C.
Validation signal: Edit lineage completeness and overwrite incident rate.

#### PS-41: Dual-view synchronization
Problem statement: Text and manga panes desynchronize under async generation.
Possibilities: (A) independent jobs, (B) shared job id, (C) shared scene/version id with stale-state indicators.
Proposed solution: Use C.
Validation signal: Desync incidence per user session.

#### PS-42: Graph rendering scalability
Problem statement: Large branch trees degrade frame rate and usability.
Possibilities: (A) full render always, (B) virtualized render, (C) virtualized render + level-of-detail zoom.
Proposed solution: Use C.
Validation signal: Frame rate and interaction latency on large graphs.

#### PS-43: Tuner control usability
Problem statement: Multiple sliders conflict without clear precedence.
Possibilities: (A) independent sliders, (B) hard precedence rules, (C) precedence rules + "impact preview" panel.
Proposed solution: Use C.
Validation signal: Regeneration attempts per scene and user confidence scores.

#### PS-44: Accessibility, mobile support, and undo
Problem statement: Graph-heavy UI can exclude keyboard-only, screen-reader, and mobile users.
Possibilities: (A) desktop-first only, (B) responsive UI only, (C) WCAG target + keyboard flows + responsive layouts + robust undo/redo.
Proposed solution: Use C.
Validation signal: A11y checks pass and mobile critical-path completion rate.

### Domain G: Platform Operations, Security, and Governance

#### PS-45: Model selection under hardware limits
Problem statement: VRAM and context limits cause OOM and unstable performance.
Possibilities: (A) fixed default model, (B) user-selected model, (C) capability matrix + preflight memory estimator + fallback chain.
Proposed solution: Use C.
Validation signal: OOM failure rate and fallback success rate.

#### PS-46: Queueing and workload scheduling
Problem statement: Interactive requests compete with batch jobs.
Possibilities: (A) single queue, (B) priority queue, (C) priority queue + concurrency budgets per workload class.
Proposed solution: Use C.
Validation signal: p95 queue wait for interactive jobs.

#### PS-47: Observability and SLO instrumentation
Problem statement: Multi-agent failures are opaque without tracing and shared ids.
Possibilities: (A) logs only, (B) metrics only, (C) structured logs + traces + metrics with SLO alerts.
Proposed solution: Use C.
Validation signal: Alert precision and trace coverage on critical flows.

#### PS-48: Incident response readiness
Problem statement: Failures repeat without playbooks and replay tooling.
Possibilities: (A) ad hoc debugging, (B) static runbooks, (C) runbooks + failure replay and postmortem templates.
Proposed solution: Use C.
Validation signal: MTTR and repeat-incident rate.

#### PS-49: Cost governance
Problem statement: Branch expansion and multimodal generation can create runaway cost.
Possibilities: (A) no budget controls, (B) per-user quotas, (C) per-job/branch budgets + forecasting + kill switches.
Proposed solution: Use C.
Validation signal: Cost per successful branch and budget breach frequency.

#### PS-50: Privacy and data retention
Problem statement: Sensitive story data can leak via logs, caches, or external providers.
Possibilities: (A) best-effort privacy, (B) local-only mode, (C) local-first defaults + explicit provider opt-in + redaction + retention policy.
Proposed solution: Use C.
Validation signal: Privacy audit pass rate and retention policy compliance.

#### PS-51: Legal rights and model licensing
Problem statement: Ingested sources and model assets may have incompatible rights.
Possibilities: (A) trust user implicitly, (B) warn only, (C) rights attestation + model-license registry + policy gates.
Proposed solution: Use C.
Validation signal: Compliance gate pass and complete provenance records.

#### PS-52: Mature content governance
Problem statement: Mature-content capability must be available but controlled by context and policy.
Possibilities: (A) no policy controls, (B) hard global blocking, (C) configurable policy profiles + override logs + review routing.
Proposed solution: Use C.
Validation signal: Governance benchmark false-positive/false-negative rates.

#### PS-53: Evaluation harness and regression discipline
Problem statement: Without standardized evaluation, quality regresses silently.
Possibilities: (A) manual spot checks, (B) per-feature tests only, (C) benchmark suites + release gates + longitudinal tracking.
Proposed solution: Use C.
Validation signal: Gate pass rate and regression detection lead time.

#### PS-54: Definition of done for each milestone
Problem statement: Teams can "ship" without consistent completion criteria.
Possibilities: (A) informal sign-off, (B) engineering-only checklist, (C) cross-functional done criteria tied to gates.
Proposed solution: Use C.
Validation signal: Reduced rollback rate and higher first-pass acceptance.

## 5) Dependency-Aware Execution Order

Build in this order so later solutions have stable foundations:

1. Trust boundaries, ingestion reliability, and profile stability (PS-01..PS-10).
2. Retrieval and memory correctness (PS-11..PS-16).
3. Graph logic and branch semantics (PS-17..PS-25).
4. Text generation quality and safety controls (PS-26..PS-31).
5. Image generation and cross-modal alignment (PS-32..PS-37).
6. Orchestration and UX reliability (PS-38..PS-44).
7. Platform, governance, and release discipline (PS-45..PS-54).

## 6) Release Gate Bundle (Must Pass Before Public Expansion)

- Ingestion gate: parser safety, completeness, deduplication.
- Retrieval gate: branch-scoped precision, latency, stale-index control.
- Narrative gate: continuity, canon adherence, contradiction limits.
- Visual gate: panel continuity, identity consistency, readability.
- UX gate: graph performance, tuner predictability, dual-view sync.
- Security gate: ingestion hardening and prompt-injection resistance.
- Privacy/compliance gate: retention, rights attestation, license conformance.
- Operability gate: traces, SLOs, incident readiness.
- Cost gate: budget adherence and queue health.

## 7) How To Keep This Document Useful

- Add new problem statements instead of bloating existing ones.
- Keep each statement atomic and testable.
- Record when a proposed solution changes and why.
- Link implementation tasks to problem IDs (for example, `PS-23`).
- Retire solved problems only when validation signals are stable.
