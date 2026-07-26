# ADR-0005 — Exact alias resolution and deterministic precedence

- **Status:** Accepted
- **Date:** 2026-07 (as embodied in the 0.2.0b1 codebase)

## Context

Cell Painting tables use many column spellings. Silent fuzzy matching would
hide mistakes; unordered matching would be non-deterministic.

## Decision

- Match aliases case-insensitively after trim, **exact** token equality.
- Try aliases in **declaration order**; first hit wins.
- Reject duplicate aliases within/across fields at schema load time.
- No regex, fuzzy, or content-based inference.

## Consequences

- Missing aliases require schema updates backed by public evidence.
- Precedence is reviewable in YAML and documented for key fields.

## Alternatives considered

- Fuzzy/typo-tolerant matching — rejected (silent mis-resolution risk).
- Content-based inference — rejected (unexplainable, unsafe).

## References

- `src/cp_anndata_validator/schema/resolve.py`, `loader.py`
- `tests/test_schema_resolution.py`, `tests/test_batch_alias_lincs.py`
- [Alias resolution](../schemas/aliases.md)
