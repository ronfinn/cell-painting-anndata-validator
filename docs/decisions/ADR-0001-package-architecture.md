# ADR-0001 — Package architecture and public API boundary

- **Status:** Accepted
- **Date:** 2026-07 (as embodied in the 0.2.0b1 codebase)

## Context

The project needed a maintainable layout for a typed scientific Python package
with a CLI, multiple check modules, versioned schema resources, and
renderers — without freezing internal paths as the compatibility contract.

## Decision

- Use a **src layout** (`src/cp_anndata_validator/`) with `uv` and `uv_build`.
- Expose a thin public surface from `cp_anndata_validator` / `api.validate`.
- Keep layers separate: loading → schema → checks → orchestration → models →
  reporting → CLI.
- Ship `py.typed` and run `mypy` in CI.
- Checks return structured `Issue` lists; they do not print.

## Consequences

- Internal refactors can proceed behind `validate()` and the models.
- Contributors must export new public symbols deliberately.
- CLI remains a thin adapter (`cli/app.py`) over the API and renderers.

## Alternatives considered

- Flat layout at repo root — rejected for import/test isolation reasons.
- Exposing every submodule as public API — rejected as too brittle.

## References

- `src/cp_anndata_validator/api.py`, `orchestrator.py`, `cli/app.py`
- `tests/test_api.py`, `tests/test_cli.py`
