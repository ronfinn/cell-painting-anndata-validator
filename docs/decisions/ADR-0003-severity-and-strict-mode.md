# ADR-0003 — Severity, status and strict-mode semantics

- **Status:** Accepted
- **Date:** 2026-07 (as embodied in the 0.2.0b1 codebase)

## Context

Publishers and explorers need different failure thresholds. Some gaps
(especially governance) should warn without failing casual runs.

## Decision

- Severities: `error`, `warning`, `information`.
- Normal mode: only errors fail `report.status`.
- Strict mode (`strict=True` / `--strict`): warnings also fail.
- Information never fails status.
- CLI exit `0`/`1` follow status; exit `2` is for execution failures.
- `AGG001` (missing aggregation method) is a **warning**.

## Consequences

- CI must opt into `--strict` to enforce warnings.
- Exploratory validation remains usable on bare pipeline exports.

## Alternatives considered

- Always fail on warnings — rejected as too harsh for beta adoption.
- Never fail on aggregation gaps — rejected for publishing use cases.

## References

- `src/cp_anndata_validator/models/report.py` (status derivation)
- `src/cp_anndata_validator/checks/aggregation.py`
- `tests/test_api.py`, `tests/test_cli.py`
