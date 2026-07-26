# ADR-0008 — Bounded sampling for large and backed matrices

- **Status:** Accepted
- **Date:** 2026-07 (as embodied in the 0.2.0b1 codebase)

## Context

Full densification or exhaustive scans of large matrices are unsafe for
memory and runtime. Backed AnnData must fail gracefully.

## Decision

- Never densify a full sparse matrix merely to validate it.
- Numeric / AI-readiness checks use bounded row sampling (`sample_rows`,
  default 5000) for large or backed inputs.
- Sparse in-memory paths may inspect `.data` without densifying.
- Unsupported modes skip with an explicit check execution record rather than
  crashing the run.

## Consequences

- Rare defects outside the sample may be missed (documented limitation).
- Large public profiles remain practical to validate.

## Alternatives considered

- Always full-matrix scan — rejected for scalability.
- Skip numeric checks on backed data silently — rejected; skips are recorded.

## References

- `src/cp_anndata_validator/sampling.py`, `loading.py`
- Matrix / AI-readiness checks and their tests
- [Large or backed AnnData](../how-to/large-backed-anndata.md)
