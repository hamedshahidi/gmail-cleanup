# Task 003: Create core service layer that wraps existing modules (no rewrite)

## Goal
Expose reusable operations so both CLI and FastAPI can call the same code.

## Constraints
- Keep behavior identical to existing CLI safety model.
- Reuse existing modules (query_builder, gmail, labels, exporter, trash, preview, gmail_iter).
- Do not break the CLI entry point or command behavior.
- Add pytest tests for safety gates.
- No secrets.

## Work
1) Create a new package under `packages/core/`:
   - `packages/core/gmail_cleanup_core/`
   - `__init__.py`

2) Add `models.py`:
   - Define request/response models for:
     - QueryRequest / QueryResult (count totals + samples)
     - LabelRequest / LabelResult
     - ExportRequest / ExportResult
     - TrashRequest / TrashResult
   - Use dataclasses or Pydantic (prefer dataclasses unless validation needed).

3) Add `operations.py`:
   - Implement functions:
     - `run_query(...)`
     - `apply_label(...)`
     - `export_messages(...)`
     - `trash_by_label(...)`
   - These should call existing modules in `gmail_cleanup/*` (no logic rewrite).

4) Enforce safety gates in core:
   - empty query refuses
   - trash requires label prefix `cleanup/`
   - trash dry-run unless execute=True
   - max-trash cap unless force=True

5) Add tests:
   - tests for trash safety gating and empty query refusal
   - tests do NOT call real Gmail API (mock gmail service layer)

## Acceptance criteria
- Core operations exist and are importable.
- Unit tests pass.
- CLI still works unchanged (`gmail-cleanup --help` and at least one dry-run query command).
