# ADR-0004 — Independent package and schema versioning

- **Status:** Accepted
- **Date:** 2026-07 (as embodied in the 0.2.0b1 / schema 0.2.1 line)

## Context

Schema vocabulary (aliases, compartments, families) evolves on a different
cadence from the Python package API.

## Decision

Track package version (`0.2.0b1`) separately from built-in
`schema_version` fields (`0.2.1` for both built-ins). CLI `--version`
reports the package version only.

## Consequences

- Release notes must state both when relevant.
- Dataset `uns['schema_version']` is not the validator package version.

## Alternatives considered

- Single version for package and schemas — rejected as coupling unrelated
  change rates.

## References

- `pyproject.toml`, `src/cp_anndata_validator/version.py`
- `src/cp_anndata_validator/schema/resources/*.yaml`
- `tests/test_release_metadata.py`
