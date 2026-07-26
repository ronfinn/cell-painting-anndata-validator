# ADR-0006 — Profile-level detection and explicit override

- **Status:** Accepted
- **Date:** 2026-07 (as embodied in the 0.2.0b1 codebase)

## Context

Single-cell, well and treatment products need different required fields.
Users must be able to override detection; detection must remain explainable.

## Decision

- Support levels: `single-cell`, `well`, `treatment`.
- Auto-detect from resolved fields, cell-granularity signals and row
  cardinality heuristics.
- Always allow CLI/API override; record declared, detected, candidates,
  confidence and explanation on the report.
- Ambiguity and declare/detect mismatch emit dedicated profile issues.

## Consequences

- Ambiguous tables may need `--profile-level`.
- Overrides never hide what detection thought.

## Alternatives considered

- Require always-declared level — rejected as poor UX for clear cases.
- Silent best-guess without explanation — rejected.

## References

- `src/cp_anndata_validator/profiles.py`
- `src/cp_anndata_validator/checks/profile_consistency.py`
- [Profile levels](../concepts/profile-levels.md)
