# AGENTS.md
Repository operating guide for coding agents in `The-Loom`.

## 1) Repository Snapshot
- Repository now has phase-zero scaffolding plus project docs.
- Core docs include `README.md`, `PRD.md`, `STRATEGY.md`, `GOALS.md`, `AGENTS.md`.
- Base directories exist: `agents/`, `core/`, `tests/`, `ui/`, `models/`, `scripts/`, `docs/`.
- Python tooling is configured via `pyproject.toml`, `requirements.txt`, `Makefile`, and CI.
- Use this file as the default engineering policy while implementation expands.

## 2) Cursor/Copilot Rule Check
- `.cursorrules`: not found
- `.cursor/rules/`: not found
- `.github/copilot-instructions.md`: not found
- Therefore, no repo-level Cursor/Copilot instructions exist yet.
- Treat `AGENTS.md` as the primary rule source for agents.

## 3) Build, Lint, and Test Commands
Commands are split into:
1. baseline commands that work now
2. Python development commands (configured)
3. optional frontend commands when `package.json` exists

### 3.1 Commands That Work Right Now
```bash
ls
git status -sb
git ls-tree -r --name-only HEAD
make lint
make test
```

### 3.2 Python Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3.3 Build Commands (Python)
Use whichever target exists:
```bash
python -m build
make build
```
- If neither command is configured, report build as "not configured".

### 3.4 Lint, Format, Typecheck (Python)
Preferred defaults:
```bash
ruff check .
ruff check . --fix
black .
mypy .
```
- Run `mypy` only if mypy config/dependency is present.

### 3.5 Test Commands (Python)
```bash
pytest -q
pytest tests/test_example.py -q
pytest tests/test_example.py::test_specific_behavior -q
pytest -k "branching and not slow" -q
pytest -x -q
```
Single-test guidance (important):
- First run the narrowest relevant test (`file::test_name`).
- Then run a broader subset or full suite before final handoff.

### 3.6 Optional Frontend Commands (Only If `package.json` Exists)
```bash
npm install
npm run lint
npm run typecheck
npm test
npm test -- src/path/file.test.ts
npm test -- -t "renders branch node"
```

## 4) Code Style Guidelines
These defaults apply unless stricter local config is added later.

### 4.1 General Principles
- Prefer clear, explicit code over clever shortcuts.
- Keep functions small and single-purpose.
- Keep module boundaries explicit.
- Make side effects obvious and localized.
- Avoid hidden global state and implicit mutations.
- Keep changes focused; avoid unrelated refactors.

### 4.2 Imports
- Order imports: standard library, third-party, local project.
- Use one blank line between import groups.
- Prefer absolute imports over deep relative imports.
- Do not use wildcard imports (`from x import *`).
- Remove unused imports.

### 4.3 Formatting
- Use `black` defaults for Python formatting.
- Use `ruff` for linting and import hygiene.
- Favor readability over dense one-liners.
- End files with a single newline.
- Avoid trailing whitespace.

### 4.4 Types
- Add type hints to public functions and methods.
- Add return types to non-trivial internal helpers.
- Prefer precise types (`list[str]`, `dict[str, Any]`) over bare containers.
- Avoid `Any` where practical; justify it when necessary.
- Use `dataclass`, `TypedDict`, or pydantic models for structured payloads.

### 4.5 Naming Conventions
- Modules/files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private helpers: `_leading_underscore`
- Test files: `test_*.py`
- Test names should describe behavior, not implementation details.

### 4.6 Error Handling
- Catch specific exceptions.
- Never use bare `except:`.
- Validate external input early.
- Fail fast with context-rich messages.
- Raise domain-appropriate exceptions.
- Log once at system boundaries (CLI/API/job), not in every layer.
- Do not swallow failures silently.

### 4.7 Testing Practices
- Use `pytest` style arrange/act/assert.
- Keep unit tests deterministic and fast.
- Mock only external boundaries (network, filesystem, model APIs).
- Cover failure paths as well as success paths.
- Reuse fixtures for shared setup.
- Keep each test focused on one behavior.

### 4.8 Documentation Practices
- Update docs when behavior or interfaces change.
- Keep command docs aligned with actual project scripts.
- Add concise docstrings where logic is non-obvious.
- Document assumptions, constraints, and edge cases.

## 5) Agent Workflow Expectations
- Inspect existing files before deciding conventions.
- Follow existing project patterns first; use this file when patterns are missing.
- Run the smallest relevant validation first.
- Escalate to broader checks before finalizing.
- If a command cannot run (tooling missing), state that explicitly.
- Do not commit secrets, credentials, or local environment artifacts.
- Keep diffs review-friendly and scoped to the requested change.

## 6) Definition of Done
- Code follows import, naming, formatting, typing, and error-handling standards.
- Relevant lint/format/type checks pass, or skipped checks are documented.
- Relevant tests pass, including at least one targeted test run during iteration.
- Docs are updated for behavior, config, or interface changes.
- No unrelated changes are bundled into the same patch.

## 7) Recommended Scaffolding Baseline
When implementation starts, add these early for reliable agent execution:
1. `pyproject.toml` with `ruff`, `black`, `pytest`, optional `mypy` config
2. dependency lock strategy (`requirements.txt`, `uv.lock`, or equivalent)
3. `tests/` with at least one smoke test
4. `Makefile` or task runner targets: `build`, `lint`, `format`, `test`
