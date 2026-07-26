# ADR-0007 — Truthful metadata and no silent fabrication

- **Status:** Accepted
- **Date:** 2026-07 (as embodied in the 0.2.0b1 codebase)

## Context

A validator that invents licence or provenance metadata would produce false
confidence and corrupt publishing workflows.

## Decision

- Read-only validation: never write the input `.h5ad`.
- Report missing/incomplete `.uns` governance blocks instead of inventing them.
- Public-data pilots document truthful conversion mappings only.
- Custom schemas cannot embed executable code (`yaml.safe_load`).

## Consequences

- Bare pipeline exports warn until authors add real metadata.
- Pilot reports retain expected governance warnings.

## Alternatives considered

- Auto-fill defaults (e.g. assume CC0) — rejected as dishonest.
- Skip provenance checks entirely — rejected for publishing utility.

## References

- Provenance/metadata/aggregation checks under `src/cp_anndata_validator/checks/`
- [Public-data pilots](../pilots/index.md)
- [Truthful metadata](../concepts/truthful-metadata.md)
