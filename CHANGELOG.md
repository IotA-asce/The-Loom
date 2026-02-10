# Changelog

All notable changes to The Loom will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - The Weaver - 2026-02-10

### Summary

Initial stable release of The Loom, a Python-first storytelling framework for branching narratives with coordinated AI agents. All ten implementation phases are complete.

### Phase Completion

- ✅ Phase 0: Project Foundation
- ✅ Phase 1: Safe, Reliable Ingestion
- ✅ Phase 2: Tone, Style, and Maturity Profiling
- ✅ Phase 3: Retrieval and Long-Form Memory
- ✅ Phase 4: Story Graph and Branching Core
- ✅ Phase 5: Text Generation Engine
- ✅ Phase 6: Manga/Image Generation Engine
- ✅ Phase 7: Orchestration and State Integrity
- ✅ Phase 8: Frontend and User Workflow
- ✅ Phase 9: Operations, Security, and Governance
- ✅ Phase 10: Evaluation, Hardening, and Release

### Added

#### Core Features
- **Multi-Format Ingestion**: Parse `.txt`, `.pdf`, `.epub`, `.cbz`, and image folders
- **Tone Preservation**: Analyze and replicate any genre from children's tales to mature fiction
- **Branching Narratives**: Create alternate timelines with navigable "Tree of Possibilities"
- **Prose Generation**: Style-faithful text with character voice integrity
- **Manga Generation**: Panel sequences with atmosphere control and identity consistency
- **State Integrity**: Event-sourced edit logs, idempotent jobs, cross-modal synchronization

#### Phase 8: Frontend (NEW)
- Interactive graph UX with virtualization and semantic zoom
- Branching workflow with creation, impact preview, archive/merge
- Tuner panel with violence/humor/romance controls
- Dual-view text + manga editor with sync badges
- Keyboard navigation and mobile-responsive layouts

#### Phase 9: Operations (NEW)
- Structured logging with correlation IDs and distributed tracing
- SLO monitoring for latency, success rate, and sync success
- Incident runbooks for parser, model, and orchestration failures
- Capacity management with budgets and kill switches
- Privacy controls with local-first defaults and PII redaction
- Legal compliance with source attestation and license registry
- Content governance with policy profiles and review queues

#### Phase 10: Evaluation (NEW)
- Comprehensive benchmark suite (20+ benchmarks)
- Release gate verification (9 gates)
- Beta program with user personas and feedback loop
- Release readiness checker and changelog generation

### Technical Details

#### Repository Statistics
- **Total Lines of Code**: ~25,000
- **Test Coverage**: 160 tests across all phases
- **Core Modules**: 11 engines
- **Test Files**: 15 test suites

#### Performance Benchmarks
- Text ingestion: < 100ms for 10KB files
- PDF ingestion: < 2s for 1MB files
- Vector retrieval: < 50ms P95
- Graph render: < 16ms frame time
- Image generation: < 5s per panel

#### Security & Privacy
- File sandboxing with size and timeout limits
- Zip bomb and path traversal protection
- PII redaction (email, phone, SSN, IP)
- Data retention policies with automatic enforcement
- External provider opt-in controls

### Documentation

- `README.md` - Project overview and quick start
- `AGENTS.md` - Engineering conventions for contributors
- `STRATEGY.md` - Problem-first architecture decisions
- `GOALS.md` - Implementation roadmap and checklist
- `PRD.md` - Product requirements document
- `CHANGELOG.md` - This file

### Contributors

This release represents the foundational implementation of The Loom.

---

## Release Notes Template

### [Unreleased]

### Added
- New features

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Now removed features

### Fixed
- Bug fixes

### Security
- Security improvements
